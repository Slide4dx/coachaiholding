import os
import requests
import time

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(f"Erreur send_message: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 20}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=25)
        return response.json()
    except Exception as e:
        print(f"Erreur get_updates: {e}")
        return {"ok": False, "result": []}

def chat_with_claude(conversation_history, message):
    conversation_history.append({"role": "user", "content": message})
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 800,
                "system": "Tu es COACH, agent d'apprentissage exigeant pour Tafsir, Directeur BTD Afrika Banque Senegal, qui prepare un AI holding. Lacunes : cap table, dilution, pre/post-money, term sheet, pipeline B2B. Commandes : /lecon [sujet], /qcm [sujet], /simulation, /suivi. Regles : critique, honnete, exemples Senegal/UEMOA, francais, max 300 mots.",
                "messages": conversation_history[-20:]
            },
            timeout=30
        )
        data = response.json()
        print(f"API response status: {response.status_code}")
        print(f"API response: {data}")
        if "content" in data:
            reply = data["content"][0]["text"]
            conversation_history.append({"role": "assistant", "content": reply})
            return reply
        else:
            return f"Erreur API: {data}"
    except Exception as e:
        print(f"Erreur claude: {e}")
        return f"Erreur: {str(e)}"

conversations = {}

def handle_update(update):
    if "message" not in update:
        return
    message = update["message"]
    chat_id = message["chat"]["id"]
    user_id = str(chat_id)
    text = message.get("text", "")
    if not text:
        return
    print(f"Message recu: {text} de {user_id}")
    if user_id not in conversations:
        conversations[user_id] = []
    if text == "/start":
        send_message(chat_id, "Bonjour Tafsir ! Je suis ton coach IA.\n\nCommandes:\n/lecon cap table\n/qcm finance\n/simulation\n/suivi\n/reset")
        return
    if text == "/reset":
        conversations[user_id] = []
        send_message(chat_id, "Conversation reinitialisee.")
        return
    reply = chat_with_claude(conversations[user_id], text)
    send_message(chat_id, reply)

def main():
    print("Coach Bot demarre...")
    print(f"TELEGRAM_TOKEN present: {bool(TELEGRAM_TOKEN)}")
    print(f"ANTHROPIC_API_KEY present: {bool(ANTHROPIC_API_KEY)}")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    handle_update(update)
                    offset = update["update_id"] + 1
        except Exception as e:
            print(f"Erreur main: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
