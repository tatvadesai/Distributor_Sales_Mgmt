import os
import logging
from datetime import datetime
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///distributor_tracker.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

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
