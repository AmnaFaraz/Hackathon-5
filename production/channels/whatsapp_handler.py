"""
WhatsApp Channel Handler via Twilio — CloudFlow Customer Success AI
Supports real Twilio API when TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set.
Falls back to mock mode gracefully for local development.
"""
import os
import logging
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)


def _try_init_twilio():
    """
    Attempt to initialize real Twilio client from environment variables.
    Returns (client, validator) or (None, None) if not configured.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

    # Skip if placeholder values are still present
    if not account_sid or account_sid in ("your_twilio_sid", "mock_sid"):
        return None, None
    if not auth_token or auth_token in ("your_twilio_token", "mock_token"):
        return None, None

    try:
        from twilio.rest import Client
        from twilio.request_validator import RequestValidator
        client = Client(account_sid, auth_token)
        validator = RequestValidator(auth_token)
        logger.info("Real Twilio WhatsApp handler initialized")
        return client, validator
    except Exception as e:
        logger.warning(f"Twilio init failed — falling back to mock mode: {e}")
        return None, None


class WhatsAppHandler:
    def __init__(self):
        self.client, self.validator = _try_init_twilio()
        self._mock = self.client is None
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        if self._mock:
            logger.info("WhatsAppHandler running in mock mode (no valid Twilio credentials)")

    async def validate_webhook(self, request: Request) -> bool:
        """Validate incoming Twilio webhook signature."""
        if self._mock:
            return True  # Allow all in mock mode
        try:
            signature = request.headers.get("X-Twilio-Signature", "")
            url = str(request.url)
            form_data = await request.form()
            params = dict(form_data)
            return self.validator.validate(url, params, signature)
        except Exception as e:
            logger.error(f"WhatsApp webhook validation error: {e}")
            return False

    async def process_webhook(self, form_data: dict) -> dict:
        """Parse Twilio webhook form data into a normalized message dict."""
        customer_phone = form_data.get("From", "").replace("whatsapp:", "")
        return {
            "channel": "whatsapp",
            "channel_message_id": form_data.get("SmsMessageSid", f"wa-{datetime.utcnow().timestamp()}"),
            "customer_phone": customer_phone,
            "content": form_data.get("Body", ""),
            "media_url": form_data.get("MediaUrl0"),
            "received_at": datetime.utcnow().isoformat(),
        }

    async def send_message(self, to_phone: str, body: str) -> dict:
        """Send a WhatsApp message to a customer phone number."""
        if self._mock:
            logger.info(f"[MOCK] WhatsApp send to {to_phone}: {body[:80]}...")
            return {"channel_message_id": "mock-sid", "delivery_status": "sent"}
        try:
            # Ensure proper whatsapp: prefix
            to = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"

            # Split long messages at sentence boundaries (WhatsApp 1600 char limit)
            chunks = self.format_response(body)
            results = []
            for chunk in chunks:
                msg = self.client.messages.create(
                    from_=self.from_number,
                    to=to,
                    body=chunk,
                )
                results.append(msg.sid)
                logger.info(f"WhatsApp sent to {to_phone}, sid={msg.sid}")

            return {
                "channel_message_id": results[0] if results else None,
                "delivery_status": "sent",
                "message_count": len(results),
            }
        except Exception as e:
            logger.error(f"WhatsApp send_message error: {e}")
            return {"channel_message_id": None, "delivery_status": "failed", "error": str(e)}

    def format_response(self, response: str, max_length: int = 1600) -> list:
        """
        Splits long responses at sentence boundaries into WhatsApp-safe chunks.
        WhatsApp max message length is 1600 characters.
        """
        if len(response) <= max_length:
            return [response]

        chunks = []
        sentences = response.replace("\n", " ").split(". ")
        current_chunk = ""

        for sentence in sentences:
            if not sentence:
                continue
            suffix = ". " if not sentence.endswith(".") else " "
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + suffix
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + suffix

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [response[:max_length]]
