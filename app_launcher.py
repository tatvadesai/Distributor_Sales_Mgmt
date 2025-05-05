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
        webbrowser.open("http://127.0.0.1:5001")
        logging.info("Browser opened successfully")
    except Exception as e:
        logging.error(f"Failed to open browser: {str(e)}")

def main():
    try:
        # Add the current directory to sys.path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import app after setting up path
        from app import app
        import routes  # Import routes module instead of using wildcard import
        from backup_utils import start_backup_scheduler
        
        # Start the backup scheduler
        backup_scheduler = start_backup_scheduler()
        logging.info("Local backup scheduler started")
        
        # Schedule browser opening 2 seconds after server start
        Timer(2, open_browser).start()
        
        # Run the Flask app
        app.run(
            host="127.0.0.1",  # Only allow local connections for security
            port=5001,
            debug=False,
            use_reloader=False  # Important for PyInstaller
        )
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()