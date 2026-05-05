import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory queue replacing Kafka broker
_queues: dict[str, asyncio.Queue] = {}

TOPICS = {
    "tickets_incoming": "fte.tickets.incoming",
    "email_inbound": "fte.channels.email.inbound",
    "whatsapp_inbound": "fte.channels.whatsapp.inbound",
    "webform_inbound": "fte.channels.webform.inbound",
    "email_outbound": "fte.channels.email.outbound",
    "whatsapp_outbound": "fte.channels.whatsapp.outbound",
    "escalations": "fte.escalations",
    "metrics": "fte.metrics",
    "dlq": "fte.dlq"
}

def _get_queue(topic: str) -> asyncio.Queue:
    if topic not in _queues:
        _queues[topic] = asyncio.Queue()
    return _queues[topic]

class FTEKafkaProducer:
    async def start(self):
        logger.info("MockProducer started (in-memory queue mode)")

    async def stop(self):
        logger.info("MockProducer stopped")

    async def publish(self, topic: str, event: dict):
        event["timestamp"] = datetime.utcnow().isoformat()
        await _get_queue(topic).put(event)
        logger.info(f"Published to {topic}: {list(event.keys())}")

class FTEKafkaConsumer:
    def __init__(self, topics: list, group_id: str):
        self.topics = topics
        self.group_id = group_id

    async def start(self):
        logger.info(f"MockConsumer started for topics: {self.topics}")

    async def stop(self):
        logger.info("MockConsumer stopped")

    async def consume(self, handler):
        while True:
            for topic in self.topics:
                q = _get_queue(topic)
                if not q.empty():
                    msg = await q.get()
                    await handler(topic, msg)
            await asyncio.sleep(0.5)
