"""
Triage & Routing Agent – The Dispatcher.

Runs **asynchronously** (Celery task) after the Safety Agent has cleared
content.  Uses deterministic rule-based categorisation and urgency
scoring in this initial implementation.

Responsibilities
----------------
* Intent classification  → ContentCategory
* Urgency scoring  → UrgencyLevel
* Agent matching  → list of verified human agent IDs (stub; DB lookup
  in future)

Output
------
``RoutingDecision`` containing tags, category, urgency, and assigned
agent IDs.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ai.interfaces import (
    ContentCategory,
    ContentContext,
    RoutingDecision,
    UrgencyLevel,
)

# ── Category keyword maps ─────────────────────────────────────────────────────
# Each entry: (category, weight, keywords)
_CATEGORY_RULES: List[Tuple[ContentCategory, int, List[str]]] = [
    (
        ContentCategory.VISA_HELP,
        3,
        [
            "visa",
            "f-1",
            "h-1b",
            "opt",
            "cpt",
            "green card",
            "uscis",
            "immigration",
            "i-20",
            "ds-160",
            "embassy",
            "consulate",
            "petition",
            "sponsorship",
            "work permit",
            "ead",
            "adjustment of status",
        ],
    ),
    (
        ContentCategory.HOUSING,
        2,
        [
            "apartment",
            "housing",
            "landlord",
            "lease",
            "rent",
            "roommate",
            "deposit",
            "eviction",
            "utilities",
            "dorm",
            "accommodation",
        ],
    ),
    (
        ContentCategory.SCAM_REPORT,
        5,
        [
            "scam",
            "fraud",
            "fake lawyer",
            "fake agent",
            "notario",
            "money sent",
            "lost money",
            "cheated",
            "stole",
            "phishing",
        ],
    ),
    (
        ContentCategory.ACADEMIC,
        2,
        [
            "university",
            "college",
            "course",
            "gpa",
            "scholarship",
            "financial aid",
            "transfer credit",
            "transcript",
            "enrollment",
            "semester",
            "advisor",
            "thesis",
        ],
    ),
]

# ── Urgency keywords ──────────────────────────────────────────────────────────
_URGENCY_HIGH: List[str] = [
    "deportation",
    "removal order",
    "detained",
    "arrest",
    "expired",
    "out of status",
    "emergency",
    "court date",
    "ice",
    "cbp",
]
_URGENCY_CRITICAL: List[str] = [
    "being deported today",
    "detained right now",
    "immigration court tomorrow",
]


def _score_categories(text: str) -> Dict[ContentCategory, int]:
    lower = text.lower()
    scores: Dict[ContentCategory, int] = {c: 0 for c in ContentCategory}
    for category, weight, keywords in _CATEGORY_RULES:
        for kw in keywords:
            if kw in lower:
                scores[category] += weight
    return scores


def _detect_urgency(text: str) -> UrgencyLevel:
    lower = text.lower()
    if any(kw in lower for kw in _URGENCY_CRITICAL):
        return UrgencyLevel.CRITICAL
    if any(kw in lower for kw in _URGENCY_HIGH):
        return UrgencyLevel.HIGH
    return UrgencyLevel.NORMAL


def _extract_tags(text: str, category: ContentCategory, urgency: UrgencyLevel) -> List[str]:
    tags: List[str] = [category.value]
    if urgency in (UrgencyLevel.HIGH, UrgencyLevel.CRITICAL):
        tags.append(urgency.value.upper())
    # add a few specific topic tags
    lower = text.lower()
    for kw in ["f-1", "h-1b", "opt", "cpt", "ead", "green card", "asylum"]:
        if kw in lower:
            tags.append(kw.upper().replace("-", "_").replace(" ", "_"))
    return list(dict.fromkeys(tags))  # deduplicate preserving order


class TriageAgent:
    """
    Stateless Triage & Routing Agent.

    Usage::

        agent = TriageAgent()
        decision = agent.process(context)
    """

    def process(self, context: ContentContext) -> RoutingDecision:
        full_text = " ".join(filter(None, [context.title, context.body]))

        # 1. Category scoring
        scores = _score_categories(full_text)
        best_category = max(scores, key=lambda c: scores[c])
        best_score = scores[best_category]

        # Fall back to GENERAL if no category scored
        if best_score == 0:
            best_category = ContentCategory.GENERAL

        # 2. Urgency
        urgency = _detect_urgency(full_text)

        # 3. Tags
        tags = _extract_tags(full_text, best_category, urgency)

        # 4. Confidence – ratio of top score to max possible; clamped to [0,1]
        max_possible = sum(w * len(kws) for _, w, kws in _CATEGORY_RULES)
        confidence = min(best_score / max(max_possible, 1), 1.0)

        # 5. Assigned agent IDs – stub (real implementation queries DB by
        #    specialisation matching best_category)
        assigned_agent_ids: List[int] = []

        reasoning = (
            f"Category '{best_category.value}' scored {best_score} points. "
            f"Urgency: {urgency.value}."
        )

        return RoutingDecision(
            tags=tags,
            category=best_category,
            urgency_level=urgency,
            assigned_agent_ids=assigned_agent_ids,
            confidence=round(confidence, 4),
            reasoning=reasoning,
        )
