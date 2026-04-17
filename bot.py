import os
import anthropic
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Tu es COACH, un agent d'apprentissage personnel et exigeant. Tu coaches Tafsir, Directeur BTD à Afrika Banque Sénégal, qui prépare un side-project AI holding entrepreneurial.

Ses lacunes : cap table, dilution, pre/post-money, term sheet, pipeline B2B.

Commandes :
/lecon [sujet] → leçon avec exemple Sénégal/AI holding
/qcm [sujet] → QCM + débrief critique
/simulation → tu joues un prospect B2B sénégalais
/suivi → suivi progression Coursera
/aide → liste commandes

Règles : sois critique, jamais complaisant, exemples contextualisés Sénégal/UEMOA, français, concis, max 300 mots."""

conversations = {}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    return requests.get(url, params=params).json()

def chat_with_claude(user_id, message):
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role": "user", "content": message})
    history = conversations[user_id][-20:]
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=history
    )
    reply = response.content[0].text
    conversations[user_id].append({"role": "assistant", "content": reply})
    return reply

def handle_update(update):
    if "message" not in update:
        return
    message = update["message"]
    chat_id = message["chat"]["id"]
    user_id = str(chat_id)
    text = message.get("text", "")
    if not text:
        return
    if text == "/start":
        send_message(chat_id, "👋 *Bonjour Tafsir !*\n\nJe suis ton coach IA pour le parcours AI Holding.\n\n*Commandes :*\n• `/lecon cap table`\n• `/qcm finance`\n• `/qcm vente`\n• `/simulation`\n• `/suivi`\n• `/reset`")
        return
    if text == "/reset":
        conversations[user_id] = []
        send_message(chat_id, "✅ Conversation réinitialisée.")
        return
    try:
        reply = chat_with_claude(user_id, text)
        send_message(chat_id, reply)
    except Exception as e:
        send_message(chat_id, f"❌ Erreur : {str(e)}")

def main():
    print("🚀 Coach Bot démarré...")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    handle_update(update)
                    offset = update["update_id"] + 1
        except Exception as e:
            print(f"Erreur : {e}")

if __name__ == "__main__":
    main()
