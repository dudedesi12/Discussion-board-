"""
Safety & Compliance Agent – The Gatekeeper.

Runs **synchronously** in the Flask request path and must complete in
< 200 ms.  All detection is deterministic (regex + keyword lists) in
this initial implementation; no external API calls are made here.

Responsibilities
----------------
* PII redaction  – SSN, A-number, passport, phone, e-mail patterns
* Toxicity heuristic  – simple bad-word/threat keyword check (stub)
* Scam detection  – immigration-fraud keyword patterns
* Legal disclaimer injection  – flags content that discusses legal strategy

Output
------
``SafetyVerdict`` with status ALLOW | BLOCK | REDACT | FLAG_FOR_HUMAN.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from ai.interfaces import ContentContext, SafetyVerdict, SafetyVerdictStatus


# ── PII patterns ──────────────────────────────────────────────────────────────
# Each tuple: (label, compiled_regex, replacement_token)
_PII_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    # US Social Security Number: 123-45-6789 or 123456789
    (
        "SSN",
        re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
        "[SSN REDACTED]",
    ),
    # USCIS A-Number: A followed by 8–9 digits
    (
        "A_NUMBER",
        re.compile(r"\bA[-\s]?\d{8,9}\b", re.IGNORECASE),
        "[A-NUMBER REDACTED]",
    ),
    # Passport-like: letter + 7–9 alphanumeric chars (basic heuristic)
    (
        "PASSPORT",
        re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
        "[PASSPORT REDACTED]",
    ),
    # US/Canada phone numbers
    (
        "PHONE",
        re.compile(
            r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"
        ),
        "[PHONE REDACTED]",
    ),
    # E-mail addresses
    (
        "EMAIL",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        "[EMAIL REDACTED]",
    ),
]

# ── Scam detection keywords ───────────────────────────────────────────────────
_SCAM_KEYWORDS: List[str] = [
    "guaranteed visa",
    "guaranteed approval",
    "pay me directly",
    "wire transfer",
    "western union",
    "money gram",
    "green card guaranteed",
    "100% success rate",
    "no lawyer needed",
    "bypass immigration",
]

# ── Toxicity keywords (stub – replace with Perspective API in production) ─────
_TOXIC_KEYWORDS: List[str] = [
    "kill",
    "die",
    "hate you",
    "go back to",
    "deport yourself",
]

# ── Legal strategy triggers (require disclaimer injection) ────────────────────
_LEGAL_TRIGGERS: List[str] = [
    "i-485",
    "i-130",
    "i-140",
    "asylum application",
    "adjustment of status",
    "naturalization",
    "removal proceedings",
    "deportation order",
    "visa petition",
    "form i-",
]


def _contains_any(text: str, keywords: List[str]) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def _redact_pii(text: str) -> Tuple[str, bool]:
    """Return (redacted_text, pii_found)."""
    pii_found = False
    for _label, pattern, replacement in _PII_PATTERNS:
        new_text, n = pattern.subn(replacement, text)
        if n:
            pii_found = True
            text = new_text
    return text, pii_found


class SafetyAgent:
    """
    Stateless Safety & Compliance Agent.

    Usage::

        agent = SafetyAgent()
        verdict = agent.process(context)
    """

    def process(self, context: ContentContext) -> SafetyVerdict:
        full_text = " ".join(filter(None, [context.title, context.body]))

        # 1. PII redaction (always runs first)
        sanitised_body, pii_found = _redact_pii(context.body)
        sanitised_title = _redact_pii(context.title or "")[0] if context.title else None
        sanitised_full = " ".join(filter(None, [sanitised_title, sanitised_body]))

        # 2. Scam detection
        scam_detected = _contains_any(full_text, _SCAM_KEYWORDS)

        # 3. Toxicity heuristic (stub – lightweight keyword match)
        toxic_hit = _contains_any(full_text, _TOXIC_KEYWORDS)
        toxicity_score = 0.85 if toxic_hit else 0.0

        # 4. Legal disclaimer trigger
        requires_disclaimer = _contains_any(sanitised_full, _LEGAL_TRIGGERS)

        # 5. Determine verdict
        status: SafetyVerdictStatus
        reasoning_parts: List[str] = []

        if toxicity_score >= 0.7:
            status = SafetyVerdictStatus.BLOCK
            reasoning_parts.append(
                f"Toxicity score {toxicity_score:.2f} exceeds threshold 0.70."
            )
        elif scam_detected:
            status = SafetyVerdictStatus.FLAG_FOR_HUMAN
            reasoning_parts.append("Scam-related language detected.")
        elif pii_found:
            status = SafetyVerdictStatus.REDACT
            reasoning_parts.append("PII detected and redacted from body.")
        else:
            status = SafetyVerdictStatus.ALLOW

        if requires_disclaimer:
            reasoning_parts.append(
                "Legal strategy keywords detected; disclaimer injection required."
            )

        return SafetyVerdict(
            status=status,
            sanitised_body=sanitised_body,
            pii_detected=pii_found,
            toxicity_score=toxicity_score,
            scam_detected=scam_detected,
            requires_disclaimer=requires_disclaimer,
            confidence=1.0,  # deterministic rules → full confidence
            reasoning="; ".join(reasoning_parts) if reasoning_parts else "No issues found.",
        )
