import base64
import re
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    creds = None
    try:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    except Exception:
        creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_part(data):
    if not data:
        return ""
    decoded = base64.urlsafe_b64decode(data + "=")
    return decoded.decode("utf-8", errors="ignore")


def _extract_plain_or_html(payload):
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if mime_type in {"text/plain", "text/html"} and body_data:
        text = _decode_part(body_data)
        if mime_type == "text/html":
            return re.sub(r"<[^>]+>", " ", text)
        return text

    parts = payload.get("parts", [])
    plain_text = ""
    html_text = ""
    for part in parts:
        part_type = part.get("mimeType", "")
        part_body = part.get("body", {}).get("data")
        if part_type == "text/plain" and part_body:
            plain_text += _decode_part(part_body)
        elif part_type == "text/html" and part_body:
            html_text += _decode_part(part_body)
        elif part.get("parts"):
            nested = _extract_plain_or_html(part)
            if nested:
                plain_text += nested

    if plain_text.strip():
        return plain_text.strip()
    if html_text.strip():
        return re.sub(r"<[^>]+>", " ", html_text).strip()
    return ""


def get_unread_emails(service):
    emails = []
    try:
        result = service.users().messages().list(userId="me", q="is:unread").execute()
        messages = result.get("messages", [])
    except Exception:
        return emails

    for msg_meta in messages:
        try:
            msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])
            header_map = {h.get("name", "").lower(): h.get("value", "") for h in headers}

            from_header = header_map.get("from", "")
            match = re.match(r"(.*)<(.+?)>", from_header)
            if match:
                from_name = match.group(1).strip().strip('"')
                from_email = match.group(2).strip()
            else:
                from_name = from_header
                from_email = from_header

            email_data = {
                "message_id": msg.get("id", ""),
                "from_email": from_email,
                "from_name": from_name or from_email,
                "subject": header_map.get("subject", "No Subject"),
                "body": _extract_plain_or_html(payload),
                "date": header_map.get("date", ""),
            }
            emails.append(email_data)
        except Exception:
            continue

    return emails


def send_reply(service, original_message_id, to_email, subject, reply_body):
    try:
        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        message = MIMEText(reply_body)
        message["to"] = to_email
        message["subject"] = reply_subject
        message["In-Reply-To"] = original_message_id
        message["References"] = original_message_id

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return True
    except Exception:
        return False


def mark_as_read(service, message_id):
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
        return True
    except Exception:
        return False