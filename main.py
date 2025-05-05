import os
from dotenv import load_dotenv
from app import app, db
from routes import *
from backup_utils import start_backup_scheduler
from models import Distributor
from database.init_db import DISTRIBUTORS

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Seed initial distributors
        existing = {d.name for d in Distributor.query.all()}
        for name in DISTRIBUTORS:
            if name not in existing:
                db.session.add(Distributor(name=name))
        db.session.commit()

    # Start the backup scheduler
    backup_scheduler = start_backup_scheduler()
    app.logger.info("Local backup scheduler started")
    
    print("\n╭─────────────────────────────────────────────────────────────────╮")
    print("│                                                                 │")
    print("│  Distributor Sales Management System                            │")
    print("│  Open your browser and navigate to: http://127.0.0.1:5001       │")
    print("│                                                                 │")
    print("│  Default login credentials:                                     │")
    print("│    Username: admin                                              │")
    print("│    Password: admin123                                           │")
    print("│                                                                 │")
    print("╰─────────────────────────────────────────────────────────────────╯\n")
    
    app.run(host="0.0.0.0", port=5001, debug=True)
