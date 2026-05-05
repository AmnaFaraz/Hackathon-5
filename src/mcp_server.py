"""
MCP Server — CloudFlow Customer Success FTE
Exercise 1.4 Implementation: Exposes agent capabilities as MCP tools.
Connects to the production agent tools defined in production/agent/tools.py
"""

import sys
import os

# Add production path so we can import agent tools
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'production'))

from mcp.server import Server
from mcp.types import Tool, TextContent
from enum import Enum


class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


server = Server("cloudflow-customer-success-fte")


@server.tool("search_knowledge_base")
async def search_knowledge_base(query: str, max_results: int = 5) -> str:
    """
    Search product documentation for relevant information.
    Use when customer asks about product features or needs technical help.
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default 5)
    Returns:
        Formatted search results with relevance scores
    """
    from agent.tools import search_knowledge_base as prod_search
    from agent.tools import KnowledgeSearchInput
    result = await prod_search(KnowledgeSearchInput(
        query=query,
        max_results=max_results
    ))
    return result


@server.tool("create_ticket")
async def create_ticket(
    customer_id: str,
    issue: str,
    priority: str,
    channel: str
) -> str:
    """
    Create a support ticket in the CRM system with channel tracking.
    ALWAYS call this at the start of every customer interaction.
    Args:
        customer_id: Unique identifier for the customer
        issue: Description of the customer's issue
        priority: Ticket priority — low, medium, or high
        channel: Source channel — email, whatsapp, or web_form
    Returns:
        Created ticket ID
    """
    from agent.tools import create_ticket as prod_create
    from agent.tools import TicketInput
    result = await prod_create(TicketInput(
        customer_id=customer_id,
        issue=issue,
        priority=priority,
        channel=Channel(channel)
    ))
    return result


@server.tool("get_customer_history")
async def get_customer_history(customer_id: str) -> str:
    """
    Get customer interaction history across ALL channels.
    Use this to understand context from previous conversations
    even if they happened on a different channel.
    Args:
        customer_id: Unique identifier for the customer
    Returns:
        Formatted history of all past interactions
    """
    from agent.tools import get_customer_history as prod_history
    result = await prod_history(customer_id)
    return result


@server.tool("escalate_to_human")
async def escalate_to_human(
    ticket_id: str,
    reason: str,
    urgency: str = "normal"
) -> str:
    """
    Escalate conversation to human support team.
    Use when: pricing questions, refund requests, legal mentions,
    negative sentiment, or customer explicitly asks for human help.
    Args:
        ticket_id: The ticket to escalate
        reason: Clear reason for escalation
        urgency: normal or urgent
    Returns:
        Escalation confirmation with reference ID
    """
    from agent.tools import escalate_to_human as prod_escalate
    from agent.tools import EscalationInput
    result = await prod_escalate(EscalationInput(
        ticket_id=ticket_id,
        reason=reason,
        urgency=urgency
    ))
    return result


@server.tool("send_response")
async def send_response(
    ticket_id: str,
    message: str,
    channel: str
) -> str:
    """
    Send response to customer via their preferred channel.
    Response is automatically formatted for channel constraints.
    Email: formal with greeting and signature.
    WhatsApp: concise under 300 characters.
    Web: semi-formal and readable.
    ALWAYS use this tool to reply — never respond directly.
    Args:
        ticket_id: The ticket being responded to
        message: The response message content
        channel: Target channel — email, whatsapp, or web_form
    Returns:
        Delivery status confirmation
    """
    from agent.tools import send_response as prod_send
    from agent.tools import ResponseInput
    result = await prod_send(ResponseInput(
        ticket_id=ticket_id,
        message=message,
        channel=Channel(channel)
    ))
    return result


@server.tool("analyze_sentiment")
async def analyze_sentiment(message: str) -> str:
    """
    Analyze customer message sentiment.
    Use on every incoming message to detect frustration early.
    Args:
        message: The customer message text to analyze
    Returns:
        Sentiment score between 0.0 (very negative) and 1.0 (very positive)
        and confidence level
    """
    # Lightweight sentiment check — production uses ML model
    negative_keywords = [
        "angry", "furious", "terrible", "broken", "useless",
        "worst", "hate", "ridiculous", "lawsuit", "refund",
        "lawyer", "cancel", "scam", "fraud"
    ]
    positive_keywords = [
        "thank", "great", "excellent", "happy", "love",
        "perfect", "amazing", "helpful", "wonderful"
    ]

    message_lower = message.lower()
    neg_count = sum(1 for w in negative_keywords if w in message_lower)
    pos_count = sum(1 for w in positive_keywords if w in message_lower)

    if neg_count > pos_count:
        score = max(0.1, 0.5 - (neg_count * 0.1))
        label = "negative"
    elif pos_count > neg_count:
        score = min(0.95, 0.6 + (pos_count * 0.1))
        label = "positive"
    else:
        score = 0.5
        label = "neutral"

    return f"sentiment: {label} | score: {score:.2f} | escalate: {score < 0.3}"


if __name__ == "__main__":
    server.run()
