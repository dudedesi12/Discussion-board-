from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.messages import messages
from app.models import Message, User
from app.forms import MessageForm
from sqlalchemy import or_


@messages.route('/inbox')
@login_required
def inbox():
    all_msgs = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()

    convs = {}
    for msg in all_msgs:
        cid = msg.conversation_id
        if cid not in convs:
            convs[cid] = msg
    conversations = list(convs.values())
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return render_template('messages/inbox.html', conversations=conversations, unread_count=unread_count)


@messages.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    form = MessageForm()
    recipient_username = request.args.get('to', '')
    if recipient_username and not form.is_submitted():
        form.recipient_username.data = recipient_username
    ref_post = request.args.get('post_id', '')
    if ref_post and not form.is_submitted():
        form.reference_post_id.data = ref_post

    if form.validate_on_submit():
        recipient = User.query.filter_by(username=form.recipient_username.data).first()
        if not recipient:
            flash('Recipient not found.', 'danger')
            return render_template('messages/compose.html', form=form)
        conv_id = Message.make_conversation_id(current_user.id, recipient.id)
        msg = Message(
            subject=form.subject.data,
            body=form.body.data,
            sender_id=current_user.id,
            recipient_id=recipient.id,
            conversation_id=conv_id,
            reference_post_id=form.reference_post_id.data or None
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message sent!', 'success')
        return redirect(url_for('messages.conversation', conv_id=conv_id))
    return render_template('messages/compose.html', form=form)


@messages.route('/conversation/<conv_id>')
@login_required
def conversation(conv_id):
    msgs = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at.asc()).all()
    if not msgs:
        abort(404)
    ids = [int(x) for x in conv_id.split('_')]
    if current_user.id not in ids:
        abort(403)
    for m in msgs:
        if m.recipient_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()
    form = MessageForm()
    other_id = ids[0] if ids[1] == current_user.id else ids[1]
    other_user = User.query.get(other_id)
    return render_template('messages/conversation.html', messages=msgs, conv_id=conv_id, other_user=other_user, form=form)


@messages.route('/reply/<conv_id>', methods=['POST'])
@login_required
def reply_message(conv_id):
    ids = [int(x) for x in conv_id.split('_')]
    if current_user.id not in ids:
        abort(403)
    other_id = ids[0] if ids[1] == current_user.id else ids[1]
    body = request.form.get('body', '').strip()
    subject = request.form.get('subject', 'Re: conversation').strip()
    if not body:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('messages.conversation', conv_id=conv_id))
    msg = Message(
        subject=subject,
        body=body,
        sender_id=current_user.id,
        recipient_id=other_id,
        conversation_id=conv_id
    )
    db.session.add(msg)
    db.session.commit()
    flash('Reply sent!', 'success')
    return redirect(url_for('messages.conversation', conv_id=conv_id))
