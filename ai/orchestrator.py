"""
Orchestrator – coordinates the multi-agent pipeline for immi-pink.

Pipeline
--------
1. **Safety Agent** (sync, in-request)  →  veto power; blocks pipeline
   on BLOCK verdict.
2. **Triage Agent** (async Celery task)  →  categorises and scores urgency.
3. **Resource Agent** (async Celery task)  →  attaches official resource links.

Every agent decision is persisted to ``AIAgentLog`` for observability
and HITL (Human-In-The-Loop) review.

Fail-safe design
----------------
* Any exception inside the orchestrator is caught and logged; it must
  never propagate to the Flask request handler and break core endpoints.
* The entire pipeline can be disabled via ``AI_ENABLED=false`` in the
  environment / config.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from ai.interfaces import (
    ContentContext,
    SafetyVerdictStatus,
    UrgencyLevel,
)
from ai.resource_agent import ResourceAgent
from ai.safety_agent import SafetyAgent
from ai.triage_agent import TriageAgent

logger = logging.getLogger(__name__)

# Instantiate stateless agents once (safe for multi-thread use)
_safety_agent = SafetyAgent()
_triage_agent = TriageAgent()
_resource_agent = ResourceAgent()


# ── Database helpers ──────────────────────────────────────────────────────────


def _log_agent_decision(
    agent_name: str,
    action_taken: str,
    content_id: int,
    content_type: str,
    metadata: Optional[dict] = None,
) -> None:
    """Persist an AIAgentLog entry.  Silently swallows errors to remain safe."""
    try:
        from app import db  # deferred import – avoids circular dep with app factory
        from models import AIAgentLog

        log = AIAgentLog(
            agent_name=agent_name,
            action_taken=action_taken,
            content_id=content_id,
            content_type=content_type,
            agent_metadata=json.dumps(metadata or {}),
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        logger.exception("Failed to write AIAgentLog for agent=%s", agent_name)


def _update_post(
    post_id: int,
    *,
    is_blocked: bool = False,
    category: Optional[str] = None,
    urgency_level: Optional[str] = None,
    ai_disclaimer_appended: bool = False,
    sanitised_body: Optional[str] = None,
) -> None:
    """Apply agent decisions back to the Post record."""
    try:
        from app import db  # deferred import – avoids circular dep with app factory
        from models import Post

        post = db.session.get(Post, post_id)
        if post is None:
            logger.warning("Post %s not found; skipping update.", post_id)
            return

        if is_blocked:
            post.is_blocked = True
        if category:
            post.category = category
        if urgency_level:
            post.urgency_level = urgency_level
        if ai_disclaimer_appended:
            post.ai_disclaimer_appended = True
        if sanitised_body is not None:
            post.body = sanitised_body

        db.session.commit()
    except Exception:
        logger.exception("Failed to update Post %s after AI processing.", post_id)


# ── Sync entry-point (called directly from Flask request context) ─────────────


def process_post_created(
    post_id: int,
    title: str,
    body: str,
    author_id: Optional[int] = None,
) -> None:
    """
    Entry-point invoked from the ``POST /api/posts`` handler.

    Step 1 (Safety) runs synchronously.
    Steps 2-3 (Triage + Resource) are dispatched as async Celery tasks.
    """
    from config import get_config

    cfg = get_config()
    if not cfg.AI_ENABLED:
        logger.debug("AI_ENABLED=false; skipping orchestration for post %s.", post_id)
        return

    context = ContentContext(
        content_id=post_id,
        content_type="post",
        title=title,
        body=body,
        author_id=author_id,
    )

    # ── Step 1: Safety (synchronous) ─────────────────────────────────────────
    try:
        verdict = _safety_agent.process(context)
    except Exception:
        logger.exception("Safety agent raised an exception for post %s.", post_id)
        return  # fail-safe: do not block the request, skip AI processing

    _log_agent_decision(
        agent_name="safety",
        action_taken=verdict.status.value,
        content_id=post_id,
        content_type="post",
        metadata={
            "pii_detected": verdict.pii_detected,
            "toxicity_score": verdict.toxicity_score,
            "scam_detected": verdict.scam_detected,
            "requires_disclaimer": verdict.requires_disclaimer,
            "confidence": verdict.confidence,
            "reasoning": verdict.reasoning,
        },
    )

    if verdict.status == SafetyVerdictStatus.BLOCK:
        _update_post(post_id, is_blocked=True)
        logger.info("Post %s BLOCKED by Safety Agent: %s", post_id, verdict.reasoning)
        return  # Safety has veto power; stop the pipeline.

    # Apply redaction / disclaimer flag back to DB
    _update_post(
        post_id,
        sanitised_body=verdict.sanitised_body if verdict.pii_detected else None,
        ai_disclaimer_appended=verdict.requires_disclaimer,
    )

    # ── Steps 2-3: Triage + Resource (async) ─────────────────────────────────
    try:
        from ai.tasks import run_triage_and_resource

        run_triage_and_resource.delay(
            post_id=post_id,
            title=title,
            body=verdict.sanitised_body,  # use redacted body
            author_id=author_id,
        )
    except Exception:
        # If Celery/Redis is unavailable, fall back to in-process execution.
        logger.warning(
            "Celery unavailable; running triage + resource synchronously for post %s.",
            post_id,
        )
        _run_triage_and_resource_sync(
            post_id=post_id,
            title=title,
            body=verdict.sanitised_body,
            author_id=author_id,
        )


# ── Async Celery task body (also callable synchronously as fallback) ──────────


def _run_triage_and_resource_sync(
    post_id: int,
    title: str,
    body: str,
    author_id: Optional[int] = None,
) -> None:
    """Shared implementation used by both the Celery task and the sync fallback."""
    context = ContentContext(
        content_id=post_id,
        content_type="post",
        title=title,
        body=body,
        author_id=author_id,
    )

    # ── Step 2: Triage ────────────────────────────────────────────────────────
    try:
        routing = _triage_agent.process(context)
    except Exception:
        logger.exception("Triage agent raised an exception for post %s.", post_id)
        return

    _log_agent_decision(
        agent_name="triage",
        action_taken=f"categorised:{routing.category.value}",
        content_id=post_id,
        content_type="post",
        metadata={
            "tags": routing.tags,
            "category": routing.category.value,
            "urgency_level": routing.urgency_level.value,
            "confidence": routing.confidence,
            "reasoning": routing.reasoning,
        },
    )

    _update_post(
        post_id,
        category=routing.category.value,
        urgency_level=routing.urgency_level.value,
    )

    # ── Step 3: Resource ──────────────────────────────────────────────────────
    try:
        from config import get_config

        cfg = get_config()
        resource_agent = ResourceAgent(
            confidence_threshold=cfg.RESOURCE_CONFIDENCE_THRESHOLD
        )
        resource_list = resource_agent.process(context, routing)
    except Exception:
        logger.exception("Resource agent raised an exception for post %s.", post_id)
        return

    _log_agent_decision(
        agent_name="resource",
        action_taken=f"attached:{len(resource_list.items)}_resources",
        content_id=post_id,
        content_type="post",
        metadata={
            "resource_count": len(resource_list.items),
            "resources": [
                {"title": r.title, "url": r.url, "confidence": r.confidence_score}
                for r in resource_list.items
            ],
        },
    )

    if routing.urgency_level in (UrgencyLevel.HIGH, UrgencyLevel.CRITICAL):
        logger.warning(
            "Post %s marked %s urgency – human review required.",
            post_id,
            routing.urgency_level.value,
        )
