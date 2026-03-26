import pytest
from app import create_app
from models import db, User, Post, Reply, Message
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def register_user(client, username, email, role, password='password123'):
    return client.post('/register', data={
        'username': username,
        'email': email,
        'role': role,
        'password': password,
        'password2': password,
    }, follow_redirects=True)


def login_user(client, email, password='password123'):
    return client.post('/login', data={
        'email': email,
        'password': password,
    }, follow_redirects=True)


class TestUserRegistration:
    def test_register_customer(self, client):
        response = register_user(client, 'student1', 'student1@test.com', 'customer')
        assert response.status_code == 200
        assert b'Registration successful' in response.data

    def test_register_agent(self, client):
        response = register_user(client, 'agent1', 'agent1@test.com', 'agent')
        assert response.status_code == 200
        assert b'Registration successful' in response.data

    def test_register_duplicate_username(self, client):
        register_user(client, 'user1', 'user1@test.com', 'customer')
        response = register_user(client, 'user1', 'user2@test.com', 'customer')
        assert b'Username already taken' in response.data

    def test_register_duplicate_email(self, client):
        register_user(client, 'user1', 'same@test.com', 'customer')
        response = register_user(client, 'user2', 'same@test.com', 'customer')
        assert b'Email already registered' in response.data

    def test_register_password_mismatch(self, client):
        response = client.post('/register', data={
            'username': 'user1',
            'email': 'user1@test.com',
            'role': 'customer',
            'password': 'password123',
            'password2': 'different',
        }, follow_redirects=True)
        assert b'Registration successful' not in response.data


class TestAuthentication:
    def test_login_valid(self, client):
        register_user(client, 'testuser', 'test@test.com', 'customer')
        response = login_user(client, 'test@test.com')
        assert response.status_code == 200
        assert b'Welcome back' in response.data

    def test_login_invalid_password(self, client):
        register_user(client, 'testuser', 'test@test.com', 'customer')
        response = login_user(client, 'test@test.com', 'wrongpassword')
        assert b'Invalid email or password' in response.data

    def test_login_invalid_email(self, client):
        response = login_user(client, 'nonexistent@test.com')
        assert b'Invalid email or password' in response.data

    def test_logout(self, client):
        register_user(client, 'testuser', 'test@test.com', 'customer')
        login_user(client, 'test@test.com')
        response = client.get('/logout', follow_redirects=True)
        assert b'logged out' in response.data


