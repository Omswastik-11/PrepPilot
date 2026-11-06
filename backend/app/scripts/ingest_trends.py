"""
Weekly / On-Demand Company Interview Trend Ingestion Runner.

Automates the discovery and ingestion of company-specific OA and interview trends
into PrepPilot's pgvector QuestionBank with semantic deduplication.

Usage:
    python -m app.scripts.ingest_trends --company Google
    python -m app.scripts.ingest_trends --all
"""

import asyncio
import argparse
import logging
from typing import List, Dict

from app.database import async_session, engine
from app.services.knowledge_service import KnowledgeService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Curated, public interview and OA debrief sources across top tech companies
CURATED_SOURCES: List[Dict[str, str]] = [
    {
        "company": "Google",
        "domain": "Software Engineering",
        "topic": "Algorithms & Distributed Systems",
        "url": "https://raw.githubusercontent.com/jwasham/coding-interview-university/main/programming-language-resources.md",
    },
    {
        "company": "Stripe",
        "domain": "Software Engineering",
        "topic": "API Design & Concurrency",
        "url": "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/solutions/system_design/scaling_aws/README.md",
    },
    {
        "company": "Amazon",
        "domain": "Behavioral Competencies",
        "topic": "Leadership & Ownership",
        "url": "https://raw.githubusercontent.com/conordowney/amazon-leadership-principles/master/README.md",
    },
    {
        "company": "Meta",
        "domain": "Software Engineering",
        "topic": "Data Structures & Graph Traversal",
        "url": "https://raw.githubusercontent.com/kdn251/interviews/master/company/facebook/README.md",
    },
]


async def run_ingestion(target_company: str | None = None) -> None:
    """Run ingestion with semantic deduplication across curated company interview sources."""
    sources_to_ingest = [
        s for s in CURATED_SOURCES
        if target_company is None or s["company"].lower() == target_company.lower()
    ]

    if not sources_to_ingest:
        logger.warning(f"No curated sources found for company: {target_company}")
        return

    logger.info(f"Starting ingestion run for {len(sources_to_ingest)} source(s)...")

    total_added = 0
    async with async_session() as session:
        service = KnowledgeService(session)

        for src in sources_to_ingest:
            logger.info(f"Ingesting [{src['company']}] {src['topic']} from {src['url']}")
            try:
                questions = await service.ingest_url(
                    url=src["url"],
                    domain=src["domain"],
                    topic=src["topic"],
                    company=src["company"]
                )
                await session.commit()
                logger.info(f"Successfully processed [{src['company']}]: {len(questions)} question(s) saved/indexed.")
                total_added += len(questions)
            except Exception as e:
                logger.error(f"Failed to ingest from {src['url']}: {e}")
                await session.rollback()

    await engine.dispose()
    logger.info(f"Ingestion completed. Total questions processed/indexed: {total_added}")


def main():
    parser = argparse.ArgumentParser(description="Ingest company interview trends into PrepPilot pgvector")
    parser.add_argument("--company", type=str, help="Specific company to ingest (e.g. Google, Stripe)")
    parser.add_argument("--all", action="store_true", help="Ingest all curated company sources")
    args = parser.parse_args()

    company = args.company if not args.all else None
    asyncio.run(run_ingestion(target_company=company))


if __name__ == "__main__":
    main()
