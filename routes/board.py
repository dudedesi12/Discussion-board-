from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Post, Reply, User
from forms import PostForm, ReplyForm

board_bp = Blueprint('board', __name__)


@board_bp.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    agents = User.query.filter_by(role='agent').all()
    return render_template('board/index.html', posts=posts, agents=agents)


@board_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            body=form.body.data,
            category=form.category.data,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('board.view_post', post_id=post.id))
    return render_template('board/new_post.html', form=form)


@board_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = ReplyForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You must be logged in to reply.', 'warning')
            return redirect(url_for('auth.login'))
        reply = Reply(
            body=form.body.data,
            user_id=current_user.id,
            post_id=post.id
        )
        db.session.add(reply)
        db.session.commit()
        flash('Your reply has been posted!', 'success')
        return redirect(url_for('board.view_post', post_id=post.id))
    replies = post.replies.order_by(Reply.created_at.asc()).all()
    return render_template('board/post.html', post=post, replies=replies, form=form)


@board_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_agent:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(url_for('board.index'))


@board_bp.route('/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
def delete_reply(reply_id):
    reply = Reply.query.get_or_404(reply_id)
    post_id = reply.post_id
    if reply.user_id != current_user.id and not current_user.is_agent:
        abort(403)
    db.session.delete(reply)
    db.session.commit()
    flash('Reply deleted.', 'info')
    return redirect(url_for('board.view_post', post_id=post_id))


@board_bp.route('/users')
@login_required
def users_list():
    agents = User.query.filter_by(role='agent').all()
    customers = User.query.filter_by(role='customer').all()
    return render_template('board/users.html', agents=agents, customers=customers)
