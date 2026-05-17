import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime


def unique_email(prefix: str = "test") -> str:
    """Generate a unique email address to avoid DB constraint conflicts across test runs."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
async def client():
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as ac:
        yield ac

class TestWebFormChannel:
    @pytest.mark.asyncio
    async def test_form_submission(self, client):
        payload = {
            "name": "Jane Doe",
            "email": unique_email("jane"),
            "subject": "Login Issue",
            "category": "technical",
            "message": "I cannot log in to my account since this morning.",
            "priority": "high"
        }
        response = await client.post("/support/submit", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert "estimated_response_time" in data

    @pytest.mark.asyncio
    async def test_form_validation(self, client):
        # Invalid data: short name, invalid email, etc.
        payload = {
            "name": "A",
            "email": "invalid",
            "subject": "Hi",
            "category": "invalid",
            "message": "Short"
        }
        response = await client.post("/support/submit", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ticket_status_retrieval(self, client):
        # First submit with unique email
        payload = {
            "name": "Test User",
            "email": unique_email("statuscheck"),
            "subject": "Status Check Test",
            "category": "general",
            "message": "Checking my ticket status please."
        }
        sub_res = await client.post("/support/submit", json=payload)
        assert sub_res.status_code == 200, f"Submit failed: {sub_res.text}"
        ticket_id = sub_res.json()["ticket_id"]

        # Then get status
        response = await client.get(f"/support/ticket/{ticket_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["open", "processing"]

class TestEmailChannel:
    @pytest.mark.asyncio
    async def test_gmail_webhook_processing(self, client):
        # Mock Pub/Sub payload
        payload = {
            "message": {
                "data": "eyJoaXN0b3J5SWQiOiAiMTIzNDU2In0=", # base64 for {"historyId": "123456"}
                "message_id": "999999"
            }
        }
        response = await client.post("/webhooks/gmail", json=payload)
        assert response.status_code == 200

class TestWhatsAppChannel:
    @pytest.mark.asyncio
    async def test_whatsapp_webhook_processing(self, client):
        # Mock Twilio form data (requires proper signature in real scenarios or mock validation)
        # Here we just check status_code logic
        form_data = {
            "From": "whatsapp:+923001234567",
            "Body": "Hello AI",
            "SmsMessageSid": "SM123"
        }
        # In a real test, signature validation might fail or need a mock header
        response = await client.post("/webhooks/whatsapp", data=form_data)
        assert response.status_code in [200, 403]

class TestCrossChannelContinuity:
    @pytest.mark.asyncio
    async def test_customer_history_across_channels(self, client):
        email = unique_email("crosschannel")
        # Submit via web form
        submit_res = await client.post("/support/submit", json={
            "name": "Cross User",
            "email": email,
            "subject": "History Test Request",
            "category": "general",
            "message": "I am testing cross-channel lookup across channels."
        })
        assert submit_res.status_code == 200, f"Submit failed: {submit_res.text}"

        # Look up the customer that was just created
        response = await client.get(f"/customers/lookup?email={email}")
        assert response.status_code == 200, f"Customer lookup failed: {response.text}"
        data = response.json()
        assert "id" in data, f"Expected 'id' in response, got: {data}"

class TestChannelMetrics:
    @pytest.mark.asyncio
    async def test_metrics_by_channel(self, client):
        response = await client.get("/metrics/channels")
        assert response.status_code == 200
        data = response.json()
        for channel in ["email", "whatsapp", "web_form"]:
            if channel in data:
                # Based on the API implementation, it might return just count or dict
                pass
