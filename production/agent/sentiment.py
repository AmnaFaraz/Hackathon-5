import re

POSITIVE_WORDS = ["thank", "great", "excellent", "perfect", "love", "happy", "appreciate", "wonderful", "amazing", "helpful"]
NEGATIVE_WORDS = ["terrible", "awful", "horrible", "useless", "broken", "ridiculous", "furious", "angry", "frustrated", "disappointed", "lawsuit", "legal", "sue", "refund", "cancel"]
ESCALATION_WORDS = ["lawyer", "attorney", "legal", "sue", "lawsuit", "court"]

def analyze_sentiment(text: str) -> float:
    """
    Returns sentiment score between 0.0 (very negative) and 1.0 (very positive).
    Score below 0.3 triggers escalation.
    """
    text_lower = text.lower()
    
    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    escalation_flag = any(word in text_lower for word in ESCALATION_WORDS)
    
    if escalation_flag:
        return 0.1
    
    total = positive_count + negative_count
    if total == 0:
        return 0.6
    
    score = positive_count / total if total > 0 else 0.6
    return round(max(0.1, min(1.0, score)), 2)

def should_escalate(sentiment_score: float, message: str) -> tuple[bool, str]:
    """
    Returns (should_escalate, reason) based on sentiment and keywords.
    """
    message_lower = message.lower()
    
    if any(word in message_lower for word in ESCALATION_WORDS):
        return True, "legal_mention"
    
    if any(word in message_lower for word in ["refund", "cancel my account"]):
        return True, "refund_request"
    
    if sentiment_score < 0.3:
        return True, "negative_sentiment"
    
    if "human" in message_lower or "agent" in message_lower or "representative" in message_lower:
        return True, "customer_requested_human"
    
    return False, ""
