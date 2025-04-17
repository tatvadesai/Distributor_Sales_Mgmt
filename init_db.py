from app import app, db
from models import User, Distributor, Target, Actual
from werkzeug.security import generate_password_hash

# Initialize the database and create an admin user
with app.app_context():
    # Create all tables based on the models
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user")
    
    print("Database initialized successfully") 