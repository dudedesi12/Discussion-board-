"""
Shared Pydantic v2 models (input/output schemas) for all AI agents.

These dataclasses form the contract between the Flask backend, the
Orchestrator, and each specialized agent.  No raw PII may be stored
inside these objects beyond the sanitised ``body`` field.
"""
from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────────────


class SafetyVerdictStatus(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REDACT = "REDACT"
    FLAG_FOR_HUMAN = "FLAG_FOR_HUMAN"


class ContentCategory(str, Enum):
    VISA_HELP = "VisaHelp"
    HOUSING = "Housing"
    SCAM_REPORT = "ScamReport"
    ACADEMIC = "Academic"
    GENERAL = "General"


class UrgencyLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ── Input schema ──────────────────────────────────────────────────────────────


class ContentContext(BaseModel):
    """
    The canonical input payload passed through the agent pipeline.

    ``body`` should already be PII-redacted before being handed to any
    LLM-backed agent (data-minimisation principle).
    """

    content_id: int
    content_type: str = Field(
        description="One of: 'post', 'reply', 'message'",
        pattern="^(post|reply|message)$",
    )
    title: Optional[str] = None
    # body may be mutated (redacted) by the Safety Agent in-place before
    # being forwarded downstream.
    body: str
    author_id: Optional[int] = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    extra: Dict[str, Any] = Field(default_factory=dict)


# ── Safety Agent output ───────────────────────────────────────────────────────


class SafetyVerdict(BaseModel):
    """Output produced by the Safety & Compliance Agent."""

    status: SafetyVerdictStatus
    # Body after PII redaction (unchanged if ALLOW, redacted if REDACT).
    sanitised_body: str
    pii_detected: bool = False
    toxicity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    scam_detected: bool = False
    requires_disclaimer: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = ""


# ── Triage Agent output ───────────────────────────────────────────────────────


class RoutingDecision(BaseModel):
    """Output produced by the Triage & Routing Agent."""

    tags: List[str] = Field(default_factory=list)
    category: ContentCategory = ContentCategory.GENERAL
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    # IDs of verified human agents that should be notified.
    assigned_agent_ids: List[int] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = ""


# ── Resource Agent output ─────────────────────────────────────────────────────


class ResourceListItem(BaseModel):
    """A single official resource recommendation."""

    title: str
    url: str
    source: str  # e.g. "USCIS", "State Dept", "IRCC"
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class ResourceList(BaseModel):
    """Output produced by the Resource & RAG Agent."""

    items: List[ResourceListItem] = Field(default_factory=list)
    disclaimer: str = (
        "These resources are for informational purposes only and do not "
        "constitute legal advice.  Consult a qualified immigration attorney "
        "or accredited representative for guidance specific to your situation."
    )
