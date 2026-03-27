from datetime import datetime, timezone
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


followers_table = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')

    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    avatar_url = db.Column(db.String(255))
    language = db.Column(db.String(10), default='en')

    student_status = db.Column(db.String(30))
    visa_type = db.Column(db.String(20))
    university = db.Column(db.String(100))

    agent_verified = db.Column(db.Boolean, default=False)
    specializations = db.Column(db.Text)
    availability_status = db.Column(db.String(20), default='offline')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    replies = db.relationship('Reply', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    # Lambda joins required: string expressions can't resolve `followers_table`
    # in SQLAlchemy's eval scope for self-referential relationships.
    followed_agents = db.relationship(
        'User', secondary=followers_table,
        primaryjoin=lambda: User.id == followers_table.c.follower_id,
        secondaryjoin=lambda: User.id == followers_table.c.followed_id,
        backref='followers'
    )

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def get_specializations_list(self):
        if self.specializations:
            return [s.strip() for s in self.specializations.split(',')]
        return []

    def is_following(self, user):
        return user in self.followed_agents

    def follow(self, user):
        if not self.is_following(user):
            self.followed_agents.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed_agents.remove(user)

    def __repr__(self):
        return f'<User {self.username}>'


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.Text)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    like_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)

    is_anonymous = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)

    ai_suggested_resources = db.Column(db.Text)
    safety_flags = db.Column(db.Text)

    replies = db.relationship('Reply', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def get_tags_list(self):
        if self.tags:
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []

    def get_display_author(self):
        if self.is_anonymous:
            return None
        return self.author


class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='uq_like_user_post'),)


class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    like_count = db.Column(db.Integer, default=0)
    is_anonymous = db.Column(db.Boolean, default=False)
    safety_flags = db.Column(db.Text)

    likes = db.relationship('ReplyLike', backref='reply', lazy='dynamic', cascade='all, delete-orphan')

    def get_display_author(self):
        if self.is_anonymous:
            return None
        return self.author


class ReplyLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reply_id = db.Column(db.Integer, db.ForeignKey('reply.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('user_id', 'reply_id', name='uq_like_user_reply'),)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    reference_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    parent_message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    conversation_id = db.Column(db.String(64), index=True)

    safety_flags = db.Column(db.Text)

    @staticmethod
    def make_conversation_id(user1_id, user2_id):
        ids = sorted([user1_id, user2_id])
        return f"{ids[0]}_{ids[1]}"


class VerificationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    license_number = db.Column(db.String(100), nullable=False)
    issuing_authority = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    document_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending')
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    agent = db.relationship('User', foreign_keys=[agent_id], backref='verification_requests')


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.Text)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False)

    download_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    author = db.relationship('User', backref='resources')


class ConsultationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    topic = db.Column(db.String(200), nullable=False)
    preferred_time = db.Column(db.DateTime)
    message = db.Column(db.Text)

    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    responded_at = db.Column(db.DateTime)

    student = db.relationship('User', foreign_keys=[student_id], backref='consultation_requests_sent')
    agent = db.relationship('User', foreign_keys=[agent_id], backref='consultation_requests_received')
