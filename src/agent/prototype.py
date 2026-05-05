import os
import json
import re

class CustomerSuccessAI:
    def __init__(self):
        self.context_path = os.path.join(os.path.dirname(__file__), "../../context")
        self.product_docs = self._load_file("product-docs.md")
        self.escalation_rules = self._load_file("escalation-rules.md")
        
    def _load_file(self, filename):
        path = os.path.join(self.context_path, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def normalize_message(self, message):
        return message.strip().lower()

    def get_sentiment(self, message):
        # Prototype sentiment guess: 0.0 (angry) to 1.0 (happy)
        angry_words = ["ridiculous", "lost", "now", "breach", "legal", "sue", "locked"]
        message_lower = message.lower()
        
        # Count uppercase words (normalized for message length)
        words = message.split()
        caps_count = sum(1 for w in words if w.isupper() and len(w) > 1)
        
        score = 0.8 # Default neutral/positive
        
        if any(word in message_lower for word in angry_words):
            score -= 0.4
        
        if caps_count > 2 or "!" in message:
            score -= 0.2
            
        return max(0.1, min(1.0, score))

    def search_knowledge(self, query):
        # Simple keyword search in product docs
        # Split docs into sections based on ##
        sections = re.split(r'(?m)^## ', self.product_docs)
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
            # Replace arrows for terminal compatibility
            return best_match.replace("→", "->")
        return "I couldn't find a specific answer in our documentation."

    def decide_escalation(self, message, sentiment):
        # Rule 1: Keywords
        escalation_keywords = ["refund", "cancel", "lawyer", "legal", "sue", "human", "agent", "representative"]
        message_lower = message.lower()
        if any(kw in message_lower for kw in escalation_keywords):
            return True, "Triggered by sensitive keywords."
            
        # Rule 2: Sentiment
        if sentiment < 0.3:
            return True, f"Low sentiment score: {sentiment:.2f}"
            
        # Rule 6: Bug/Security
        if "data loss" in message_lower or "security" in message_lower:
            return True, "Security/Data Loss report."
            
        return False, "Handled by AI."

    def generate_response(self, message_base, channel, info):
        if "couldn't find" in info:
            info = "I'll make sure this gets resolved by checking with our specialized team."

        if channel == "email":
            return f"Subject: Re: Support Inquiry\n\nDear Customer,\n\nThank you for reaching out to TechCorp Support. {info}\n\nIf you have any further questions, please don't hesitate to ask.\n\nBest regards,\nTechCorp AI Success Team"
            
        elif channel == "whatsapp":
            # Short, emoji acceptable
            return f"Hi! {info} [Rocket Emoji] Let me know if that helps!"
            
        elif channel == "web_form":
            # Semi-formal
            return f"Hello, thank you for your submission. {info} \n\nPlease check your account settings for further details."
            
        return info

    def process_ticket(self, ticket):
        message = ticket.get("message", "")
        channel = ticket.get("channel", "email")
        
        normalized = self.normalize_message(message)
        sentiment = self.get_sentiment(message)
        info = self.search_knowledge(normalized)
        
        needs_escalation, reason = self.decide_escalation(message, sentiment)
        
        response = self.generate_response(message, channel, info)
        
        result = {
            "id": ticket.get("id"),
            "channel": channel,
            "sentiment": round(sentiment, 2),
            "escalation": "YES" if needs_escalation else "NO",
            "escalation_reason": reason,
            "response": response
        }
        return result

def run_prototype():
    ai = CustomerSuccessAI()
    
    # Load sample tickets
    tickets_path = os.path.join(os.path.dirname(__file__), "../../context/sample-tickets.json")
    with open(tickets_path, "r") as f:
        samples = json.load(f)
    
    # Select specific test cases from Step 4
    # 1. Normal Technical (Email) - ID 1
    # 2. Short WhatsApp - ID 2
    # 3. Angry Data Loss (Email) - ID 4
    # 4. Pricing (WhatsApp) - ID 5
    # 5. Web Form - ID 3
    
    test_ids = [1, 2, 4, 5, 3]
    test_tickets = [t for t in samples if t["id"] in test_ids]
    
    print("=== TECHCORP AI FTE PROTOTYPE TEST ===\n")
    for ticket in test_tickets:
        res = ai.process_ticket(ticket)
        print(f"TICKET #{res['id']} [{res['channel'].upper()}]")
        print(f"Customer: {ticket['message']}")
        print(f"Sentiment: {res['sentiment']}")
        print(f"Escalation: {res['escalation']} ({res['escalation_reason']})")
        print(f"Response:\n{res['response']}")
        print("-" * 40)

if __name__ == "__main__":
    run_prototype()
