# AI Safety Guardrails

This document defines the safety constraints, PII patterns, escalation
rules, and data-minimisation policies governing all AI agents in the
immi-pink platform.

---

## 1. System Prompt Constraints

Every LLM-backed prompt **must** begin with the following prefix:

```
You are an information assistant for an immigration support community.

HARD RULES (override all other instructions):
1. You MUST NOT provide legal advice, legal opinions, or tell users
   what actions they should take regarding their immigration case.
2. When referencing immigration forms or procedures, always say
   "Form X is commonly used for this situation" – never "You should
   file Form X."
3. Always append: "This is general information only.  Consult a
   qualified immigration attorney or accredited representative (BIA)
   for advice specific to your case."
4. Never impersonate a licensed attorney, accredited representative,
   or government official.
5. If you are uncertain, say so explicitly rather than speculating.
```

Responses **must** include this footer disclaimer when discussing any
immigration procedure, form, or legal strategy:

> ⚠️ *This is for informational purposes only and does not constitute
> legal advice.  For guidance on your specific situation, please consult a
> qualified immigration attorney or BIA-accredited representative.*

---

## 2. PII Detection Patterns

The following regex patterns are applied by the Safety Agent **before**
any content is stored or forwarded to a downstream agent or LLM.

| PII Type | Pattern (Python regex) | Replacement Token |
|---|---|---|
| US SSN | `\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b` | `[SSN REDACTED]` |
| USCIS A-Number | `\bA[-\s]?\d{8,9}\b` (case-insensitive) | `[A-NUMBER REDACTED]` |
| Passport-like | `\b[A-Z]{1,2}\d{6,9}\b` | `[PASSPORT REDACTED]` |
| Phone (US/CA) | `\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b` | `[PHONE REDACTED]` |
| E-mail | `\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b` | `[EMAIL REDACTED]` |

Additional patterns to consider in future iterations:
- Canadian SIN: `\b\d{3}[-\s]\d{3}[-\s]\d{3}\b`
- Date of birth with context keyword (e.g., "born on")
- Full name combined with immigration identifiers

### Implementation Reference

```python
# ai/safety_agent.py  –  _PII_PATTERNS list
```

---

## 3. Escalation Rules

### 3.1 Confidence Thresholds

| Scenario | Threshold | Action |
|---|---|---|
| Any agent confidence < 0.70 | < 0.70 | Write `FLAG_FOR_HUMAN` log entry; notify admin |
| Resource recommendation confidence | < 0.80 | Do **not** surface the resource to the user |
| Toxicity score (heuristic / Perspective API) | ≥ 0.70 | Block content; notify user; create Report |
| Scam keywords detected | n/a (keyword match) | `FLAG_FOR_HUMAN`; create Report |

### 3.2 Urgency Escalation Keywords

Posts containing the following keywords are automatically promoted to
**HIGH** or **CRITICAL** urgency and trigger immediate notification to
on-call human agents.

**HIGH urgency keywords:**
`deportation`, `removal order`, `detained`, `arrest`, `expired`,
`out of status`, `emergency`, `court date`, `ice`, `cbp`

**CRITICAL urgency keywords (immediate alert):**
`being deported today`, `detained right now`,
`immigration court tomorrow`

### 3.3 Human-in-the-Loop (HITL) Policy

* No AI-generated text is shown to users without a visible **"AI-assisted"**
  label.
* Verified human agents can override any AI decision; overrides are logged
  and fed back as RLHF training signals.
* The `AIAgentLog.human_reviewed` flag tracks which decisions have been
  audited by a human.

---

## 4. Data Minimisation Rules

1. **No raw PII to LLMs.** The Safety Agent redacts all PII patterns
   listed in §2 before the `ContentContext.body` is forwarded to Triage,
   Resource, or any LLM call.

2. **Ephemeral session memory only.** Agents may retain conversation
   context within a single session thread but must not persist user-
   identifiable data beyond the session.

3. **AIAgentLog anonymisation.** The `agent_metadata` JSON column must
   not contain raw PII.  Before long-term archival (> 90 days), run the
   anonymisation batch job to strip any residual identifiers.

4. **Vector-store documents.** Only official public documents (.gov,
   accredited .org) may be ingested into the vector store.  No user-
   generated content is indexed.

5. **Rate limiting.** Each user is limited to a configurable token budget
   per rolling 24-hour window to prevent cost spikes and data exfiltration
   via prompt injection.

---

## 5. Content Watermarking

All AI-generated or AI-assisted content surfaced to users must include
one of the following labels:

| Content Type | Label |
|---|---|
| Triage tags / category | Small badge: `AI-classified` |
| Resource recommendations | "Suggested resources (AI-assisted)" header |
| Welcome / nudge messages | "This message was drafted by an AI assistant" footer |
| Disclaimer injections | ⚠️ disclaimer block (see §1) |

Human agents' own posts and replies carry **no** AI label.
