import requests

from config import BOT_TOKEN, CHAT_ID



def send_telegram_message(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)
