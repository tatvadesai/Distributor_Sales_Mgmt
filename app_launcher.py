import webbrowser
import os
import sys
import logging
from threading import Timer
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_launcher.log')
)

# Load environment variables
load_dotenv()

def open_browser():
    try:
        webbrowser.open("http://127.0.0.1:8765")
        logging.info("Browser opened successfully")
    except Exception as e:
        logging.error(f"Failed to open browser: {str(e)}")

def main():
    try:
        # Add the current directory to sys.path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import app after setting up path
        from app import app, db
        import routes
        from backup_utils import start_backup_scheduler
        from models import Distributor
        from database.init_db import DISTRIBUTORS
        
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
        logging.info("Local backup scheduler started")
        
        print("\n╭─────────────────────────────────────────────────────────────────╮")
        print("│                                                                 │")
        print("│  Distributor Sales Management System                            │")
        print("│  Open your browser and navigate to: http://127.0.0.1:8765       │")
        print("│                                                                 │")
        print("│  Default login credentials:                                     │")
        print("│    Username: admin                                              │")
        print("│    Password: admin123                                           │")
        print("│                                                                 │")
        print("╰─────────────────────────────────────────────────────────────────╯\n")
        
        # Schedule browser opening 2 seconds after server start
        Timer(2, open_browser).start()
        
        # Run the Flask app
        app.run(
            host="127.0.0.1",  # Only allow local connections for security
            port=8765,
            debug=True,  # Enable debug for internal app
            use_reloader=False  # Important for PyInstaller
        )
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()