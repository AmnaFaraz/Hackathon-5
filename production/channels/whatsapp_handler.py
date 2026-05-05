import os
from datetime import datetime
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from fastapi import Request

class WhatsAppHandler:
    def __init__(self):
        """
        Mock WhatsApp handler for local deployment.
        """
        self.account_sid = "mock_sid"
        self.auth_token = "mock_token"
        self.from_number = "whatsapp:+14155238886"
        self.client = None
        self.validator = None

    async def validate_webhook(self, request: Request) -> bool:
        return True

    async def process_webhook(self, form_data: dict) -> dict:
        customer_phone = form_data.get("From", "").replace("whatsapp:", "")
        return {
            "channel": "whatsapp",
            "channel_message_id": form_data.get("SmsMessageSid", "mock-sid"),
            "customer_phone": customer_phone,
            "content": form_data.get("Body", ""),
            "received_at": datetime.utcnow().isoformat()
        }

    async def send_message(self, to_phone: str, body: str) -> dict:
        return {
            "channel_message_id": "mock-sid",
            "delivery_status": "sent"
        }

    def format_response(self, response: str, max_length: int = 1600) -> list:
        """
        Splits long responses at sentence boundaries into multiple chunks.
        """
        if len(response) <= max_length:
            return [response]
        
        chunks = []
        sentences = response.replace("\n", " ").split(". ")
        current_chunk = ""
        
        for sentence in sentences:
            if not sentence: continue
            suffix = ". " if not sentence.endswith(".") else " "
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + suffix
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + suffix
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