class TestDiscussionBoard:
    def test_index_page_public(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Discussion Board' in response.data

    def test_create_post_requires_login(self, client):
        response = client.post('/post/new', data={
            'title': 'Test post',
            'body': 'Test body content',
            'category': 'General',
        }, follow_redirects=True)
        assert b'Please log in' in response.data

    def test_create_post_as_customer(self, client):
        register_user(client, 'customer1', 'customer1@test.com', 'customer')
        login_user(client, 'customer1@test.com')
        response = client.post('/post/new', data={
            'title': 'My work permit question',
            'body': 'I need help with my work permit application process.',
            'category': 'Immigration',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Your post has been created' in response.data

    def test_view_post(self, client, app):
        register_user(client, 'customer1', 'customer1@test.com', 'customer')
        login_user(client, 'customer1@test.com')
        client.post('/post/new', data={
            'title': 'Test post',
            'body': 'Test body content here.',
            'category': 'General',
        }, follow_redirects=True)
        response = client.get('/post/1')
        assert response.status_code == 200
        assert b'Test post' in response.data

    def test_reply_to_post_as_agent(self, client, app):
        # Customer creates post
        register_user(client, 'customer1', 'customer1@test.com', 'customer')
        login_user(client, 'customer1@test.com')
        client.post('/post/new', data={
            'title': 'Need help',
            'body': 'I need help with my housing issue.',
            'category': 'Housing',
        }, follow_redirects=True)
        client.get('/logout')

        # Agent replies
        register_user(client, 'agent1', 'agent1@test.com', 'agent')
        login_user(client, 'agent1@test.com')
        response = client.post('/post/1', data={
            'body': 'I can help you with your housing issue.',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Your reply has been posted' in response.data

    def test_delete_post_as_owner(self, client, app):
        register_user(client, 'customer1', 'customer1@test.com', 'customer')
        login_user(client, 'customer1@test.com')
        client.post('/post/new', data={
            'title': 'Post to delete',
            'body': 'This will be deleted.',
            'category': 'General',
        }, follow_redirects=True)
        response = client.post('/post/1/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Post deleted' in response.data

    def test_delete_post_forbidden_for_other_customer(self, client, app):
        # Customer 1 creates post
        register_user(client, 'customer1', 'customer1@test.com', 'customer')
        login_user(client, 'customer1@test.com')
        client.post('/post/new', data={
            'title': 'Protected post',
            'body': 'This should not be deleted by others.',
            'category': 'General',
        }, follow_redirects=True)
        client.get('/logout')

        # Customer 2 tries to delete
        register_user(client, 'customer2', 'customer2@test.com', 'customer')
        login_user(client, 'customer2@test.com')
        response = client.post('/post/1/delete', follow_redirects=True)
        assert response.status_code == 403

    def test_agent_can_delete_any_post(self, client, app):
        # Customer creates post
        register_user(client, 'customer1', 'customer1@test.com', 'customer')
        login_user(client, 'customer1@test.com')
        client.post('/post/new', data={
            'title': 'Post by customer',
            'body': 'This is a customer post.',
            'category': 'General',
        }, follow_redirects=True)
        client.get('/logout')

        # Agent deletes
        register_user(client, 'agent1', 'agent1@test.com', 'agent')
        login_user(client, 'agent1@test.com')
        response = client.post('/post/1/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Post deleted' in response.data


class TestMessaging:
    def test_inbox_requires_login(self, client):
        response = client.get('/messages', follow_redirects=True)
        assert b'Please log in' in response.data

    def test_send_message(self, client, app):
        register_user(client, 'sender', 'sender@test.com', 'customer')
        register_user(client, 'recipient', 'recipient@test.com', 'agent')
        login_user(client, 'sender@test.com')
        response = client.post('/messages/compose', data={
            'recipient': 'recipient',
            'subject': 'Hello Agent',
            'body': 'I need help with my application.',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Message sent to recipient' in response.data

    def test_receive_message_in_inbox(self, client, app):
        register_user(client, 'agent1', 'agent1@test.com', 'agent')
        register_user(client, 'customer1', 'customer1@test.com', 'customer')
        login_user(client, 'agent1@test.com')
        client.post('/messages/compose', data={
            'recipient': 'customer1',
            'subject': 'Follow-up',
            'body': 'Please provide more details.',
        }, follow_redirects=True)
        client.get('/logout')

        login_user(client, 'customer1@test.com')
        response = client.get('/messages')
        assert response.status_code == 200
        assert b'Follow-up' in response.data

    def test_cannot_send_message_to_self(self, client):
        register_user(client, 'user1', 'user1@test.com', 'customer')
        login_user(client, 'user1@test.com')
        response = client.post('/messages/compose', data={
            'recipient': 'user1',
            'subject': 'To myself',
            'body': 'This should fail.',
        }, follow_redirects=True)
        assert b'cannot send a message to yourself' in response.data

    def test_cannot_send_to_nonexistent_user(self, client):
        register_user(client, 'user1', 'user1@test.com', 'customer')
        login_user(client, 'user1@test.com')
        response = client.post('/messages/compose', data={
            'recipient': 'nobody',
            'subject': 'Test',
            'body': 'This should fail.',
        }, follow_redirects=True)
        assert b'User not found' in response.data

    def test_message_marked_read_on_view(self, client, app):
        register_user(client, 'sender', 'sender@test.com', 'agent')
        register_user(client, 'receiver', 'receiver@test.com', 'customer')
        login_user(client, 'sender@test.com')
        client.post('/messages/compose', data={
            'recipient': 'receiver',
            'subject': 'Read me',
            'body': 'Please read this.',
        }, follow_redirects=True)
        client.get('/logout')

        login_user(client, 'receiver@test.com')
        with app.app_context():
            msg = Message.query.first()
            assert msg.read is False
            client.get(f'/messages/{msg.id}')
            db.session.refresh(msg)
            assert msg.read is True


class TestUserRoles:
    def test_user_is_agent(self, app):
        with app.app_context():
            user = User(username='agent1', email='agent1@test.com', role='agent')
            user.set_password('test')
            assert user.is_agent is True

    def test_user_is_not_agent(self, app):
        with app.app_context():
            user = User(username='customer1', email='customer1@test.com', role='customer')
            user.set_password('test')
            assert user.is_agent is False

    def test_users_list_page(self, client):
        register_user(client, 'agent1', 'agent1@test.com', 'agent')
        login_user(client, 'agent1@test.com')
        response = client.get('/users')
        assert response.status_code == 200
        assert b'Agents' in response.data
        assert b'Customers' in response.data
