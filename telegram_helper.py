import os

import requests


def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=20)
        return response.status_code == 200 and response.json().get("ok", False)
    except Exception:
        return False


def send_enquiry_notification(from_email, from_name, subject, reply_preview):
    message = (
        "📩 <b>New Enquiry Received!</b>\n\n"
        f"👤 <b>From:</b> {from_name} ({from_email})\n"
        f"📋 <b>Subject:</b> {subject}\n\n"
        "✅ <b>Auto-reply sent!</b>\n\n"
        "<b>Reply preview:</b>\n"
        f"{(reply_preview or '')[:300]}..."
    )
    return send_telegram_message(message)


def test_telegram_connection():
    return send_telegram_message("✅ Telegram connected! Your email agent is ready.")