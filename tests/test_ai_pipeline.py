"""
Tests for the multi-agent orchestration pipeline.

Run with:  python -m pytest tests/ -v
"""
from __future__ import annotations

import pytest

from ai.interfaces import ContentCategory, ContentContext, UrgencyLevel
from ai.resource_agent import ResourceAgent
from ai.safety_agent import SafetyAgent
from ai.triage_agent import TriageAgent
from ai.interfaces import SafetyVerdictStatus


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def safety_agent():
    return SafetyAgent()


@pytest.fixture()
def triage_agent():
    return TriageAgent()


@pytest.fixture()
def resource_agent():
    return ResourceAgent(confidence_threshold=0.8)


def make_context(body: str, title: str = "", content_id: int = 1) -> ContentContext:
    return ContentContext(
        content_id=content_id,
        content_type="post",
        title=title,
        body=body,
    )


# ── Safety Agent tests ────────────────────────────────────────────────────────


class TestSafetyAgent:
    def test_clean_content_is_allowed(self, safety_agent):
        ctx = make_context("Hello, I have a question about my F-1 visa renewal.")
        verdict = safety_agent.process(ctx)
        assert verdict.status == SafetyVerdictStatus.ALLOW
        assert not verdict.pii_detected

    def test_ssn_is_redacted(self, safety_agent):
        ctx = make_context("My SSN is 123-45-6789 please help.")
        verdict = safety_agent.process(ctx)
        assert verdict.status == SafetyVerdictStatus.REDACT
        assert verdict.pii_detected
        assert "[SSN REDACTED]" in verdict.sanitised_body
        assert "123-45-6789" not in verdict.sanitised_body

    def test_a_number_is_redacted(self, safety_agent):
        ctx = make_context("My A-number is A123456789.")
        verdict = safety_agent.process(ctx)
        assert verdict.pii_detected
        assert "[A-NUMBER REDACTED]" in verdict.sanitised_body

    def test_email_is_redacted(self, safety_agent):
        ctx = make_context("Contact me at user@example.com for info.")
        verdict = safety_agent.process(ctx)
        assert verdict.pii_detected
        assert "[EMAIL REDACTED]" in verdict.sanitised_body

    def test_phone_is_redacted(self, safety_agent):
        ctx = make_context("Call me at 555-867-5309 anytime.")
        verdict = safety_agent.process(ctx)
        assert verdict.pii_detected
        assert "[PHONE REDACTED]" in verdict.sanitised_body

    def test_scam_content_is_flagged_for_human(self, safety_agent):
        ctx = make_context("Guaranteed visa approval – pay me directly $2000!")
        verdict = safety_agent.process(ctx)
        assert verdict.status == SafetyVerdictStatus.FLAG_FOR_HUMAN
        assert verdict.scam_detected

    def test_toxic_content_is_blocked(self, safety_agent):
        ctx = make_context("I hate you, go back to your country and die.")
        verdict = safety_agent.process(ctx)
        assert verdict.status == SafetyVerdictStatus.BLOCK
        assert verdict.toxicity_score >= 0.7

    def test_legal_trigger_requires_disclaimer(self, safety_agent):
        ctx = make_context("I filed form i-485 last month.")
        verdict = safety_agent.process(ctx)
        assert verdict.requires_disclaimer


# ── Triage Agent tests ────────────────────────────────────────────────────────


class TestTriageAgent:
    def test_visa_help_category(self, triage_agent):
        ctx = make_context("How do I renew my H-1B visa petition?")
        decision = triage_agent.process(ctx)
        assert decision.category == ContentCategory.VISA_HELP

    def test_scam_report_category(self, triage_agent):
        ctx = make_context("I was scammed by a fake immigration agent who took my money.")
        decision = triage_agent.process(ctx)
        assert decision.category == ContentCategory.SCAM_REPORT

    def test_housing_category(self, triage_agent):
        ctx = make_context("My landlord is trying to evict me from my apartment.")
        decision = triage_agent.process(ctx)
        assert decision.category == ContentCategory.HOUSING

    def test_urgency_high_on_deportation(self, triage_agent):
        ctx = make_context("I received a deportation order, what do I do?")
        decision = triage_agent.process(ctx)
        assert decision.urgency_level in (UrgencyLevel.HIGH, UrgencyLevel.CRITICAL)

    def test_urgency_normal_for_general_post(self, triage_agent):
        ctx = make_context("Where can I find good food near campus?")
        decision = triage_agent.process(ctx)
        assert decision.urgency_level == UrgencyLevel.NORMAL

    def test_tags_include_category(self, triage_agent):
        ctx = make_context("OPT application for STEM extension deadline?")
        decision = triage_agent.process(ctx)
        assert decision.category.value in decision.tags


# ── Resource Agent tests ──────────────────────────────────────────────────────


class TestResourceAgent:
    def test_visa_resources_returned(self, triage_agent, resource_agent):
        ctx = make_context("I need help with my visa petition.")
        routing = triage_agent.process(ctx)
        result = resource_agent.process(ctx, routing)
        assert len(result.items) > 0
        for item in result.items:
            assert item.confidence_score >= 0.8

    def test_all_resources_have_https_urls(self, triage_agent, resource_agent):
        ctx = make_context("I was scammed – lost money to a fake immigration agent.")
        routing = triage_agent.process(ctx)
        result = resource_agent.process(ctx, routing)
        for item in result.items:
            assert item.url.startswith("https://")

    def test_disclaimer_always_present(self, triage_agent, resource_agent):
        ctx = make_context("General question about living in the US.")
        routing = triage_agent.process(ctx)
        result = resource_agent.process(ctx, routing)
        assert "informational purposes only" in result.disclaimer.lower()

    def test_low_confidence_resources_filtered(self):
        agent = ResourceAgent(confidence_threshold=0.999)
        ctx = make_context("General question.")
        from ai.interfaces import RoutingDecision
        routing = RoutingDecision(category=ContentCategory.GENERAL)
        result = agent.process(ctx, routing)
        assert result.items == []


# ── Integration: interfaces import cleanly ────────────────────────────────────


def test_interfaces_import():
    from ai.interfaces import (
        ContentContext,
        ResourceList,
        ResourceListItem,
        RoutingDecision,
        SafetyVerdict,
        SafetyVerdictStatus,
        UrgencyLevel,
    )

    assert SafetyVerdictStatus.ALLOW.value == "ALLOW"
    assert UrgencyLevel.CRITICAL.value == "critical"


# ── Flask app integration ─────────────────────────────────────────────────────


@pytest.fixture()
def flask_app():
    from config import TestingConfig
    from app import create_app

    application = create_app(TestingConfig())
    with application.app_context():
        from models import db
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_post_endpoint(client):
    from models import db, User
    from flask import current_app

    with current_app.app_context():
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    response = client.post(
        "/api/posts",
        json={"title": "Test Post", "body": "Hello world", "author_id": user_id},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Test Post"


def test_create_post_missing_fields(client):
    response = client.post("/api/posts", json={"title": "No body"})
    assert response.status_code == 400
