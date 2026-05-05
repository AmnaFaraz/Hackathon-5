import asyncio
import logging
from production.database import queries

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KNOWLEDGE_ENTRIES = [
    {
        "title": "Password Reset",
        "content": "Go to login page → click \"Forgot Password\" → enter your email → check inbox for reset link → link expires in 30 minutes.",
        "category": "technical"
    },
    {
        "title": "API Access",
        "content": "API keys are found under Settings → Developer → API Keys. Each plan has rate limits: Starter=100 req/day, Pro=1000 req/day, Enterprise=unlimited.",
        "category": "technical"
    },
    {
        "title": "Team Members",
        "content": "Invite via Settings → Team → Invite Member. Enter email and select role: Viewer, Editor, or Admin.",
        "category": "general"
    },
    {
        "title": "Integrations",
        "content": "CloudFlow integrates with Slack, GitHub, Jira, and Zapier. Found under Settings → Integrations.",
        "category": "general"
    },
    {
        "title": "Export Data",
        "content": "Go to Settings → Data → Export. Supports CSV and JSON. Enterprise users get PDF export.",
        "category": "general"
    },
    {
        "title": "Mobile App",
        "content": "Available on iOS and Android. Download from App Store or Google Play. Same login credentials as web.",
        "category": "general"
    },
    {
        "title": "Billing",
        "content": "Billing is managed under Settings → Billing. Upgrade/downgrade anytime. Refunds handled by billing team only.",
        "category": "billing"
    },
    {
        "title": "Bug Reporting",
        "content": "Report bugs via Settings → Feedback → Report Bug. Include steps to reproduce.",
        "category": "technical"
    }
]

async def main():
    logger.info("Seeding knowledge base...")
    # The queries functions create their own pool and close it, so we can just call them.
    # However, for seeding, we might want to check if they already exist or just insert.
    
    count = 0
    for entry in KNOWLEDGE_ENTRIES:
        try:
            await queries.insert_knowledge_base_entry(
                title=entry["title"],
                content=entry["content"],
                category=entry["category"]
            )
            count += 1
        except Exception as e:
            logger.error(f"Failed to insert entry '{entry['title']}': {e}")
            
    print(f"Seeded {count} knowledge base entries")

if __name__ == "__main__":
    asyncio.run(main())
