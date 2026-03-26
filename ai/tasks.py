"""
Celery task definitions for async AI agent processing.

Workers are started separately from the Flask web process:

    celery -A ai.tasks worker --loglevel=info

If Celery/Redis is unavailable the orchestrator falls back to running
these tasks in-process (see ``ai/orchestrator.py``).
"""
from __future__ import annotations

import logging
from typing import Optional

from celery import Celery

from config import get_config

logger = logging.getLogger(__name__)


def make_celery() -> Celery:
    cfg = get_config()
    celery_app = Celery(
        "immi_pink",
        broker=cfg.CELERY_BROKER_URL,
        backend=cfg.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    return celery_app


celery = make_celery()


@celery.task(
    name="ai.tasks.run_triage_and_resource",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def run_triage_and_resource(
    self,
    post_id: int,
    title: str,
    body: str,
    author_id: Optional[int] = None,
) -> None:
    """
    Async Celery task: run Triage + Resource agents for a newly created post.

    Retries up to 3 times with a 30-second back-off on transient failures.
    """
    try:
        from ai.orchestrator import _run_triage_and_resource_sync

        _run_triage_and_resource_sync(
            post_id=post_id,
            title=title,
            body=body,
            author_id=author_id,
        )
    except Exception as exc:
        logger.exception(
            "run_triage_and_resource task failed for post %s, retrying.", post_id
        )
        raise self.retry(exc=exc)
