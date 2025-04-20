import os
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

def configure_database(app):
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
    
    # Initialize database with app
    db.init_app(app)
    
    return app 