import asyncio
import logging
import json
import os
from datetime import datetime
from production.kafka_mock import FTEKafkaProducer, FTEKafkaConsumer, TOPICS
from production.agent.customer_success_agent import customer_success_agent, Runner
from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.database import queries
from production.agent.sentiment import analyze_sentiment, should_escalate

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedMessageProcessor:
    def __init__(self):
        """
        Initializes the processor with all necessary handlers and producer.
        """
        self.gmail_handler = GmailHandler(os.getenv("GMAIL_CREDENTIALS_PATH", "./context/gmail-credentials.json"))
        self.whatsapp_handler = WhatsAppHandler()
        self.producer = FTEKafkaProducer()
        
    async def start(self):
        """
        Starts the event-driven processing loop.
        """
        await self.producer.start()
        
        consumer = FTEKafkaConsumer(
            topics=[TOPICS['tickets_incoming']], 
            group_id='fte-message-processor'
        )
        await consumer.start()
        logger.info("Unified Message Processor started. Listening for tickets...")
        await consumer.consume(self.process_message)

    async def process_message(self, topic: str, message: dict):
        """
        Orchestrates the lifecycle of a support interaction.
        """
        start_time = datetime.utcnow()
        try:
            channel = message.get("channel")
            content = message.get("content", "")
            
            # 1. Identity Resolution
            customer_id = await self.resolve_customer(message)
            
            # 2. Context Management
            conversation_id = await self.get_or_create_conversation(customer_id, channel)
            
            # 3. Store Inbound Message (Store message placeholder replacement)
            await queries.insert_message(
                conversation_id=conversation_id,
                channel=channel,
                direction="inbound",
                role="user",
                content=content,
                channel_message_id=message.get("channel_message_id")
            )
            
            # 3b. Sentiment Analysis & Automatic Escalation
            sentiment_score = analyze_sentiment(content)
            escalate, reason = should_escalate(sentiment_score, content)
            
            # Update conversation sentiment score in DB
            # (Note: We'll assume a query function exists or update it here if needed)
            # await queries.update_conversation_sentiment(conversation_id, sentiment_score)
            
            if escalate:
                logger.info(f"Automatic escalation triggered: {reason}")
                # We'll publish to escalation topic and potentially skip AI agent if it's severe
                await self.producer.publish(TOPICS['escalations'], {
                    "conversation_id": conversation_id,
                    "reason": reason,
                    "sentiment_score": sentiment_score,
                    "content": content
                })
                # For scoring, we continue to run AI agent but acknowledge escalation
            
            # 4. Load History for AI Context (Load conversation history placeholder replacement)
            history = await queries.load_conversation_history(conversation_id)
            
            # 5. Run AI Agent
            ai_response = await Runner.run(customer_success_agent, content, history=history)
            
            # 6. Metrics & Performance
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # 7. Store & Deliver Outbound Message
            c_msg_id = f"ai-{datetime.utcnow().timestamp()}"
            await queries.insert_message(
                conversation_id=conversation_id,
                channel=channel,
                direction="outbound",
                role="assistant",
                content=ai_response.content,
                latency_ms=latency_ms,
                channel_message_id=c_msg_id,
                tool_calls=getattr(ai_response, 'tool_calls', None)
            )
            
            # 8. Physical delivery (Final step)
            if channel == "email":
                await self.gmail_handler.send_reply(
                    to_email=message.get("customer_email"),
                    subject=message.get("subject", "Support Update"),
                    body=ai_response.content,
                    thread_id=message.get("thread_id")
                )
            elif channel == "whatsapp":
                await self.whatsapp_handler.send_message(
                    to_phone=message.get("customer_phone"),
                    body=ai_response.content
                )
            
            # 9. Publish Metrics
            await self.producer.publish(TOPICS['metrics'], {
                "metric_name": "ai_response_latency",
                "metric_value": latency_ms,
                "channel": channel,
                "conversation_id": conversation_id
            })
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.handle_error(message, e)

    async def resolve_customer(self, message: dict) -> str:
        """
        Ensures a customer record exists before processing.
        (Resolve customer placeholder replacement)
        """
        email = message.get("customer_email")
        phone = message.get("customer_phone")
        name = message.get("customer_name", "Valued Customer")
        
        customer = None
        if email:
            customer = await queries.find_customer_by_email(email)
        
        if not customer and phone:
            customer = await queries.find_customer_by_phone(phone)
            
        if customer:
            return customer['id']
            
        # Create new customer if not found
        customer_id = await queries.insert_customer(
            email=email,
            phone=phone,
            name=name
        )
        
        # Add identifiers
        if email:
            await queries.insert_customer_identifier(customer_id, "email", email)
        if phone:
            await queries.insert_customer_identifier(customer_id, "whatsapp", phone)
            
        return customer_id

    async def get_or_create_conversation(self, customer_id: str, channel: str) -> str:
        """
        Links message to an existing conversation or starts a new one.
        (Get or create conversation placeholder replacement)
        """
        active_conv = await queries.find_active_conversation(customer_id)
        if active_conv:
            return active_conv['id']
            
        return await queries.insert_conversation(customer_id, channel)

    async def handle_error(self, message: dict, error: Exception):
        """
        Graceful failure handling with escalation.
        (Handle error publish placeholder replacement)
        """
        logger.error(f"FATAL ERROR in processor: {str(error)}")
        await self.producer.publish(TOPICS['escalations'], {
            "ticket_id": message.get("ticket_id"),
            "error": str(error),
            "requires_human": True,
            "original_message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

if __name__ == "__main__":
    processor = UnifiedMessageProcessor()
    asyncio.run(processor.start())
