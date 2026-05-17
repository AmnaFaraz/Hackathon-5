"""
Sentiment analysis module for CloudFlow Customer Success AI.
Provides lightweight keyword-based sentiment scoring and escalation logic.
Production-ready with no external dependencies.
"""

NEGATIVE_KEYWORDS = [
    "angry", "furious", "terrible", "broken", "useless", "worst", "hate",
    "ridiculous", "lawsuit", "refund", "lawyer", "cancel", "scam", "fraud",
    "disgusting", "horrible", "unacceptable", "disappointed", "frustrated",
    "data loss", "security breach", "lost my data", "lost all"
]

POSITIVE_KEYWORDS = [
    "thank", "great", "excellent", "happy", "love", "perfect", "amazing",
    "helpful", "wonderful", "appreciate", "awesome", "fantastic", "satisfied"
]

ESCALATION_KEYWORDS = [
    "refund", "cancel", "lawyer", "legal", "sue", "human", "agent",
    "representative", "data loss", "security breach", "fraud", "scam",
    "lost all my", "my data is gone"
]


def analyze_sentiment(message: str) -> float:
    """
    Analyze customer message sentiment.
    Returns score between 0.0 (very negative) and 1.0 (very positive).
    """
    if not message:
        return 0.5

    message_lower = message.lower()
    neg_count = sum(1 for w in NEGATIVE_KEYWORDS if w in message_lower)
    pos_count = sum(1 for w in POSITIVE_KEYWORDS if w in message_lower)

    # Excessive caps = frustration signal
    words = message.split()
    caps_count = sum(1 for w in words if w.isupper() and len(w) > 1)
    if caps_count > 2:
        neg_count += 1

    # Excessive exclamation marks = frustration signal
    if message.count("!") > 2:
        neg_count += 1

    if neg_count > pos_count:
        score = max(0.1, 0.5 - (neg_count * 0.1))
        return round(score, 2)
    elif pos_count > neg_count:
        score = min(0.95, 0.6 + (pos_count * 0.1))
        return round(score, 2)
    else:
        return 0.5


def should_escalate(score: float, message: str) -> tuple[bool, str]:
    """
    Determines if a message should be escalated to a human agent.
    Returns (should_escalate: bool, reason: str).
    """
    message_lower = message.lower()

    # Hard keyword triggers — always escalate immediately
    for keyword in ESCALATION_KEYWORDS:
        if keyword in message_lower:
            return True, f"Escalation keyword detected: '{keyword}'"

    # Sentiment-based escalation
    if score < 0.3:
        return True, f"Low sentiment score ({score:.2f}) — customer appears highly frustrated"

    return False, "Handled by AI agent"
