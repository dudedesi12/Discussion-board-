# AI Pipeline Deployment Strategy

This document explains how to run the immi-pink AI orchestration pipeline
asynchronously without blocking Flask request/response cycles.

---

## Architecture Summary

```
Flask Web Process  ──────►  Redis (Celery broker)  ──────►  Celery Worker(s)
     │                                                            │
     │  Safety Agent (sync, < 200 ms)                            │
     │◄───────────────────────────────────────────────────────────┘
     │
     ▼
 Response returned to user (Triage + Resource continue in background)
```

The **Safety Agent** runs synchronously inside the Flask request so
content can be blocked or redacted before a response is returned.
All subsequent agents (Triage, Resource, Engagement, Analytics) run
as **Celery tasks** and do not block the HTTP response.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `development` | `development` / `production` / `testing` |
| `SECRET_KEY` | `dev-secret-…` | Flask secret key – **change in production** |
| `DATABASE_URL` | `sqlite:///discussion_board.db` | SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL for Celery broker + backend |
| `AI_ENABLED` | `true` | Set to `false` to disable all AI processing |
| `TOXICITY_THRESHOLD` | `0.70` | Block content above this toxicity score |
| `RESOURCE_CONFIDENCE_THRESHOLD` | `0.80` | Minimum confidence to surface a resource |
| `AGENT_CONFIDENCE_THRESHOLD` | `0.70` | Below this, flag for human review |
| `LITELLM_MODEL` | `gpt-4o-mini` | LiteLLM model identifier |
| `LITELLM_API_KEY` | `` | API key for the LLM provider |

Copy `.env.example` to `.env` and fill in values before starting:

```bash
cp .env.example .env
```

---

## Local Development

### Prerequisites

```bash
pip install -r requirements.txt
# Redis (choose one)
brew install redis && brew services start redis  # macOS
sudo apt-get install redis-server && sudo service redis start  # Debian/Ubuntu
docker run -d -p 6379:6379 redis:7-alpine  # Docker
```

### 1 – Database setup

```bash
export FLASK_APP=app.py
flask db upgrade          # creates all tables (runs Alembic migrations)
```

### 2 – Start the Flask web server

```bash
export FLASK_ENV=development
flask run                  # default: http://127.0.0.1:5000
```

### 3 – Start the Celery worker (separate terminal)

```bash
celery -A ai.tasks worker --loglevel=info --concurrency=4
```

### 4 – (Optional) Start Celery Beat for scheduled tasks

```bash
celery -A ai.tasks beat --loglevel=info
```

---

## Production Deployment

### Recommended stack

| Layer | Technology |
|---|---|
| Web server | Gunicorn (4+ workers) behind nginx |
| Database | PostgreSQL 15+ |
| Cache / broker | Redis 7+ (managed: ElastiCache, Upstash) |
| Celery workers | 2–4 dedicated worker dynos / containers |
| Container orchestration | Docker Compose (small) / Kubernetes (large) |

### Docker Compose (example)

```yaml
version: "3.9"
services:
  web:
    build: .
    command: gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/immi_pink
      - REDIS_URL=redis://redis:6379/0
      - AI_ENABLED=true
    depends_on: [db, redis]

  worker:
    build: .
    command: celery -A ai.tasks worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/immi_pink
      - REDIS_URL=redis://redis:6379/0
      - AI_ENABLED=true
    depends_on: [db, redis]

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: immi_pink
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  redis:
    image: redis:7-alpine
```

### Database migrations in production

```bash
# Run as part of deployment pipeline, before web/worker restart
flask db upgrade
```

---

## Graceful Degradation (AI_ENABLED=false)

Setting `AI_ENABLED=false` in the environment disables **all** AI
processing.  The platform continues to function with:

* Posts created and served normally.
* No Safety Agent, Triage, or Resource Agent runs.
* Human moderators review content manually.
* No Celery tasks dispatched.

This flag is checked at the top of `ai/orchestrator.py:process_post_created`.
No code changes are required; a simple environment variable restart is enough.

---

## Observability

* **AIAgentLog table** – every agent decision is recorded with:
  `agent_name`, `action_taken`, `content_id`, `content_type`,
  `agent_metadata` (JSON), `human_reviewed`, `created_at`.
* **Admin endpoint** – `GET /api/admin/ai-logs` returns the last 100
  log entries for dashboard display.
* **Celery monitoring** – run Flower for task queue visibility:
  ```bash
  pip install flower
  celery -A ai.tasks flower --port=5555
  ```
* **Structured logging** – all agents use Python's `logging` module;
  ship logs to your preferred aggregator (Datadog, CloudWatch, etc.).
