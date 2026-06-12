import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

from agent import chat_with_agent, extract_business_summary
from gmail_helper import get_gmail_service
from monitor import process_new_emails, set_socketio, start_monitoring_loop
from store import (
    get_business_knowledge,
    get_conversation_history,
    get_monitoring_settings,
    get_reply_logs,
    load_store,
    save_business_knowledge,
    save_conversation_history,
    set_monitoring_active,
    set_monitoring_interval,
)
from telegram_helper import test_telegram_connection

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "email-agent-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
set_socketio(socketio)


def _print_setup_guide():
    print(
        """
============================================
📧 EMAIL AGENT — SETUP GUIDE
============================================

1. Get FREE Groq API Key:
   → Go to console.groq.com
   → Sign up (no credit card needed)
   → API Keys → Create Key
   → Paste into .env as GROQ_API_KEY

2. Get Gmail Credentials:
   → Go to console.cloud.google.com
   → Create project → Enable Gmail API
   → Credentials → OAuth 2.0 Client ID
   → Application type: Desktop App
   → Download credentials.json
   → Place in this folder

3. Get Telegram Bot Token:
   → Open Telegram → Search @BotFather
   → Send: /newbot → Follow prompts
   → Copy token → Paste in Settings tab

4. Get Telegram Chat ID:
   → Search @userinfobot on Telegram
   → Send any message → Copy your ID
   → Paste in Settings tab

5. Run: pip install -r requirements.txt
6. Run: python app.py
7. Open: http://localhost:5000

============================================
"""
    )


def _upsert_env_values(values):
    env_path = ".env"
    existing = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file.readlines():
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    existing[key] = value

    existing.update(values)

    with open(env_path, "w", encoding="utf-8") as env_file:
        for key, value in existing.items():
            env_file.write(f"{key}={value}\n")

    os.environ.update(values)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/agent/chat")
def api_agent_chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    history = get_conversation_history()
    try:
        response = chat_with_agent(message, history)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    save_conversation_history(response["updated_history"])
    return jsonify({"reply": response["reply"]})


@app.post("/api/agent/save")
def api_agent_save():
    history = get_conversation_history()
    if not history:
        return jsonify({"error": "No conversation history to save"}), 400

    try:
        summary = extract_business_summary(history)
        save_business_knowledge(summary)
        return jsonify({"success": True, "summary": summary})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/business")
def api_business():
    knowledge = get_business_knowledge()
    return jsonify({"knowledge": knowledge, "has_knowledge": bool(knowledge.strip())})


@app.get("/api/gmail/auth")
def api_gmail_auth():
    try:
        get_gmail_service()
        return jsonify({"connected": True})
    except Exception as exc:
        return jsonify({"connected": False, "error": str(exc)}), 500


@app.post("/api/monitor/start")
def api_monitor_start():
    payload = request.get_json(silent=True) or {}
    interval_minutes = int(payload.get("interval_minutes", 5))
    set_monitoring_interval(interval_minutes)
    set_monitoring_active(True)
    started = start_monitoring_loop(interval_minutes)
    return jsonify({"success": True, "started": started})


@app.post("/api/monitor/stop")
def api_monitor_stop():
    set_monitoring_active(False)
    return jsonify({"success": True})


@app.get("/api/monitor/status")
def api_monitor_status():
    settings = get_monitoring_settings()
    return jsonify(
        {
            "active": settings["monitoring_active"],
            "interval": settings["monitoring_interval_minutes"],
        }
    )


@app.post("/api/monitor/scan-now")
def api_scan_now():
    result = process_new_emails()
    return jsonify(
        {
            "emails_found": result["emails_found"],
            "replies_sent": result["replies_sent"],
            "errors": result.get("errors", []),
        }
    )


@app.get("/api/logs")
def api_logs():
    return jsonify({"logs": get_reply_logs()})


@app.post("/api/telegram/test")
def api_telegram_test():
    return jsonify({"success": test_telegram_connection()})


@app.post("/api/settings/save")
def api_settings_save():
    payload = request.get_json(silent=True) or {}
    bot_token = (payload.get("telegram_bot_token") or "").strip()
    chat_id = (payload.get("telegram_chat_id") or "").strip()
    interval = int(payload.get("interval_minutes", 5))

    _upsert_env_values(
        {
            "TELEGRAM_BOT_TOKEN": bot_token,
            "TELEGRAM_CHAT_ID": chat_id,
        }
    )
    set_monitoring_interval(interval)
    load_store()
    return jsonify({"success": True})


if __name__ == "__main__":
    _print_setup_guide()
    load_store()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
