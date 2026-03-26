"""
immi-pink Discussion Board – Flask application factory.

AI processing is gated behind the AI_ENABLED feature flag in config.py;
disabling it allows the platform to run in human-only moderation mode.
"""
from __future__ import annotations

from flask import Flask, jsonify, request
from flask_migrate import Migrate

from config import get_config
from models import AIAgentLog, Post, Reply, User, db


def create_app(config=None) -> Flask:
    app = Flask(__name__)
    cfg = config or get_config()
    app.config.from_object(cfg)

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    Migrate(app, db)

    # ── Blueprints / Routes ───────────────────────────────────────────────────
    _register_routes(app)

    return app


def _register_routes(app: Flask) -> None:
    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # ── Posts ─────────────────────────────────────────────────────────────────

    @app.get("/api/posts")
    def list_posts():
        posts = Post.query.filter_by(is_blocked=False).order_by(
            Post.created_at.desc()
        ).all()
        return jsonify(
            [
                {
                    "id": p.id,
                    "title": p.title,
                    "category": p.category,
                    "urgency_level": p.urgency_level,
                    "created_at": p.created_at.isoformat(),
                }
                for p in posts
            ]
        )

    @app.post("/api/posts")
    def create_post():
        data = request.get_json(force=True)
        title = (data.get("title") or "").strip()
        body = (data.get("body") or "").strip()
        author_id = data.get("author_id")

        if not title or not body or not author_id:
            return jsonify({"error": "title, body, and author_id are required"}), 400

        post = Post(title=title, body=body, author_id=author_id)
        db.session.add(post)
        db.session.flush()  # obtain post.id before commit

        # ── AI Orchestration hook ─────────────────────────────────────────────
        if app.config.get("AI_ENABLED", False):
            try:
                from ai.orchestrator import process_post_created
                process_post_created(post_id=post.id, title=title, body=body)
            except Exception:
                # AI pipeline failures must never break core endpoints.
                app.logger.exception(
                    "AI orchestration failed for post %s – continuing without AI",
                    post.id,
                )

        db.session.commit()
        return jsonify({"id": post.id, "title": post.title}), 201

    @app.get("/api/posts/<int:post_id>")
    def get_post(post_id: int):
        post = Post.query.get_or_404(post_id)
        if post.is_blocked:
            return jsonify({"error": "This post has been removed."}), 410
        return jsonify(
            {
                "id": post.id,
                "title": post.title,
                "body": post.body,
                "category": post.category,
                "urgency_level": post.urgency_level,
                "ai_disclaimer_appended": post.ai_disclaimer_appended,
                "created_at": post.created_at.isoformat(),
            }
        )

    # ── AI Agent Logs (read-only for admins) ──────────────────────────────────

    @app.get("/api/admin/ai-logs")
    def list_ai_logs():
        logs = (
            AIAgentLog.query.order_by(AIAgentLog.created_at.desc()).limit(100).all()
        )
        return jsonify(
            [
                {
                    "id": lg.id,
                    "agent_name": lg.agent_name,
                    "action_taken": lg.action_taken,
                    "content_type": lg.content_type,
                    "content_id": lg.content_id,
                    "human_reviewed": lg.human_reviewed,
                    "created_at": lg.created_at.isoformat(),
                    "agent_metadata": lg.agent_metadata,
                }
                for lg in logs
            ]
        )


app = create_app()

if __name__ == "__main__":
    import os
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(debug=debug)
