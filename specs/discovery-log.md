# Discovery Log — Customer Success AI FTE

## Channel Patterns
| Channel | Characteristics | Tone Requirement |
|---------|-----------------|------------------|
| **Email** | Long-form, descriptive, structured. Used for complex or serious issues. | Formal greeting, structured body, professional sign-off. |
| **WhatsApp** | Brief, conversational, often urgent. Emojis are common. | Short, direct, 1-2 emojis acceptable. |
| **Web Form** | Purpose-driven, semi-structured. Used for specific account actions. | Semi-formal, clear, actionable. |

## Top 10 Issue Categories
1. **Password Reset** (Technical)
2. **App Availability/Stability** (Technical)
3. **Team Management/Invitations** (General)
4. **API Access & Rate Limits** (Technical)
5. **Billing & Refunds** (Billing)
6. **Pricing Inquiries** (Billing)
7. **Mobile App Installation** (General)
8. **Custom Integrations** (General)
9. **Data Loss/Security Reports** (Urgent/Technical)
10. **Legal/Compliance Inquiries** (Legal)

## Discovered Escalation Triggers
- **Financial/Legal Keywords:** "refund", "cancel", "lawyer", "legal", "sue".
- **Sentiment Threshold:** Any message conveying high frustration or anger (Score < 0.3).
- **Specific Requests:** Express requests for "human", "agent", or "representative".
- **Security/Data Integrity:** Mentions of "data loss" or "security issue".
- **High-Value/Enterprise:** Pricing negotiations or Enterprise SLA requests.

## Performance Baseline Targets
- **Initial Response Time:** < 5 seconds for AI responses.
- **Accuracy:** > 85% correct retrieval from product docs.
- **Escalation Accuracy:** 100% for defined triggers.
- **Sentiment Detection:** > 90% alignment with manual labels.
