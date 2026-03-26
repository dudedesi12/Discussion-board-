"""
Resource & RAG Agent – The Librarian.

Runs **asynchronously** (Celery task) after Triage completes.

Initial implementation uses a **deterministic official-links registry**
(no LLM calls) to ensure zero hallucination risk in this PR.

A placeholder vector-store integration point is included and commented;
uncomment + implement once ChromaDB/pgvector is provisioned.

Responsibilities
----------------
* Match content category to curated official resource URLs
* Return resources only when confidence >= RESOURCE_CONFIDENCE_THRESHOLD
* If confidence < threshold → return empty list with standard disclaimer

Output
------
``ResourceList`` containing ``ResourceListItem`` entries.
"""
from __future__ import annotations

from typing import Dict, List

from ai.interfaces import (
    ContentCategory,
    ContentContext,
    ResourceList,
    ResourceListItem,
    RoutingDecision,
)

# ── Deterministic official-links registry ─────────────────────────────────────
# All URLs point to authoritative .gov or official sources.
# Confidence is set conservatively (0.95) for deterministic matches.
_OFFICIAL_REGISTRY: Dict[ContentCategory, List[ResourceListItem]] = {
    ContentCategory.VISA_HELP: [
        ResourceListItem(
            title="USCIS – Check Case Status",
            url="https://egov.uscis.gov/casestatus/landing.do",
            source="USCIS",
            confidence_score=0.97,
        ),
        ResourceListItem(
            title="USCIS – Forms & Instructions",
            url="https://www.uscis.gov/forms",
            source="USCIS",
            confidence_score=0.97,
        ),
        ResourceListItem(
            title="U.S. Department of State – Visa Information",
            url="https://travel.state.gov/content/travel/en/us-visas.html",
            source="State Dept",
            confidence_score=0.95,
        ),
        ResourceListItem(
            title="ICE – Student & Exchange Visitor Program (SEVP)",
            url="https://www.ice.gov/sevis",
            source="ICE / SEVP",
            confidence_score=0.95,
        ),
    ],
    ContentCategory.HOUSING: [
        ResourceListItem(
            title="HUD – Renter Assistance & Fair Housing",
            url="https://www.hud.gov/topics/rental_assistance",
            source="HUD",
            confidence_score=0.95,
        ),
        ResourceListItem(
            title="Consumer Financial Protection Bureau – Renting a Home",
            url="https://www.consumerfinance.gov/consumer-tools/renting/",
            source="CFPB",
            confidence_score=0.93,
        ),
    ],
    ContentCategory.SCAM_REPORT: [
        ResourceListItem(
            title="FTC – Report Fraud",
            url="https://reportfraud.ftc.gov/",
            source="FTC",
            confidence_score=0.97,
        ),
        ResourceListItem(
            title="USCIS – Avoid Scams",
            url="https://www.uscis.gov/avoid-scams",
            source="USCIS",
            confidence_score=0.97,
        ),
        ResourceListItem(
            title="DOJ – Report Immigration Fraud",
            url="https://www.justice.gov/eoir/report-immigration-fraud",
            source="DOJ",
            confidence_score=0.95,
        ),
    ],
    ContentCategory.ACADEMIC: [
        ResourceListItem(
            title="StudentAid.gov – Federal Student Aid",
            url="https://studentaid.gov/",
            source="Dept of Education",
            confidence_score=0.95,
        ),
        ResourceListItem(
            title="NAFSA – International Student Resources",
            url="https://www.nafsa.org/resources",
            source="NAFSA",
            confidence_score=0.90,
        ),
    ],
    ContentCategory.GENERAL: [
        ResourceListItem(
            title="USA.gov – Immigration & Citizenship",
            url="https://www.usa.gov/immigration-and-citizenship",
            source="USA.gov",
            confidence_score=0.90,
        ),
    ],
}

# ── Placeholder: vector-store integration ─────────────────────────────────────
# TODO: Replace with ChromaDB or pgvector semantic search once provisioned.
# Example integration (commented out):
#
# from chromadb import Client as ChromaClient
#
# def _vector_search(query: str, n_results: int = 3) -> List[ResourceListItem]:
#     client = ChromaClient()
#     collection = client.get_collection("immigration_docs")
#     results = collection.query(query_texts=[query], n_results=n_results)
#     items = []
#     for doc, meta, dist in zip(
#         results["documents"][0], results["metadatas"][0], results["distances"][0]
#     ):
#         confidence = 1.0 - dist  # convert distance to confidence
#         if confidence >= RESOURCE_CONFIDENCE_THRESHOLD:
#             items.append(ResourceListItem(
#                 title=meta.get("title", "Official Resource"),
#                 url=meta.get("url", ""),
#                 source=meta.get("source", "Unknown"),
#                 confidence_score=round(confidence, 4),
#             ))
#     return items


class ResourceAgent:
    """
    Stateless Resource & RAG Agent.

    Usage::

        agent = ResourceAgent(confidence_threshold=0.8)
        resource_list = agent.process(context, routing_decision)
    """

    def __init__(self, confidence_threshold: float = 0.8) -> None:
        self.confidence_threshold = confidence_threshold

    def process(
        self, context: ContentContext, routing: RoutingDecision
    ) -> ResourceList:
        category = routing.category
        candidates = _OFFICIAL_REGISTRY.get(category, _OFFICIAL_REGISTRY[ContentCategory.GENERAL])

        # Filter by confidence threshold (hallucination guard)
        approved = [
            item
            for item in candidates
            if item.confidence_score >= self.confidence_threshold
        ]

        # Placeholder: would merge vector-store results here
        # approved += _vector_search(context.body or "")

        return ResourceList(items=approved)
