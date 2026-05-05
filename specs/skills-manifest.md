# Agent Skills Manifest — Customer Success FTE

## 1. Knowledge Retrieval Skill
- **When to use:** When a customer asks a question about product features, settings, or "how-to" guides.
- **Inputs:** `query` (string), `context_files` (path).
- **Outputs:** `answer_text` (string), `source_confidence` (float).

## 2. Sentiment Analysis Skill
- **When to use:** Every input message must be analyzed for emotional tone to determine urgency and escalation needs.
- **Inputs:** `message` (string).
- **Outputs:** `sentiment_score` (0.0=angry, 1.0=happy), `emotional_label` (string).

## 3. Escalation Decision Skill
- **When to use:** After sentiment analysis and knowledge retrieval, to decide if a human is needed.
- **Inputs:** `sentiment_score`, `keywords_found`, `search_results_found`.
- **Outputs:** `should_escalate` (boolean), `escalation_reason` (string).

## 4. Channel Adaptation Skill
- **When to use:** Before sending any response to ensure the format matches the interaction channel.
- **Inputs:** `raw_response`, `target_channel` (email/whatsapp/web_form).
- **Outputs:** `formatted_response` (string).

## 5. Customer Identification Skill
- **When to use:** At the start of an interaction to link the message to an existing account.
- **Inputs:** `channel_identifier` (email/phone), `database_lookup`.
- **Outputs:** `customer_profile` (object), `is_enterprise` (boolean).
