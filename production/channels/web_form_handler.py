import uuid
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from production.kafka_client import FTEKafkaProducer, TOPICS
from production.database import queries

# Setup logging
logger = logging.getLogger(__name__)

web_form_router = APIRouter(prefix="/support", tags=["support-form"])

# Global producer instance for the router
producer = FTEKafkaProducer()

# --- Models ---

class SupportFormSubmission(BaseModel):
    name: str
    email: EmailStr
    subject: str
    category: str
    message: str
    priority: str = "medium"
    attachments: List[str] = []

    @field_validator('name')
    @classmethod
    def name_must_be_long(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v

    @field_validator('message')
    @classmethod
    def message_must_be_long(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v

    @field_validator('category')
    @classmethod
    def category_must_be_valid(cls, v: str) -> str:
        valid_cats = ["general", "technical", "billing", "feedback", "bug_report"]
        if v not in valid_cats:
            raise ValueError(f'Category must be one of: {", ".join(valid_cats)}')
        return v

class SupportFormResponse(BaseModel):
    ticket_id: str
    message: str
    estimated_response_time: str

# --- Endpoints ---

@web_form_router.post("/submit", response_model=SupportFormResponse)
async def submit_form(submission: SupportFormSubmission):
    """
    Validates submission, records the ticket, and initiates AI processing via Kafka.
    (publish_to_kafka and create_ticket_record placeholder replacements)
    """
    try:
        # 1. Resolve customer
        customer = await queries.find_customer_by_email(submission.email)
        if not customer:
            customer_id = await queries.insert_customer(
                email=submission.email,
                name=submission.name
            )
            await queries.insert_customer_identifier(customer_id, "email", submission.email)
        else:
            customer_id = customer['id']

        # 2. Create conversation
        conversation_id = await queries.insert_conversation(customer_id, "web_form")
        
        # 3. Create ticket record (create_ticket_record call)
        ticket_id = str(uuid.uuid4())
        await queries.create_ticket_record(
            ticket_id=ticket_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            source_channel="web_form",
            category=submission.category,
            priority=submission.priority
        )
        
        message_data = {
            "channel": "web_form",
            "ticket_id": ticket_id,
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "customer_email": submission.email,
            "customer_name": submission.name,
            "subject": submission.subject,
            "content": submission.message,
            "category": submission.category,
            "priority": submission.priority,
            "received_at": datetime.utcnow().isoformat()
        }
        
        # 4. Push to Kafka for worker processing (publish_to_kafka call)
        await producer.publish(TOPICS['tickets_incoming'], message_data)
        
        return SupportFormResponse(
            ticket_id=ticket_id,
            message="Your request has been received. Our AI Success Agent is reviewing it now.",
            estimated_response_time="< 5 minutes"
        )
    except Exception as e:
        logger.error(f"Error in submit_form: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit form: {str(e)}")

@web_form_router.get("/ticket/{ticket_id}")
async def check_ticket_status(ticket_id: str):
    """
    Fetches ticket status and conversation history.
    """
    try:
        ticket = await queries.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        # Also load messages for this ticket's conversation
        messages = await queries.load_conversation_history(ticket['conversation_id'])
            
        return {
            "ticket_id": ticket_id,
            "status": ticket.get("status", "open"),
            "customer_name": ticket.get("name"),
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in check_ticket_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
