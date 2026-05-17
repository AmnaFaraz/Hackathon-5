"""
Customer Success AI Agent — Production Implementation
Uses OpenAI GPT-4o directly via AsyncOpenAI SDK.
Falls back gracefully when OPENAI_API_KEY is not set.
"""
import os
import logging
from openai import AsyncOpenAI
from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("sk-placeholder"):
            logger.warning("OPENAI_API_KEY not set — AI responses will use fallback mode")
        _client = AsyncOpenAI(api_key=api_key or "sk-missing")
    return _client


async def run_agent(content: str, history: list | None = None) -> str:
    """
    Run the Customer Success AI agent against incoming message content.
    Sends the system prompt + conversation history + new message to GPT-4o.
    Falls back to a safe acknowledgment message on API errors.

    Args:
        content: The customer's message text.
        history: Optional list of prior messages [{"role": ..., "content": ...}]

    Returns:
        The agent's response as a plain string.
    """
    client = _get_client()

    # Build message chain: system + recent history (last 10) + new user message
    messages = [{"role": "system", "content": CUSTOMER_SUCCESS_SYSTEM_PROMPT}]

    if history:
        for msg in history[-10:]:
            role = msg.get("role", "user")
            msg_content = msg.get("content", "")
            if role in ("user", "assistant") and msg_content:
                messages.append({"role": role, "content": msg_content})

    messages.append({"role": "user", "content": content})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=800,
            temperature=0.3,
        )
        result = response.choices[0].message.content
        logger.info(f"GPT-4o response generated ({len(result)} chars)")
        return result

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        # Safe fallback — customer always gets a response
        return (
            "Thank you for reaching out to CloudFlow Support. "
            "We have received your request and a member of our support team "
            "will review it and get back to you as soon as possible. "
            "We apologize for any inconvenience caused."
        )
