import os
import json
import logging
import asyncpg
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_pool = None

async def get_db_pool():
    """Singleton connection pool using env vars, bound to the running event loop."""
    global _pool
    import asyncio
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    # Recreate the pool if it doesn't exist, has a different loop, or is closed
    if _pool is None or (current_loop and getattr(_pool, "_loop", None) != current_loop) or getattr(_pool, "_closed", False):
        if _pool is not None:
            try:
                await _pool.close()
            except Exception:
                pass
        try:
            _pool = await asyncpg.create_pool(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "fte_db"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "localpassword"),
                min_size=5,
                max_size=20
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Error creating DB pool: {e}")
            raise
    return _pool

async def find_customer_by_email(email: str) -> dict | None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, email, phone, name FROM customers WHERE email = $1", email)
        return dict(row) if row else None

async def find_customer_by_phone(phone: str) -> dict | None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        customer_id = await conn.fetchval(
            "SELECT customer_id FROM customer_identifiers WHERE identifier_type='whatsapp' AND identifier_value=$1", 
            phone
        )
        if customer_id:
            row = await conn.fetchrow("SELECT id, email, phone, name FROM customers WHERE id = $1", customer_id)
            return dict(row) if row else None
        return None

async def insert_customer(email: str = None, phone: str = None, name: str = None) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        customer_id = await conn.fetchval(
            "INSERT INTO customers (email, phone, name) VALUES ($1, $2, $3) RETURNING id",
            email, phone, name
        )
        return str(customer_id)

async def insert_customer_identifier(customer_id: str, identifier_type: str, identifier_value: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value) VALUES ($1, $2, $3)",
            customer_id, identifier_type, identifier_value
        )

async def find_active_conversation(customer_id: str) -> dict | None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM conversations WHERE customer_id=$1 AND status='active' AND started_at > NOW() - INTERVAL '24 hours' ORDER BY started_at DESC LIMIT 1",
            customer_id
        )
        return dict(row) if row else None

async def insert_conversation(customer_id: str, channel: str) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        conversation_id = await conn.fetchval(
            "INSERT INTO conversations (customer_id, initial_channel, status) VALUES ($1, $2, 'active') RETURNING id",
            customer_id, channel
        )
        return str(conversation_id)

async def insert_message(conversation_id: str, channel: str, direction: str, role: str, content: str, latency_ms: int = None, tool_calls: list = None, channel_message_id: str = None, delivery_status: str = "pending"):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        await conn.execute(
            """INSERT INTO messages 
            (conversation_id, channel, direction, role, content, latency_ms, tool_calls, channel_message_id, delivery_status) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            conversation_id, channel, direction, role, content, latency_ms, tool_calls_json, channel_message_id, delivery_status
        )

async def load_conversation_history(conversation_id: str) -> list[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content, channel, created_at FROM messages WHERE conversation_id=$1 ORDER BY created_at ASC",
            conversation_id
        )
        return [{"role": row["role"], "content": row["content"]} for row in rows]

async def create_ticket_record(ticket_id: str, customer_id: str, conversation_id: str, source_channel: str, category: str = None, priority: str = "medium"):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO tickets (id, customer_id, conversation_id, source_channel, category, priority, status) VALUES ($1, $2, $3, $4, $5, $6, 'open')",
            ticket_id, customer_id, conversation_id, source_channel, category, priority
        )

async def get_ticket_by_id(ticket_id: str) -> dict | None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT t.*, c.email, c.phone FROM tickets t JOIN customers c ON t.customer_id=c.id WHERE t.id=$1",
            ticket_id
        )
        return dict(row) if row else None

async def update_ticket_status(ticket_id: str, status: str, resolution_notes: str = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE tickets SET status=$1, resolution_notes=$2 WHERE id=$3",
            status, resolution_notes, ticket_id
        )

async def update_delivery_status(channel_message_id: str, status: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET delivery_status=$1 WHERE channel_message_id=$2",
            status, channel_message_id
        )

async def get_channel_metrics(hours: int = 24) -> list[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        query = """
            SELECT 
                initial_channel, 
                COUNT(*) as total_conversations, 
                AVG(COALESCE(sentiment_score, 0)) as avg_sentiment, 
                COUNT(*) FILTER (WHERE status='escalated') as escalations 
            FROM conversations 
            WHERE started_at > NOW() - $1::interval 
            GROUP BY initial_channel
        """
        rows = await conn.fetch(query, timedelta(hours=hours))
        return [dict(row) for row in rows]

async def insert_knowledge_base_entry(title: str, content: str, category: str = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO knowledge_base (title, content, category) VALUES ($1, $2, $3)",
            title, content, category
        )

async def search_knowledge_base_text(query: str, max_results: int = 5) -> list[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT title, content, category FROM knowledge_base WHERE content ILIKE '%' || $1 || '%' OR title ILIKE '%' || $1 || '%' LIMIT $2",
            query, max_results
        )
        return [dict(row) for row in rows]
