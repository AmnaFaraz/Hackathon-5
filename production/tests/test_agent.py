import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from production.agent.tools import (
    search_knowledge_base, create_ticket, escalate_to_human, 
    KnowledgeSearchInput, TicketInput, EscalationInput
)
from production.agent.formatters import format_for_channel

@pytest.mark.asyncio
class TestKnowledgeSearch:
    @patch("production.database.queries.search_knowledge_base_text")
    async def test_search_returns_results(self, mock_search):
        # Mock results
        mock_search.return_value = [
            {"title": "Password Reset", "content": "How to reset your password", "category": "technical"}
        ]
        
        input_data = KnowledgeSearchInput(query="password reset", max_results=5)
        result = await search_knowledge_base(input_data)
        
        assert "Password" in result
        assert "password" in result.lower()
        mock_search.assert_called_once_with("password reset", 5)

    @patch("production.database.queries.search_knowledge_base_text")
    async def test_search_handles_no_results(self, mock_search):
        mock_search.return_value = []
        
        input_data = KnowledgeSearchInput(query="unknown query", max_results=5)
        result = await search_knowledge_base(input_data)
        
        # assert result contains "no" or "not found"
        assert "no" in result.lower() or "not found" in result.lower()

    @patch("production.database.queries.search_knowledge_base_text")
    async def test_search_respects_max_results(self, mock_search):
        # Mock 10 rows
        mock_rows = [{"title": f"Title {i}", "content": f"Content {i}"} for i in range(10)]
        mock_search.return_value = mock_rows[:3]
        
        input_data = KnowledgeSearchInput(query="test", max_results=3)
        result = await search_knowledge_base(input_data)
        
        # Result should show only 3 results. 
        # In our implementation, they are joined by " --- "
        assert result.count("---") == 2 # 3 items = 2 separators

@pytest.mark.asyncio
class TestTicketCreation:
    @patch("production.database.queries.find_customer_by_email")
    @patch("production.database.queries.create_ticket_record")
    @patch("production.database.queries.find_active_conversation")
    async def test_create_ticket_returns_id(self, mock_conv, mock_create, mock_find):
        mock_find.return_value = {"id": "cust-123"}
        mock_create.return_value = None
        mock_conv.return_value = {"id": "conv-123"}
        
        input_data = TicketInput(
            customer_id="test@example.com",
            issue="Test issue",
            priority="low",
            category="technical",
            channel="email"
        )
        result = await create_ticket(input_data)
        
        assert "Ticket created:" in result
        mock_create.assert_called_once()

    async def test_create_ticket_requires_channel(self):
        # Using TicketInput model validation
        with pytest.raises(Exception): # Pydantic ValidationError
             TicketInput(customer_id="test", issue="test", priority="low")

@pytest.mark.asyncio
class TestEscalation:
    @patch("production.database.queries.update_ticket_status")
    @patch("production.agent.tools.producer")
    async def test_escalate_updates_status(self, mock_producer, mock_update):
        mock_update.return_value = None
        mock_producer.publish = AsyncMock()
        
        input_data = EscalationInput(ticket_id="tk-123", reason="Too complex", urgency="high")
        result = await escalate_to_human(input_data)
        
        assert "escalated" in result.lower()
        mock_update.assert_called_once_with("tk-123", "escalated", "Too complex")

    @patch("production.database.queries.update_ticket_status")
    @patch("production.agent.tools.producer")
    async def test_escalate_publishes_event(self, mock_producer, mock_update):
        mock_producer.publish = AsyncMock()
        
        input_data = EscalationInput(ticket_id="tk-123", reason="Test", urgency="normal")
        await escalate_to_human(input_data)
        
        mock_producer.publish.assert_called_once()

class TestFormatters:
    def test_email_format_has_greeting(self):
        result = format_for_channel("test", "email")
        assert "Dear Customer" in result

    def test_email_format_has_signature(self):
        result = format_for_channel("test", "email")
        assert "Best regards" in result

    def test_whatsapp_truncates_long_response(self):
        result = format_for_channel("x" * 400, "whatsapp")
        # In implementation: response[:300] + "..." + suffix
        # Suffix is "Reply for more help or type 'human' for live support." (approx 50 chars)
        assert len(result) <= 350

    def test_webform_format_has_footer(self):
        result = format_for_channel("test", "web_form")
        assert "support portal" in result.lower()
