import uuid
import logging
import os
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.web_form_handler import web_form_router
from production.kafka_mock import FTEKafkaProducer, TOPICS
from production.database import queries

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- App Init ---

app = FastAPI(
    title="Customer Success FTE API",
    description="24/7 AI-powered customer support across Email, WhatsApp, and Web",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Global Instances ---

kafka_producer = FTEKafkaProducer()
gmail_handler = GmailHandler(os.getenv("GMAIL_CREDENTIALS_PATH", "./context/gmail-credentials.json"))
whatsapp_handler = WhatsAppHandler()

# --- Lifecycle Hooks ---

@app.on_event("startup")
async def startup_event():
    await kafka_producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await kafka_producer.stop()

# --- Routers ---

app.include_router(web_form_router)

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """
    Service health and status of channel integrations.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "channels": {
            "email": "active",
            "whatsapp": "active",
            "web_form": "active"
        }
    }

@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives Pub/Sub notifications from Google Cloud.
    """
    try:
        data = await request.json()
        messages = await gmail_handler.process_notification(data)
        
        for msg_meta in messages:
            msg = await gmail_handler.get_message(msg_meta['id'])
            background_tasks.add_task(kafka_producer.publish, TOPICS['tickets_incoming'], msg)
            
        return {"status": "accepted", "count": len(messages)}
    except Exception as e:
        logger.error(f"Error in gmail_webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives inbound messages from Twilio.
    """
    try:
        if not await whatsapp_handler.validate_webhook(request):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
            
        form_data = await request.form()
        message_data = await whatsapp_handler.process_webhook(dict(form_data))
        
        background_tasks.add_task(kafka_producer.publish, TOPICS['tickets_incoming'], message_data)
        
        # Return empty TwiML response as status 200 acknowledge
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        return Response(content=twiml, media_type="application/xml")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in whatsapp_webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/whatsapp/status")
async def whatsapp_status_webhook(request: Request):
    """
    Updates delivery status (delivered, read, etc.) in the database.
    (update_delivery_status placeholder replacement)
    """
    try:
        form_data = await request.form()
        sid = form_data.get("SmsSid")
        status = form_data.get("SmsStatus")
        if sid and status:
            await queries.update_delivery_status(sid, status)
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error in whatsapp_status_webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Fetches full history of a given conversation.
    (load_conversation_history placeholder replacement)
    """
    history = await queries.load_conversation_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found or empty")
    return {"conversation_id": conversation_id, "messages": history}

@app.get("/customers/lookup")
async def lookup_customer(email: Optional[str] = None, phone: Optional[str] = None):
    """
    Cross-channel customer identification.
    (find_customer placeholder replacement)
    """
    customer = None
    if email:
        customer = await queries.find_customer_by_email(email)
    elif phone:
        customer = await queries.find_customer_by_phone(phone)
        
    if not customer:
        if not email and not phone:
             raise HTTPException(status_code=400, detail="Must provide at least email or phone")
        raise HTTPException(status_code=404, detail="Customer not found")
        
    return customer

@app.get("/metrics/channels")
async def get_channel_metrics():
    """
    Aggregates conversation volume per channel for the last 24h.
    (get_channel_metrics placeholder replacement)
    """
    try:
        metrics = await queries.get_channel_metrics(hours=24)
        return {m['initial_channel']: m for m in metrics}
    except Exception as e:
        logger.error(f"Error in get_channel_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
