from enum import Enum
from agents import Agent, Runner, function_tool
from openai import OpenAI
from production.agent.tools import (
    search_knowledge_base, 
    create_ticket, 
    get_customer_history, 
    escalate_to_human, 
    send_response
)
from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from production.agent.formatters import format_for_channel as format_logic

class Channel(Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"

# --- Agent Definition ---

customer_success_agent = Agent(
    name="Customer Success FTE",
    model="gpt-4o",
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    tools=[
        search_knowledge_base, 
        create_ticket, 
        get_customer_history, 
        escalate_to_human, 
        send_response
    ]
)

# --- Channel Adaptation Wrapper ---

async def format_for_channel(response: str, channel: str, ticket_id: str = "N/A") -> str:
    """
    Wrapper for existing formatting logic to ensure channel consistency.
    """
    # Simply delegates to the formatter logic from Phase 1 Transition
    return format_logic(response, channel, ticket_id)
