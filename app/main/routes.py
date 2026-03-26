from flask import render_template, jsonify, request
from app.main import main
from app.models import Post, User


@main.route('/')
def index():
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(6).all()
    agents = User.query.filter_by(role='agent', is_active=True).limit(6).all()
    user_count = User.query.count()
    post_count = Post.query.count()
    agent_count = User.query.filter_by(role='agent').count()
    return render_template('main/index.html', recent_posts=recent_posts, agents=agents,
                           user_count=user_count, post_count=post_count, agent_count=agent_count)


@main.route('/health')
def health():
    return jsonify({'status': 'ok'})


@main.route('/api/users/search')
def search_users():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    found_users = User.query.filter(User.username.ilike(f'%{q}%')).limit(10).all()
    return jsonify([{'id': u.id, 'username': u.username, 'role': u.role} for u in found_users])
