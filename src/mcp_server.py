import os
import json
import re

# In-memory storage for the prototype
tickets = {}
customer_history = {
    "ali@example.com": [{"id": 1, "issue": "Password login issue", "status": "resolved"}],
    "angry@client.com": [{"id": 4, "issue": "Data loss complaint", "status": "open"}]
}
knowledge_base_path = os.path.join(os.path.dirname(__file__), "../context/product-docs.md")

def search_knowledge_base(query: str) -> str:
    """
    Searches the CloudFlow product documentation for relevant information based on the query.
    
    Args:
        query: The search term or question from the customer.
    Returns:
        The most relevant section of the documentation or a default message if not found.
    """
    if not os.path.exists(knowledge_base_path):
        return "Knowledge base unavailable."
        
    with open(knowledge_base_path, "r", encoding="utf-8") as f:
        docs = f.read()
        
    sections = re.split(r'(?m)^## ', docs)
    keywords = query.lower().split()
    
    best_match = ""
    max_matches = 0
    
    for section in sections:
        if not section.strip(): continue
        match_count = sum(1 for kw in keywords if kw in section.lower())
        if match_count > max_matches:
            max_matches = match_count
            best_match = section.strip()
            
    if max_matches > 0:
        return best_match.replace("→", "->")
    return "No relevant documentation found."

def create_ticket(customer_id: str, issue: str, priority: str, channel: str) -> str:
    """
    Creates a new support ticket in the system.
    
    Args:
        customer_id: Email or phone number of the customer.
        issue: Brief description of the problem.
        priority: Low, Medium, High, or Urgent.
        channel: email, whatsapp, or web_form.
    Returns:
        The ID of the newly created ticket.
    """
    ticket_id = f"TICK-{len(tickets) + 1001}"
    tickets[ticket_id] = {
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "channel": channel,
        "status": "open",
        "responses": []
    }
    
    # Update customer history
    if customer_id not in customer_history:
        customer_history[customer_id] = []
    customer_history[customer_id].append({"id": ticket_id, "issue": issue, "status": "open"})
    
    return ticket_id

def get_customer_history(customer_id: str) -> str:
    """
    Retrieves the past support history for a specific customer.
    
    Args:
        customer_id: The identifier for the customer (email/phone).
    Returns:
        A JSON string containing the list of previous tickets and their statuses.
    """
    history = customer_history.get(customer_id, [])
    return json.dumps(history, indent=2)

def escalate_to_human(ticket_id: str, reason: str) -> str:
    """
    Escalates an existing ticket to a human agent.
    
    Args:
        ticket_id: The ID of the ticket to escalate.
        reason: The reason for escalation (e.g., 'sentiment_low', 'legal_threat').
    Returns:
        A confirmation message of the escalation.
    """
    if ticket_id in tickets:
        tickets[ticket_id]["status"] = "escalated"
        tickets[ticket_id]["escalation_reason"] = reason
        return f"Ticket {ticket_id} has been escalated to a human agent. Reason: {reason}"
    return f"Error: Ticket {ticket_id} not found."

def send_response(ticket_id: str, message: str, channel: str) -> str:
    """
    Sends a response message back to the customer through the specified channel.
    
    Args:
        ticket_id: The ID of the ticket.
        message: The message content to send.
        channel: The channel to use for sending.
    Returns:
        A status message indicating success or failure.
    """
    if ticket_id in tickets:
        tickets[ticket_id]["responses"].append({"message": message, "channel": channel})
        # In a real system, this would call an API (SendGrid, Twilio, etc.)
        return f"Response sent to {tickets[ticket_id]['customer_id']} via {channel}."
    return f"Error: Ticket {ticket_id} not found."

# Mock server execution for testing
if __name__ == "__main__":
    print("MCP Server Tools Loaded (Mock Mode)")
    print(f"Test Search: {search_knowledge_base('reset password')[:50]}...")
    tid = create_ticket("user@test.com", "App is crashing", "High", "whatsapp")
    print(f"Created Ticket: {tid}")
    print(f"History: {get_customer_history('user@test.com')}")
    print(escalate_to_human(tid, "Sentiment low"))
    print(send_response(tid, "We are looking into it.", "whatsapp"))
