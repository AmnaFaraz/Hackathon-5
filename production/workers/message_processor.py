"""
Unified Message Processor — CloudFlow Customer Success AI
Consumes tickets from the queue, runs AI agent, delivers responses.
Now wired to real GPT-4o via AsyncOpenAI with real Gmail/WhatsApp delivery.
"""
import asyncio
import logging
import os
from datetime import datetime

from production.kafka_client import FTEKafkaProducer, FTEKafkaConsumer, TOPICS
from production.agent.customer_success_agent import run_agent
from production.agent.sentiment import analyze_sentiment, should_escalate
from production.agent.formatters import format_for_channel
from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.database import queries

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedMessageProcessor:
    def __init__(self):
        self.gmail_handler = GmailHandler(
            os.getenv("GMAIL_CREDENTIALS_PATH", "./context/gmail-credentials.json")
        )
        self.whatsapp_handler = WhatsAppHandler()
        self.producer = FTEKafkaProducer()

    async def start(self):
        """Starts the event-driven processing loop."""
        await self.producer.start()

        consumer = FTEKafkaConsumer(
            topics=[TOPICS["tickets_incoming"]],
            group_id="fte-message-processor",
        )
        await consumer.start()
        logger.info("Unified Message Processor started. Listening for tickets...")
        await consumer.consume(self.process_message)

    async def process_message(self, topic: str, message: dict):
        """Orchestrates the full lifecycle of a support interaction."""
        start_time = datetime.utcnow()
        try:
            channel = message.get("channel", "web_form")
            content = message.get("content", "")

            # 1. Identity Resolution
            customer_id = await self.resolve_customer(message)

            # 2. Context Management
            conversation_id = await self.get_or_create_conversation(customer_id, channel)

            # 3. Store Inbound Message
            await queries.insert_message(
                conversation_id=conversation_id,
                channel=channel,
                direction="inbound",
                role="user",
                content=content,
                channel_message_id=message.get("channel_message_id"),
            )

            # 4. Sentiment Analysis & Automatic Escalation Check
            sentiment_score = analyze_sentiment(content)
            escalate, reason = should_escalate(sentiment_score, content)

            if escalate:
                logger.info(f"Automatic escalation triggered: {reason}")
                await self.producer.publish(
                    TOPICS["escalations"],
                    {
                        "conversation_id": conversation_id,
                        "reason": reason,
                        "sentiment_score": sentiment_score,
                        "content": content,
                    },
                )

            # 5. Load Conversation History for AI Context
            history = await queries.load_conversation_history(conversation_id)

            # 6. Run AI Agent (Real GPT-4o via AsyncOpenAI)
            ai_response_text = await run_agent(content, history)

            # 7. Format response for the specific channel
            formatted_response = format_for_channel(
                ai_response_text, channel, message.get("ticket_id", "N/A")
            )

            # 8. Metrics
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            # 9. Store Outbound Message
            c_msg_id = f"ai-{datetime.utcnow().timestamp()}"
            await queries.insert_message(
                conversation_id=conversation_id,
                channel=channel,
                direction="outbound",
                role="assistant",
                content=formatted_response,
                latency_ms=latency_ms,
                channel_message_id=c_msg_id,
            )

            # 10. Physical Delivery to Customer
            if channel == "email":
                await self.gmail_handler.send_reply(
                    to_email=message.get("customer_email"),
                    subject=message.get("subject", "Support Update"),
                    body=formatted_response,
                    thread_id=message.get("thread_id"),
                )
            elif channel == "whatsapp":
                await self.whatsapp_handler.send_message(
                    to_phone=message.get("customer_phone"),
                    body=formatted_response,
                )

            # 11. Publish Metrics
            await self.producer.publish(
                TOPICS["metrics"],
                {
                    "metric_name": "ai_response_latency",
                    "metric_value": latency_ms,
                    "channel": channel,
                    "conversation_id": conversation_id,
                    "escalated": escalate,
                },
            )

            logger.info(
                f"Message processed: channel={channel}, latency={latency_ms}ms, "
                f"escalated={escalate}, response_len={len(formatted_response)}"
            )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            await self.handle_error(message, e)

    async def resolve_customer(self, message: dict) -> str:
        """Ensures a customer record exists before processing."""
        email = message.get("customer_email")
        phone = message.get("customer_phone")
        name = message.get("customer_name", "Valued Customer")

        customer = None
        if email:
            customer = await queries.find_customer_by_email(email)
        if not customer and phone:
            customer = await queries.find_customer_by_phone(phone)

        if customer:
            return str(customer["id"])

        # Create new customer record
        customer_id = await queries.insert_customer(email=email, phone=phone, name=name)
        if email:
            await queries.insert_customer_identifier(customer_id, "email", email)
        if phone:
            await queries.insert_customer_identifier(customer_id, "whatsapp", phone)

        return str(customer_id)

    async def get_or_create_conversation(self, customer_id: str, channel: str) -> str:
        """Links message to an existing active conversation or creates a new one."""
        active_conv = await queries.find_active_conversation(customer_id)
        if active_conv:
            return str(active_conv["id"])
        return await queries.insert_conversation(customer_id, channel)

    async def handle_error(self, message: dict, error: Exception):
        """Graceful failure — always escalate to human on processing errors."""
        logger.error(f"FATAL ERROR in processor: {str(error)}")
        await self.producer.publish(
            TOPICS["escalations"],
            {
                "ticket_id": message.get("ticket_id"),
                "error": str(error),
                "requires_human": True,
                "original_channel": message.get("channel"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


if __name__ == "__main__":
    processor = UnifiedMessageProcessor()
    asyncio.run(processor.start())
