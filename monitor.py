import threading
import time
import uuid
from datetime import datetime

from agent import generate_email_reply
from gmail_helper import get_gmail_service, get_unread_emails, mark_as_read, send_reply
from store import (
    add_processed_id,
    add_reply_log,
    get_business_knowledge,
    get_monitoring_settings,
    is_processed,
)
from telegram_helper import send_enquiry_notification

monitor_thread = None
monitor_thread_lock = threading.Lock()
socketio_instance = None


def set_socketio(socketio):
    global socketio_instance
    socketio_instance = socketio


def _emit_activity(message, level="info"):
    if socketio_instance:
        socketio_instance.emit(
            "new_log",
            {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "level": level,
            },
        )


def process_new_emails():
    result = {"emails_found": 0, "replies_sent": 0, "errors": []}

    try:
        service = get_gmail_service()
    except Exception as exc:
        err = f"Gmail not connected: {exc}"
        result["errors"].append(err)
        _emit_activity(err, "error")
        return result

    emails = get_unread_emails(service)
    result["emails_found"] = len(emails)
    _emit_activity(f"Scan complete: found {len(emails)} unread emails", "info")

    knowledge = get_business_knowledge().strip()
    if not knowledge:
        msg = "No business knowledge set. Please complete Business Setup first."
        result["errors"].append(msg)
        _emit_activity(msg, "error")
        return result

    for email in emails:
        email_id = email.get("message_id", "")
        if not email_id or is_processed(email_id):
            continue

        try:
            reply = generate_email_reply(
                knowledge,
                email.get("from_name", "Customer"),
                email.get("from_email", ""),
                email.get("subject", "No Subject"),
                email.get("body", ""),
            )

            sent = send_reply(
                service,
                email_id,
                email.get("from_email", ""),
                email.get("subject", "No Subject"),
                reply,
            )

            if not sent:
                raise RuntimeError("Failed to send reply")

            mark_as_read(service, email_id)
            add_processed_id(email_id)
            notified = send_enquiry_notification(
                email.get("from_email", ""),
                email.get("from_name", "Customer"),
                email.get("subject", "No Subject"),
                reply,
            )

            log_entry = {
                "id": str(uuid.uuid4()),
                "from_email": email.get("from_email", ""),
                "from_name": email.get("from_name", "Customer"),
                "subject": email.get("subject", "No Subject"),
                "received_at": datetime.now().isoformat(),
                "email_body": email.get("body", ""),
                "reply_sent": reply,
                "status": "replied",
                "telegram_notified": bool(notified),
            }
            add_reply_log(log_entry)
            _emit_activity(
                f"Replied to {log_entry['from_email']} about '{log_entry['subject']}'",
                "success",
            )
            _emit_activity(log_entry, "success")
            result["replies_sent"] += 1
        except Exception as exc:
            error_msg = f"Failed to process email {email_id}: {exc}"
            result["errors"].append(error_msg)
            _emit_activity(error_msg, "error")

    return result


def _monitor_loop(interval_minutes):
    interval_seconds = max(1, int(interval_minutes)) * 60
    while True:
        settings = get_monitoring_settings()
        if not settings["monitoring_active"]:
            _emit_activity("Monitoring loop stopped", "info")
            break

        process_new_emails()
        slept = 0
        while slept < interval_seconds:
            settings = get_monitoring_settings()
            if not settings["monitoring_active"]:
                break
            time.sleep(1)
            slept += 1


def start_monitoring_loop(interval_minutes):
    global monitor_thread
    with monitor_thread_lock:
        if monitor_thread and monitor_thread.is_alive():
            return False

        monitor_thread = threading.Thread(
            target=_monitor_loop,
            args=(interval_minutes,),
            daemon=True,
        )
        monitor_thread.start()
        _emit_activity(f"Monitoring started (every {interval_minutes} min)", "info")
        return True