from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Message, User
from forms import MessageForm

messages_bp = Blueprint('messages', __name__)


@messages_bp.route('/messages')
@login_required
def inbox():
    received = Message.query.filter_by(recipient_id=current_user.id)\
        .order_by(Message.created_at.desc()).all()
    sent = Message.query.filter_by(sender_id=current_user.id)\
        .order_by(Message.created_at.desc()).all()
    unread_count = Message.query.filter_by(recipient_id=current_user.id, read=False).count()
    return render_template('messages/inbox.html', received=received, sent=sent,
                           unread_count=unread_count)


@messages_bp.route('/messages/compose', methods=['GET', 'POST'])
@messages_bp.route('/messages/compose/<username>', methods=['GET', 'POST'])
@login_required
def compose(username=None):
    form = MessageForm()
    if username:
        form.recipient.data = username
    if form.validate_on_submit():
        recipient = User.query.filter_by(username=form.recipient.data).first()
        if recipient is None:
            flash('User not found. Please check the username.', 'danger')
            return redirect(url_for('messages.compose'))
        if recipient.id == current_user.id:
            flash('You cannot send a message to yourself.', 'warning')
            return redirect(url_for('messages.compose'))
        msg = Message(
            subject=form.subject.data,
            body=form.body.data,
            sender_id=current_user.id,
            recipient_id=recipient.id
        )
        db.session.add(msg)
        db.session.commit()
        flash(f'Message sent to {recipient.username}!', 'success')
        return redirect(url_for('messages.inbox'))
    return render_template('messages/compose.html', form=form)


@messages_bp.route('/messages/<int:message_id>')
@login_required
def view_message(message_id):
    msg = Message.query.get_or_404(message_id)
    if msg.recipient_id != current_user.id and msg.sender_id != current_user.id:
        abort(403)
    if msg.recipient_id == current_user.id and not msg.read:
        msg.read = True
        db.session.commit()
    return render_template('messages/view.html', msg=msg)


@messages_bp.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    msg = Message.query.get_or_404(message_id)
    if msg.recipient_id != current_user.id and msg.sender_id != current_user.id:
        abort(403)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('messages.inbox'))
