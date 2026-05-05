import pytest
from pydantic import ValidationError
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.web_form_handler import SupportFormSubmission

class TestWhatsAppHandler:
    def test_format_response_short(self):
        handler = WhatsAppHandler()
        result = handler.format_response("Hello", 1600)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Hello"

    def test_format_response_splits_long(self):
        handler = WhatsAppHandler()
        long_text = "word. " * 200 # approx 1200 chars
        result = handler.format_response(long_text, 100)
        assert len(result) > 1

    @pytest.mark.asyncio
    async def test_process_webhook_extracts_phone(self):
        handler = WhatsAppHandler()
        form_data = {
            "From": "whatsapp:+923001234567",
            "Body": "Hello",
            "SmsMessageSid": "SM123"
        }
        result = await handler.process_webhook(form_data)
        assert result["customer_phone"] == "+923001234567"

class TestWebFormValidation:
    def test_valid_submission_passes(self):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Testing",
            "category": "technical",
            "message": "This is a long enough message for validation."
        }
        # Should not raise
        SupportFormSubmission(**data)

    def test_short_name_fails(self):
        data = {
            "name": "A",
            "email": "john@example.com",
            "subject": "Testing",
            "category": "technical",
            "message": "This is a long enough message for validation."
        }
        with pytest.raises(ValidationError) as excinfo:
            SupportFormSubmission(**data)
        assert "Name must be at least 2 characters" in str(excinfo.value)

    def test_invalid_email_fails(self):
        data = {
            "name": "John Doe",
            "email": "notanemail",
            "subject": "Testing",
            "category": "technical",
            "message": "This is a long enough message for validation."
        }
        with pytest.raises(ValidationError):
            SupportFormSubmission(**data)

    def test_invalid_category_fails(self):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Testing",
            "category": "unknown",
            "message": "This is a long enough message for validation."
        }
        with pytest.raises(ValidationError) as excinfo:
            SupportFormSubmission(**data)
        assert "Category must be one of" in str(excinfo.value)

    def test_short_message_fails(self):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Testing",
            "category": "technical",
            "message": "Hi"
        }
        with pytest.raises(ValidationError) as excinfo:
            SupportFormSubmission(**data)
        assert "Message must be at least 10 characters" in str(excinfo.value)
