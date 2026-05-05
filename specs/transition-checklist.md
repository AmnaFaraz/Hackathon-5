# Transition Checklist — Customer Success AI FTE

## 1. Discovered Requirements
1. **Multi-Channel Support:** Must handle Email, WhatsApp, and Web Form inputs natively.
2. **Automated Documentation Retrieval:** System must perform keyword/semantic search against product docs before responding.
3. **Sentiment-Aware Response:** Escalation should trigger if sentiment score is below 0.3.
4. **Keyword Escalation:** Immediate human handoff for legal terms (lawyer, sue, legal) and financial terms (refund, cancel).
5. **Security/Integrity Triggers:** Urgent escalation for mentions of "data loss" or "security breach".
6. **Tone Consistency:** Responses must follow channel-specific style guides (Formal, conversational, or semi-formal).
7. **Ticket Lifecycle:** Every interaction must be logged as a ticket with status tracking.
8. **Enterprise Awareness:** Priority handling for Enterprise-level pricing and SLA inquiries.
9. **No Hallucination:** If no answer is found, the system must defer to a human rather than guessing.
10. **High Performance:** Response latency must be minimal (< 2s targeted in production).

## 2. Working System Prompt (Extracted from Prototype)
> "You are the TechCorp AI Success Agent. Your goal is to help users with 'CloudFlow' inquiries. Be helpful, professional, and empathetic. 
> For **Email**, use a formal subject and signature. 
> For **WhatsApp**, be brief and conversational. 
> For **Web Forms**, provide actionable steps. 
> **Escalate immediately** if the user mentions refunds, legal action, or explicitly asks for a human. 
> If you cannot find an answer in the documentation, state that you will check with the specialized team. 
> Never say 'I don't know' or 'Not my problem'."

## 3. Top 10 Edge Cases & Handling
| Edge Case | Handling Strategy |
|-----------|-------------------|
| Empty message submitted | Return 422 Unprocessed Entity via Pydantic validation. |
| Message in Urdu/non-English | Normalize via LLM; if confidence < 0.7, escalate for manual review. |
| Customer submits same issue twice | AI identifies duplicate via `get_customer_history` and merges tickets. |
| WhatsApp message > 1600 chars | `format_response` splits into multiple sequential WhatsApp messages. |
| Gmail bounce/delivery failure | Monitor status webhook; move ticket to 'failed_delivery' queue. |
| Database connection timeout | Circuit breaker pattern in `queries.py` retries 3 times before DLQ. |
| Customer switches channel | Unified identity resolution links interactions via `customer_identifiers`. |
| Pricing question via web form | Acknowledge and immediately escalate to Sales team. |
| Multiple attachments in web form | Store in S3/Blob; include links in ticket metadata for human agents. |
| Concurrent messages | Lock conversation session for 30s to ensure sequential processing. |

## 4. Channel Response Patterns
- **Email:** Formal greeting, structured body, professional sign-off.
- **WhatsApp:** 1-2 emojis, conversational, under 300 characters.
- **Web Form:** Clear instructions, reference to "Settings" or "Account" sections.

## 5. Finalized Escalation Triggers
- **Keywords:** "refund", "cancel", "lawyer", "legal", "sue", "human", "agent", "representative".
- **Sentiment:** Score < 0.3 (detected via angry words or excessive capitalization).
- **Issue Category:** "Data Loss", "Security Issue", "Pricing Negotiation".
- **Interaction Failures:** > 2 failed searches in KB.

## 6. Performance Baseline Numbers
- **Retrieval Latency:** 200ms - 500ms (Prototype).
- **Sentiment Detection:** < 50ms.
- **Response Generation:** 1.2s - 2.5s (Target).
- **Success Rate:** ~80% documentation coverage in prototype tests.
