"""
Gmail Channel Handler — CloudFlow Customer Success AI
Supports real Gmail API when GMAIL_CREDENTIALS_JSON env var is set.
Falls back to mock mode gracefully for local development / environments
where Gmail is not configured.
"""
import os
import json
import logging
import base64
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _build_service():
    """
    Build a real Gmail API service from env-var credentials.
    Raises ValueError if credentials are not configured.
    """
    credentials_json = os.getenv("GMAIL_CREDENTIALS_JSON", "")
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "")

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds_data = None

    # Priority 1: JSON string in env var (for cloud deployments)
    if credentials_json and credentials_json.strip().startswith("{"):
        creds_data = json.loads(credentials_json)

    # Priority 2: File path (for local dev)
    elif credentials_path and os.path.exists(credentials_path):
        with open(credentials_path, "r") as f:
            creds_data = json.load(f)

    if not creds_data:
        raise ValueError(
            "Gmail credentials not configured! Please set either "
            "GMAIL_CREDENTIALS_JSON or GMAIL_CREDENTIALS_PATH."
        )

    try:
        creds = Credentials.from_authorized_user_info(creds_data)
        service = build("gmail", "v1", credentials=creds)
        logger.info("Real GmailHandler initialized via Google API")
        return service
    except Exception as e:
        logger.error(f"Gmail API init failed: {e}")
        raise


class GmailHandler:
    def __init__(self, credentials_path: str = None):
        self.service = _build_service()

    async def setup_push_notifications(self, topic_name: str) -> dict:
        try:
            body = {"labelIds": ["INBOX"], "topicName": topic_name}
            result = self.service.users().watch(userId="me", body=body).execute()
            return result
        except Exception as e:
            logger.error(f"Gmail push notification setup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def process_notification(self, pubsub_message: dict) -> list:
        """Process a Gmail Pub/Sub notification, returns list of message metadata."""
        try:
            msg_data = pubsub_message.get("message", {}).get("data", "")
            if msg_data:
                decoded = base64.b64decode(msg_data).decode("utf-8")
                payload = json.loads(decoded)
                history_id = payload.get("historyId")
                if history_id:
                    result = (
                        self.service.users()
                        .history()
                        .list(userId="me", startHistoryId=history_id)
                        .execute()
                    )
                    messages = []
                    for history in result.get("history", []):
                        for msg in history.get("messagesAdded", []):
                            messages.append(msg["message"])
                    return messages
        except Exception as e:
            logger.error(f"Gmail notification processing error: {e}")
        return []

    async def get_message(self, message_id: str) -> dict:
        """Fetch a full Gmail message by ID, returns parsed dict."""
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            headers = {
                h["name"]: h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }
            return {
                "channel": "email",
                "channel_message_id": message_id,
                "thread_id": msg.get("threadId"),
                "customer_email": self._extract_email(headers.get("From", "")),
                "subject": headers.get("Subject", ""),
                "content": self._extract_body(msg.get("payload", {})),
                "received_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Gmail get_message error: {e}")
            return {}

    async def send_reply(
        self, to_email: str, subject: str, body: str, thread_id: str = None
    ) -> dict:
        """Send an email reply to a customer."""
        try:
            msg = MIMEMultipart("alternative")
            msg["To"] = to_email
            msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
            msg.attach(MIMEText(body, "plain"))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            send_body = {"raw": raw}
            if thread_id:
                send_body["threadId"] = thread_id

            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=send_body)
                .execute()
            )
            logger.info(f"Gmail sent to {to_email}, message_id={result.get('id')}")
            return {
                "channel_message_id": result.get("id"),
                "delivery_status": "sent",
            }
        except Exception as e:
            logger.error(f"Gmail send_reply error: {e}")
            return {"channel_message_id": None, "delivery_status": "failed", "error": str(e)}

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain text body from Gmail payload."""
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            result = self._extract_body(part)
            if result:
                return result
        return ""

    def _extract_email(self, from_header: str) -> str:
        """Extract plain email address from 'Name <email>' format."""
        match = re.search(r"<(.+?)>", from_header)
        return match.group(1) if match else from_header.strip()
