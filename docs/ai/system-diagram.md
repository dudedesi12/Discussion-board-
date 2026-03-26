# immi-pink AI System Architecture

## Overview

This diagram shows the end-to-end flow of content through the multi-agent
orchestration pipeline.

```mermaid
graph TD
    subgraph "Client Layer"
        U[👤 User / Browser]
    end

    subgraph "Flask Backend (Sync)"
        FB[Flask Request Handler\n/api/posts]
        SA[🛡️ Safety Agent\n< 200 ms sync]
    end

    subgraph "Message Queue"
        Q[(Redis\nCelery Broker)]
    end

    subgraph "Async Workers (Celery)"
        TA[🎯 Triage Agent\nCategorise + Urgency]
        RA[📚 Resource Agent\nOfficial Links / RAG]
        EA[💬 Engagement Agent\nNudge / Welcome]
        AA[📊 Analytics Agent\nAudit / Trends]
    end

    subgraph "Storage"
        DB[(PostgreSQL / SQLite\nPosts · Users · AIAgentLog)]
        VS[(Vector Store\nChromaDB / pgvector)]
    end

    subgraph "External APIs"
        LLM[LLM via LiteLLM\nGPT-4 · Llama-3]
        PII[PII Detection\nPresidio / regex]
    end

    U -->|POST /api/posts| FB
    FB -->|1 - sync veto| SA
    SA -->|PII check| PII
    SA -- "BLOCK ➜ 403" --> FB
    SA -- "ALLOW/REDACT" --> DB
    SA --> Q
    Q -->|task: run_triage_and_resource| TA
    TA --> RA
    RA -->|semantic search| VS
    RA -->|optional LLM summarisation| LLM
    TA --> EA
    TA --> AA
    TA --> DB
    RA --> DB
    EA --> DB
    AA --> DB
    FB -->|response| U
```

## Component Descriptions

| Component | Role | Latency Target |
|---|---|---|
| **Safety Agent** | PII redaction, toxicity/scam check, veto power | < 200 ms (sync) |
| **Triage Agent** | Intent classification, urgency scoring | async (Celery) |
| **Resource Agent** | Official-link retrieval, RAG, hallucination guard | async (Celery) |
| **Engagement Agent** | Nudge unanswered posts, welcome new users | async (scheduled) |
| **Analytics Agent** | Trend detection, RLHF sampling, admin reports | async (batch) |
| **Redis** | Celery task broker + result backend | — |
| **Vector Store** | Semantic search over official immigration docs | < 300 ms |
| **AIAgentLog table** | Immutable audit trail for all agent decisions | — |

## Conflict Resolution Policy

1. **Safety > All** – If the Safety Agent returns `BLOCK`, no downstream
   agent runs.
2. **Human > AI** – Admin overrides are logged and feed RLHF pipelines.
3. **Uncertainty → Escalation** – Any agent with confidence < 0.70 writes a
   `FLAG_FOR_HUMAN` log entry.

## Key Data-Flow Invariants

* Raw PII is **never** forwarded to any LLM API.
* Every agent decision is persisted to `AIAgentLog` before returning.
* If `AI_ENABLED=false`, the Flask handler skips the orchestration hook
  entirely and the platform operates in human-only moderation mode.
