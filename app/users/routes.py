from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.users import users
from app.models import User, Post, ConsultationRequest, VerificationRequest
from app.forms import ProfileEditForm, ConsultationRequestForm, VerificationForm


@users.route('/u/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_posts = user.posts.order_by(Post.created_at.desc()).limit(10).all()
    return render_template('users/profile.html', user=user, user_posts=user_posts)


@users.route('/u/<username>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    if current_user.username != username:
        abort(403)
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.bio = form.bio.data
        current_user.location = form.location.data
        current_user.visa_type = form.visa_type.data
        current_user.university = form.university.data
        current_user.student_status = form.student_status.data
        if current_user.role == 'agent':
            current_user.specializations = form.specializations.data
            current_user.availability_status = form.availability_status.data
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('users.profile', username=username))
    return render_template('users/edit.html', form=form, user=current_user)


@users.route('/u/<username>/follow', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    if current_user.is_following(user):
        current_user.unfollow(user)
        following = False
    else:
        current_user.follow(user)
        following = True
    db.session.commit()
    return jsonify({'following': following, 'follower_count': len(user.followers)})


@users.route('/agent/verify', methods=['GET', 'POST'])
@login_required
def agent_verify():
    if current_user.role != 'agent':
        abort(403)
    form = VerificationForm()
    if form.validate_on_submit():
        vr = VerificationRequest(
            agent_id=current_user.id,
            license_number=form.license_number.data,
            issuing_authority=form.issuing_authority.data,
            expiry_date=form.expiry_date.data,
            document_url=form.document_url.data
        )
        db.session.add(vr)
        db.session.commit()
        flash('Verification request submitted!', 'success')
        return redirect(url_for('users.profile', username=current_user.username))
    return render_template('users/edit.html', form=form, user=current_user, verification_mode=True)


@users.route('/agent/requests')
@login_required
def agent_requests():
    if current_user.role != 'agent':
        abort(403)
    reqs = ConsultationRequest.query.filter_by(agent_id=current_user.id).order_by(ConsultationRequest.created_at.desc()).all()
    return render_template('users/profile.html', user=current_user, user_posts=[], consultation_requests=reqs)


@users.route('/agent/requests/<int:id>/respond', methods=['POST'])
@login_required
def respond_consultation(id):
    if current_user.role != 'agent':
        abort(403)
    req = ConsultationRequest.query.get_or_404(id)
    if req.agent_id != current_user.id:
        abort(403)
    action = request.form.get('action')
    if action in ('accepted', 'declined'):
        req.status = action
        from datetime import datetime
        req.responded_at = datetime.utcnow()
        db.session.commit()
        flash(f'Request {action}.', 'success')
    return redirect(url_for('users.agent_requests'))


@users.route('/consultation/<username>', methods=['GET', 'POST'])
@login_required
def request_consultation(username):
    agent = User.query.filter_by(username=username, role='agent').first_or_404()
    form = ConsultationRequestForm()
    if form.validate_on_submit():
        cr = ConsultationRequest(
            student_id=current_user.id,
            agent_id=agent.id,
            topic=form.topic.data,
            preferred_time=form.preferred_time.data,
            message=form.message.data
        )
        db.session.add(cr)
        db.session.commit()
        flash('Consultation request sent!', 'success')
        return redirect(url_for('users.profile', username=username))
    return render_template('users/profile.html', user=agent, user_posts=[], consult_form=form)
