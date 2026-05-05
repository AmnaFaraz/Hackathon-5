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
    customer_id: str = Field(..., description="Unique identifier for the customer (email, ID, or phone).")
    issue: str = Field(..., description="A concise summary of the reported issue.")
    priority: str = Field(..., description="Priority level: low, medium, high, urgent.")
    category: Optional[str] = Field(None, description="The category of the issue (technical, billing, etc.).")
    channel: str = Field(..., description="The source channel: email, whatsapp, or web_form.")

class EscalationInput(BaseModel):
    ticket_id: str = Field(..., description="The ID of the ticket to be escalated.")
    reason: str = Field(..., description="Detailed reason for escalation (e.g., legal mention, sentiment low).")
    urgency: str = Field(default="normal", description="Urgency of the escalation: normal, high, critical.")

class ResponseInput(BaseModel):
    ticket_id: str = Field(..., description="The ticket ID associated with this response.")
    message: str = Field(..., description="The content of the response to send.")
    channel: str = Field(..., description="The channel to use for delivery.")

class HistoryInput(BaseModel):
    customer_id: str = Field(..., description="The identifier for the customer (email/phone).")

# --- Tool Functions ---

def function_tool(func):
    """Placeholder for OpenAI Agents SDK @function_tool decorator"""
    func._is_tool = True
    return func

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
    """
    try:
        # 1. Resolve customer
        customer = await queries.find_customer_by_email(input.customer_id)
        if not customer:
            customer = await queries.find_customer_by_phone(input.customer_id)
            
        if not customer:
            return f"Error: Customer {input.customer_id} not found. Please resolve customer first."
        
        customer_id = customer['id']
        ticket_id = str(uuid.uuid4())
        
        # Find active conversation to link
        conv = await queries.find_active_conversation(customer_id)
        conversation_id = conv['id'] if conv else None
        
        # 2. Create ticket record
        await queries.create_ticket_record(
            ticket_id=ticket_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            source_channel=input.channel,
            category=input.category,
            priority=input.priority
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
        # First try to find active conversation
        conv = await queries.find_active_conversation(input.customer_id)
        if not conv:
            return "No active conversation history found."
            
        history = await queries.load_conversation_history(conv['id'])
        if not history:
            return "No history found for current conversation."
            
        formatted = []
        for msg in history:
            formatted.append(f"[{msg['role'].upper()}]: {msg['content']}")
            
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Error in get_customer_history: {e}")
        return f"Error fetching customer history: {str(e)}"

@function_tool
async def escalate_to_human(input: EscalationInput) -> str:
    """
    Transfers the conversation and ticket to a human support agent.
    Use this for legal threats, refunds, extreme frustration, or repeated AI failures.
    """
    try:
        await queries.update_ticket_status(input.ticket_id, "escalated", input.reason)
        
        # Publish escalation event to Kafka
        await producer.publish(TOPICS['escalations'], {
            "ticket_id": input.ticket_id,
            "reason": input.reason,
            "urgency": input.urgency,
            "timestamp": str(uuid.uuid4())
        })
        
        return f"Escalated ticket {input.ticket_id}: {input.reason}"
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
            handler = GmailHandler(os.getenv("GMAIL_CREDENTIALS_PATH", "./context/gmail-credentials.json"))
            await handler.send_reply(
                to_email=ticket['email'],
                subject=f"Update regarding your ticket {input.ticket_id}",
                body=final_message
            )
        elif input.channel == "whatsapp":
            handler = WhatsAppHandler()
            await handler.send_message(
                to_phone=ticket['phone'],
                body=final_message
            )
        
        return f"Response dispatched to channel {input.channel} for ticket {input.ticket_id}."
    except Exception as e:
        logger.error(f"Error in send_response: {e}")
        return f"Error sending response: {str(e)}"
