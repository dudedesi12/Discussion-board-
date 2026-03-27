from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.posts import posts
from app.models import Post, Reply, PostLike, ReplyLike, User
from app.forms import PostForm, ReplyForm

CATEGORIES = ['Housing', 'Employment', 'Immigration', 'Healthcare', 'Legal', 'Academics', 'General']


@posts.route('/')
def index():
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    tag = request.args.get('tag', '')
    page = request.args.get('page', 1, type=int)

    query = Post.query
    if category and category in CATEGORIES:
        query = query.filter_by(category=category)
    if tag:
        query = query.filter(Post.tags.contains(tag))
    if sort == 'liked':
        query = query.order_by(Post.like_count.desc())
    elif sort == 'unanswered':
        query = query.filter_by(reply_count=0).order_by(Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())

    pagination = query.paginate(page=page, per_page=15, error_out=False)
    return render_template('posts/index.html', posts=pagination.items, pagination=pagination,
                           categories=CATEGORIES, current_category=category, current_sort=sort, current_tag=tag)


@posts.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            body=form.body.data,
            category=form.category.data,
            tags=form.tags.data,
            is_anonymous=form.is_anonymous.data,
            author_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('posts.show', id=post.id))
    return render_template('posts/create.html', form=form)


@posts.route('/<int:id>')
def show(id):
    post = Post.query.get_or_404(id)
    Post.query.filter_by(id=post.id).update({Post.view_count: (Post.view_count or 0) + 1})
    db.session.commit()
    form = ReplyForm()
    user_liked = False
    if current_user.is_authenticated:
        user_liked = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None
    replies = post.replies.order_by(Reply.created_at.asc()).all()
    return render_template('posts/show.html', post=post, form=form, user_liked=user_liked, replies=replies)


@posts.route('/<int:id>/reply', methods=['POST'])
@login_required
def reply(id):
    post = Post.query.get_or_404(id)
    form = ReplyForm()
    if form.validate_on_submit():
        r = Reply(
            body=form.body.data,
            post_id=post.id,
            author_id=current_user.id,
            is_anonymous=form.is_anonymous.data
        )
        post.reply_count = (post.reply_count or 0) + 1
        db.session.add(r)
        db.session.commit()
        flash('Reply posted!', 'success')
    return redirect(url_for('posts.show', id=id))


@posts.route('/<int:id>/like', methods=['POST'])
@login_required
def like_post(id):
    post = Post.query.get_or_404(id)
    existing = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        db.session.delete(existing)
        post.like_count = max(0, (post.like_count or 0) - 1)
        liked = False
    else:
        like = PostLike(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        post.like_count = (post.like_count or 0) + 1
        liked = True
    db.session.commit()
    return jsonify({'liked': liked, 'like_count': post.like_count})


@posts.route('/<int:id>/resolve', methods=['POST'])
@login_required
def resolve(id):
    post = Post.query.get_or_404(id)
    if post.author_id != current_user.id:
        abort(403)
    post.is_resolved = not post.is_resolved
    db.session.commit()
    flash('Post status updated.', 'success')
    return redirect(url_for('posts.show', id=id))


@posts.route('/replies/<int:id>/like', methods=['POST'])
@login_required
def like_reply(id):
    reply_obj = Reply.query.get_or_404(id)
    existing = ReplyLike.query.filter_by(user_id=current_user.id, reply_id=reply_obj.id).first()
    if existing:
        db.session.delete(existing)
        reply_obj.like_count = max(0, (reply_obj.like_count or 0) - 1)
        liked = False
    else:
        like = ReplyLike(user_id=current_user.id, reply_id=reply_obj.id)
        db.session.add(like)
        reply_obj.like_count = (reply_obj.like_count or 0) + 1
        liked = True
    db.session.commit()
    return jsonify({'liked': liked, 'like_count': reply_obj.like_count})


@posts.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(url_for('posts.index'))


@posts.route('/replies/<int:id>/delete', methods=['POST'])
@login_required
def delete_reply(id):
    r = Reply.query.get_or_404(id)
    post_id = r.post_id
    if r.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    post = db.session.get(Post, post_id)
    if post:
        post.reply_count = max(0, (post.reply_count or 0) - 1)
    db.session.delete(r)
    db.session.commit()
    flash('Reply deleted.', 'info')
    return redirect(url_for('posts.show', id=post_id))
