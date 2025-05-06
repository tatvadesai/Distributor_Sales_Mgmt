import os
import logging
from datetime import datetime
from flask import Flask, session, request, render_template, redirect, url_for

# Handle the flask_login import with complete fallback mechanism
try:
    from flask_login import LoginManager, login_user, logout_user, login_required, current_user
    HAS_FLASK_LOGIN = True
except ImportError:
    print("WARNING: flask_login module not found. Using simple auth fallback.")
    HAS_FLASK_LOGIN = False
    
    # Create dummy classes and functions for flask_login
    class DummyLoginManager:
        def __init__(self):
            self.login_view = 'login'
        
        def init_app(self, app):
            pass
    
    class DummyUserMixin:
        @property
        def is_authenticated(self):
            return True
        
        @property
        def is_active(self):
            return True
        
        @property
        def is_anonymous(self):
            return False
        
        def get_id(self):
            return "1"
    
    # Create a global user that's always authenticated
    class DummyUser(DummyUserMixin):
        id = 1
        username = "admin"
        
    # Create a dummy current_user
    current_user = DummyUser()
    
    # Create dummy decorator functions
    def login_required(f):
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    
    def login_user(user, remember=False):
        return True
    
    def logout_user():
        return True
    
    # Use the dummy login manager
    LoginManager = DummyLoginManager

# We're not using CSRF protection at all
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import pathlib

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging_level = logging.DEBUG if os.environ.get("FLASK_DEBUG", "true").lower() == "true" else logging.INFO
logging.basicConfig(level=logging_level, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy(model_class=Base)
except ImportError:
    print("WARNING: flask_sqlalchemy not found. Database operations will not work.")
    db = None

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set Flask debug mode from environment
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

# Configure database
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path_env = os.environ.get("DATABASE_PATH")

if db_path_env:
    # Use the environment variable if provided
    if os.path.isabs(db_path_env):
        # Absolute path from environment
        db_path = db_path_env
    else:
        # Relative path from environment - make it absolute
        db_path = os.path.join(current_dir, db_path_env)
else:
    # Default path in the application directory
    db_path = os.path.join(current_dir, "data", "distributor_tracker.db")

# Create directory if it doesn't exist
db_dir = os.path.dirname(db_path)
if not os.path.exists(db_dir) and db_dir:
    os.makedirs(db_dir, exist_ok=True)

print(f"Database path: {db_path}")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Security settings
app.config['SESSION_COOKIE_SECURE'] = False  # Not needed for internal app
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = False  # Not needed for internal app
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 1 day in seconds

# Completely disable WTF CSRF
app.config['WTF_CSRF_ENABLED'] = False

# Create a context processor to provide a dummy csrf_token function to templates
@app.context_processor
def inject_csrf_token():
    def csrf_token():
        return "dummy_token"
    return dict(csrf_token=csrf_token)

# Initialize database with app
if db:
    db.init_app(app)

# Configure login manager
login_manager = LoginManager()
if HAS_FLASK_LOGIN:
    login_manager.init_app(app)
    login_manager.login_view = 'login'
else:
    print("WARNING: Using dummy login manager, all authentication is bypassed")

# Import models if database is available
if db:
    try:
        with app.app_context():
            from models import User, Distributor, Target, Actual
            db.create_all()
            
            # Create admin user if it doesn't exist
            from werkzeug.security import generate_password_hash
            from models import User
            
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin)
                db.session.commit()
                logging.info("Created default admin user")
    except ImportError:
        print("WARNING: Unable to import models - database migrations skipped")

# User loader for Flask-Login
if HAS_FLASK_LOGIN:
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from models import User
            return User.query.get(int(user_id))
        except:
            # Fallback to dummy user
            return DummyUser()

# Simplified security headers for internal app
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    logging.warning(f"Page not found: {request.url}")
    return render_template('error.html', 
                         error_code=404, 
                         error_message="The page you're looking for doesn't exist. Please check the URL or contact IT support."), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {str(e)}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Something went wrong on our end. Please try again or contact IT support if the problem persists."), 500

@app.errorhandler(403)
def forbidden(e):
    logging.warning(f"Access forbidden: {request.url} by {request.remote_addr}")
    return render_template('error.html', 
                         error_code=403, 
                         error_message="You don't have permission to access this page. Please contact your administrator if you believe this is an error."), 403

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled exception: {str(e)}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message="An unexpected error occurred. Please contact IT support with the error details."), 500

# Jinja2 template filters
@app.template_filter('format_date')
def format_date(value, format='%Y-%m-%d'):
    if value:
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').strftime(format)
            except ValueError:
                return value
        return value.strftime(format)
    return ""

@app.template_filter('format_currency')
def format_currency(value):
    if value is not None:
        return f"{int(value):,} cases" if value else "0 cases"
    return "0 cases"

@app.template_filter('format_percent')
def format_percent(value):
    if value is not None:
        return f"{int(value)}%" if value else "0%"
    return "0%"
