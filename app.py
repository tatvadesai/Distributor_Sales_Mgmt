import os
import logging
from datetime import datetime
from flask import Flask, session, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
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
db = SQLAlchemy(model_class=Base)

# Initialize CSRF protection
csrf = CSRFProtect()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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
    # Default path in /tmp to avoid permission issues
    db_path = os.path.join("/tmp", "distributor_tracker.db")

# Create directory if it doesn't exist
db_dir = os.path.dirname(db_path)
if not os.path.exists(db_dir) and db_dir:
    os.makedirs(db_dir, exist_ok=True)

print(f"Database path: {db_path}")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set Flask debug mode from environment
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

# Security settings
app.config['SESSION_COOKIE_SECURE'] = not app.config["DEBUG"]  # Secure in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = not app.config["DEBUG"]  # Secure in production
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 1 day in seconds

# Initialize database with app
db.init_app(app)

# Initialize CSRF protection with app
csrf.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models to ensure tables are created
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

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' data:; font-src 'self' cdn.jsdelivr.net;"
    return response

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {str(e)}")
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code=403, error_message="Access forbidden"), 403

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
        return f"{value:,.2f} cases" if value else "0.00 cases"
    return "0.00 cases"

@app.template_filter('format_percent')
def format_percent(value):
    if value is not None:
        return f"{value:.2f}%" if value else "0.00%"
    return "0.00%"
