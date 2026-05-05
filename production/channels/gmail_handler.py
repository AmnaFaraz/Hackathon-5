import logging
import base64
import email

logger = logging.getLogger(__name__)

import json
import re
from datetime import datetime
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GmailHandler:
    def __init__(self, credentials_path: str = None):
        """
        Mock Gmail handler for local deployment.
        """
        self.service = None
        logger.info("Mock GmailHandler initialized")

    async def setup_push_notifications(self, topic_name: str) -> dict:
        return {"status": "mocked"}

    async def process_notification(self, pubsub_message: dict) -> list:
        return []

    async def get_message(self, message_id: str) -> dict:
        return {}

    async def send_reply(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        logger.info(f"Mock Gmail send to {to_email}")
        return {"channel_message_id": "mock-id", "delivery_status": "sent"}

    def _extract_body(self, payload: dict) -> str:
        return ""

    def _extract_email(self, from_header: str) -> str:
        return ""
