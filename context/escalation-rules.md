# Escalation Rules

Escalate IMMEDIATELY to human when:
1. Customer mentions: "refund", "cancel", "lawyer", "legal", "sue"
2. Customer sentiment score < 0.3 (angry/frustrated tone)
3. Pricing negotiation requested
4. Cannot find answer after 2 knowledge base searches
5. Customer explicitly types: "human", "agent", "representative"
6. Bug reported as data loss or security issue
7. Enterprise customer with urgent SLA request

Escalation channel: publish to `fte.escalations` Kafka topic with full context.