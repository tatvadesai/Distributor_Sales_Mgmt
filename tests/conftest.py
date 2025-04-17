import os
import pytest
import tempfile
from app import app as flask_app
from app import db as _db
from models import User
from werkzeug.security import generate_password_hash

@pytest.fixture(scope='session')
def app():
    """Session-wide test Flask application."""
    # Configure app for testing
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF during tests
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Create the database and the database tables
    with flask_app.app_context():
        _db.create_all()
        
        # Create test user
        test_user = User(
            username='testuser',
            password_hash=generate_password_hash('password123')
        )
        _db.session.add(test_user)
        _db.session.commit()
    
    yield flask_app
    
    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database."""
    with app.app_context():
        yield _db

@pytest.fixture(scope='function')
def session(db):
    """Creates a new database session for each test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.session
    
    yield session
    
    # Rollback the transaction and close the connection
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def logged_in_client(client):
    """A test client that's logged in as the test user."""
    with client.session_transaction() as sess:
        # Log in the user
        client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
    return client 