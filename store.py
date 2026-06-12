import json
from pathlib import Path

STORE_PATH = Path("data.json")

DEFAULT_STORE = {
    "business_knowledge": "",
    "conversation_history": [],
    "processed_email_ids": [],
    "monitoring_active": False,
    "monitoring_interval_minutes": 5,
    "reply_logs": [],
}


def _ensure_store_file():
    if not STORE_PATH.exists():
        save_store(DEFAULT_STORE.copy())


def load_store():
    _ensure_store_file()
    try:
        with STORE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        data = DEFAULT_STORE.copy()
        save_store(data)

    for key, default_value in DEFAULT_STORE.items():
        data.setdefault(key, default_value if not isinstance(default_value, list) else default_value.copy())

    return data


def save_store(data):
    with STORE_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_business_knowledge():
    return load_store().get("business_knowledge", "")


def save_business_knowledge(text):
    data = load_store()
    data["business_knowledge"] = text
    save_store(data)


def get_conversation_history():
    return load_store().get("conversation_history", [])


def save_conversation_history(history):
    data = load_store()
    data["conversation_history"] = history
    save_store(data)


def add_reply_log(log_entry):
    data = load_store()
    data.setdefault("reply_logs", [])
    data["reply_logs"].append(log_entry)
    save_store(data)


def get_reply_logs():
    logs = load_store().get("reply_logs", [])
    return list(reversed(logs))


def add_processed_id(email_id):
    data = load_store()
    data.setdefault("processed_email_ids", [])
    if email_id not in data["processed_email_ids"]:
        data["processed_email_ids"].append(email_id)
        save_store(data)


def is_processed(email_id):
    return email_id in load_store().get("processed_email_ids", [])


def get_monitoring_settings():
    data = load_store()
    return {
        "monitoring_active": bool(data.get("monitoring_active", False)),
        "monitoring_interval_minutes": int(data.get("monitoring_interval_minutes", 5)),
    }


def set_monitoring_active(active):
    data = load_store()
    data["monitoring_active"] = bool(active)
    save_store(data)


def set_monitoring_interval(interval_minutes):
    data = load_store()
    data["monitoring_interval_minutes"] = max(1, int(interval_minutes))
    save_store(data)