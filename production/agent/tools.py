import json
import uuid
import logging
import os
from typing import Optional, List
from pydantic import BaseModel, Field
from production.database import queries
from production.agent.formatters import format_for_channel
from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.kafka_mock import FTEKafkaProducer, TOPICS

# Setup logging
logger = logging.getLogger(__name__)

producer = FTEKafkaProducer()


# --- Input Models ---

class KnowledgeSearchInput(BaseModel):
    query: str = Field(..., description="The user's question or search query for the documentation.")
    max_results: int = Field(default=5, description="Maximum number of results to return.")


class TicketInput(BaseModel):
    customer_id: str = Field(..., description="Customer email, phone, or ID.")
    issue: str = Field(..., description="A concise summary of the reported issue.")
    priority: str = Field(..., description="Priority level: low, medium, high, urgent.")
    category: Optional[str] = Field(None, description="Issue category (technical, billing, etc.).")
    channel: str = Field(..., description="Source channel: email, whatsapp, or web_form.")


class EscalationInput(BaseModel):
    ticket_id: str = Field(..., description="The ID of the ticket to be escalated.")
    reason: str = Field(..., description="Detailed reason for escalation.")
    urgency: str = Field(default="normal", description="Urgency: normal, high, critical.")


class ResponseInput(BaseModel):
    ticket_id: str = Field(..., description="The ticket ID associated with this response.")
    message: str = Field(..., description="The content of the response to send.")
    channel: str = Field(..., description="The channel to use for delivery.")


class HistoryInput(BaseModel):
    customer_id: str = Field(..., description="The identifier for the customer (email/phone).")


# --- Tool Decorator (local shim, compatible with openai-agents SDK) ---

def function_tool(func):
    """Marks a function as an AI agent tool."""
    func._is_tool = True
    return func


# --- Tool Functions ---

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """
    Searches the CloudFlow product documentation for relevant answers.
    Use this whenever a customer asks a how-to question or experiences a technical issue.
    """
    try:
        results = await queries.search_knowledge_base_text(input.query, input.max_results)
        if not results:
            return "No relevant documentation found."

        formatted = []
        for r in results:
            formatted.append(f"**{r['title']}**\n{r['content'][:300]}")

        return "\n\n---\n\n".join(formatted)
    except Exception as e:
        logger.error(f"Error in search_knowledge_base: {e}")
        return f"Error searching knowledge base: {str(e)}"


@function_tool
async def create_ticket(input: TicketInput) -> str:
    """
    Records a new support ticket in the database.
    MUST be called at the start of every new conversation to ensure tracking.
    Creates a new customer record if one does not exist.
    """
    try:
        # 1. Try to resolve existing customer
        customer = await queries.find_customer_by_email(input.customer_id)
        if not customer:
            customer = await queries.find_customer_by_phone(input.customer_id)

        # 2. Create customer if not found (handles first-time visitors)
        if not customer:
            logger.info(f"New customer — creating record for: {input.customer_id}")
            is_email = "@" in input.customer_id
            customer_id = await queries.insert_customer(
                email=input.customer_id if is_email else None,
                phone=None if is_email else input.customer_id,
                name="Customer",
            )
            id_type = "email" if is_email else "whatsapp"
            await queries.insert_customer_identifier(customer_id, id_type, input.customer_id)
        else:
            customer_id = str(customer["id"])

        # 3. Find or create a conversation
        conv = await queries.find_active_conversation(customer_id)
        if conv:
            conversation_id = str(conv["id"])
        else:
            conversation_id = await queries.insert_conversation(customer_id, input.channel)

        # 4. Create the ticket
        ticket_id = str(uuid.uuid4())
        await queries.create_ticket_record(
            ticket_id=ticket_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            source_channel=input.channel,
            category=input.category,
            priority=input.priority,
        )

        return f"Ticket created: {ticket_id}"
    except Exception as e:
        logger.error(f"Error in create_ticket: {e}")
        return f"Error creating ticket: {str(e)}"


@function_tool
async def get_customer_history(input: HistoryInput) -> str:
    """
    Retrieves previous interaction history for a customer.
    Use this to provide context-aware support.
    """
    try:
        # Resolve customer
        customer = await queries.find_customer_by_email(input.customer_id)
        if not customer:
            customer = await queries.find_customer_by_phone(input.customer_id)
        if not customer:
            return "No customer record found."

        conv = await queries.find_active_conversation(str(customer["id"]))
        if not conv:
            return "No active conversation history found."

        history = await queries.load_conversation_history(str(conv["id"]))
        if not history:
            return "No messages found for current conversation."

        formatted = [f"[{msg['role'].upper()}]: {msg['content']}" for msg in history]
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Error in get_customer_history: {e}")
        return f"Error fetching customer history: {str(e)}"


@function_tool
async def escalate_to_human(input: EscalationInput) -> str:
    """
    Transfers the conversation and ticket to a human support agent.
    Use for legal threats, refunds, extreme frustration, or repeated AI failures.
    """
    try:
        await queries.update_ticket_status(input.ticket_id, "escalated", input.reason)

        # Publish escalation event
        await producer.publish(
            TOPICS["escalations"],
            {
                "ticket_id": input.ticket_id,
                "reason": input.reason,
                "urgency": input.urgency,
                "escalated_at": str(uuid.uuid4()),
            },
        )

        return f"Escalated ticket {input.ticket_id} to human team. Reason: {input.reason}"
    except Exception as e:
        logger.error(f"Error in escalate_to_human: {e}")
        return f"Error during escalation: {str(e)}"


@function_tool
async def send_response(input: ResponseInput) -> str:
    """
    Dispatches a final formatted message to the customer through their preferred channel.
    ALWAYS call this as the final step of your workflow.
    """
    try:
        ticket = await queries.get_ticket_by_id(input.ticket_id)
        if not ticket:
            return f"Error: Ticket {input.ticket_id} not found."

        final_message = format_for_channel(input.message, input.channel, input.ticket_id)

        if input.channel == "email":
            handler = GmailHandler(
                os.getenv("GMAIL_CREDENTIALS_PATH", "./context/gmail-credentials.json")
            )
            await handler.send_reply(
                to_email=ticket.get("email"),
                subject=f"Update regarding your ticket {input.ticket_id}",
                body=final_message,
            )
        elif input.channel == "whatsapp":
            handler = WhatsAppHandler()
            await handler.send_message(
                to_phone=ticket.get("phone"),
                body=final_message,
            )

        return f"Response dispatched via {input.channel} for ticket {input.ticket_id}."
    except Exception as e:
        logger.error(f"Error in send_response: {e}")
        return f"Error sending response: {str(e)}"
