"""
SQLAlchemy models for the immi-pink Discussion Board platform.

Includes core discussion models and AIAgentLog for observability.
"""
from __future__ import annotations

import datetime
from typing import Optional

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

_UTC = datetime.timezone.utc


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(_UTC)


# ── Core models ───────────────────────────────────────────────────────────────


class User(db.Model):
    __tablename__ = "users"

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False)
    email: str = db.Column(db.String(120), unique=True, nullable=False)
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=_utcnow
    )

    posts = db.relationship("Post", back_populates="author", lazy="dynamic")


class Post(db.Model):
    __tablename__ = "posts"

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(300), nullable=False)
    body: str = db.Column(db.Text, nullable=False)
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category: Optional[str] = db.Column(db.String(60))
    urgency_level: str = db.Column(db.String(20), default="normal")
    is_blocked: bool = db.Column(db.Boolean, default=False)
    ai_disclaimer_appended: bool = db.Column(db.Boolean, default=False)
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=_utcnow
    )
    updated_at: datetime.datetime = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    author = db.relationship("User", back_populates="posts")
    replies = db.relationship("Reply", back_populates="post", lazy="dynamic")


class Reply(db.Model):
    __tablename__ = "replies"

    id: int = db.Column(db.Integer, primary_key=True)
    body: str = db.Column(db.Text, nullable=False)
    post_id: int = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_blocked: bool = db.Column(db.Boolean, default=False)
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=_utcnow
    )

    post = db.relationship("Post", back_populates="replies")


class Report(db.Model):
    """Minimal stub for content reports (used by Safety Agent escalation path)."""

    __tablename__ = "reports"

    id: int = db.Column(db.Integer, primary_key=True)
    content_type: str = db.Column(db.String(30), nullable=False)  # "post" | "reply"
    content_id: int = db.Column(db.Integer, nullable=False)
    reason: str = db.Column(db.String(200))
    reported_by: Optional[int] = db.Column(db.Integer, db.ForeignKey("users.id"))
    resolved: bool = db.Column(db.Boolean, default=False)
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=_utcnow
    )


class Notification(db.Model):
    """Minimal stub for notifications (used by Engagement Agent)."""

    __tablename__ = "notifications"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message: str = db.Column(db.Text, nullable=False)
    is_read: bool = db.Column(db.Boolean, default=False)
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=_utcnow
    )


# ── AI Observability ──────────────────────────────────────────────────────────


class AIAgentLog(db.Model):
    """
    Records every decision made by an AI agent for observability,
    auditing, and RLHF feedback collection.

    All entries must be anonymized before long-term archival (GDPR/CCPA).
    """

    __tablename__ = "ai_agent_logs"

    id: int = db.Column(db.Integer, primary_key=True)

    # Which agent produced this entry (e.g., "safety", "triage", "resource")
    agent_name: str = db.Column(db.String(60), nullable=False, index=True)

    # Human-readable description of what the agent did
    action_taken: str = db.Column(db.String(200), nullable=False)

    # The content piece this log entry refers to
    content_id: Optional[int] = db.Column(db.Integer)
    content_type: Optional[str] = db.Column(db.String(30))  # "post" | "reply"

    # JSON blob with agent-specific reasoning, confidence scores, etc.
    # NOTE: Must NOT contain raw PII (data-minimization principle).
    agent_metadata: Optional[str] = db.Column(db.Text)

    # HITL fields
    human_reviewed: bool = db.Column(db.Boolean, default=False)
    reviewed_by: Optional[int] = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at: datetime.datetime = db.Column(
        db.DateTime, default=_utcnow, index=True
    )
