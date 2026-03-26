"""
Application configuration with feature flags for AI orchestration.
Set AI_ENABLED=false to disable all AI processing and degrade gracefully
to human-only moderation.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask / SQLAlchemy ────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///discussion_board.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Celery / Redis ────────────────────────────────────────────────────────
    CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # ── AI Feature Flags ─────────────────────────────────────────────────────
    # Set AI_ENABLED=false to disable all AI processing (graceful degradation).
    AI_ENABLED: bool = os.environ.get("AI_ENABLED", "true").lower() == "true"

    # Safety agent thresholds
    TOXICITY_THRESHOLD: float = float(os.environ.get("TOXICITY_THRESHOLD", "0.7"))
    # Minimum confidence to surface a resource recommendation
    RESOURCE_CONFIDENCE_THRESHOLD: float = float(
        os.environ.get("RESOURCE_CONFIDENCE_THRESHOLD", "0.8")
    )
    # Minimum agent confidence; below this, flag for human review
    AGENT_CONFIDENCE_THRESHOLD: float = float(
        os.environ.get("AGENT_CONFIDENCE_THRESHOLD", "0.7")
    )

    # ── LLM Backend (abstracted via LiteLLM) ─────────────────────────────────
    LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "gpt-4o-mini")
    LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", "")


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AI_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config() -> Config:
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)()
