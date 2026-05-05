def format_for_channel(response: str, channel: str, ticket_id: str = "N/A") -> str:
    """
    Adapts the raw response text to meet specific channel requirements and brand voice.
    
    Args:
        response: The raw logic-based response message.
        channel: The destination channel (email, whatsapp, web_form).
        ticket_id: The ID of the associated ticket for reference.
        
    Returns:
        A channel-optimized string.
    """
    
    if channel == "email":
        return (
            f"Dear Customer,\n\n"
            f"{response}\n\n"
            f"If you have further questions, please reply to this email.\n\n"
            f"Reference Ticket: {ticket_id}\n\n"
            f"Best regards,\n"
            f"TechCorp AI Support Team"
        )
        
    elif channel == "whatsapp":
        # Rule: Truncate to 300 chars if longer
        truncated_response = response[:290] + "..." if len(response) > 290 else response
        return (
            f"{truncated_response}\n\n"
            f"Reply for more help or type 'human' for live support."
        )
        
    elif channel == "web_form":
        return (
            f"Hello, thank you for your submission.\n\n"
            f"{response}\n\n"
            f"---\n"
            f"Need more help? Reply to this message or visit our support portal."
        )
        
    return response
