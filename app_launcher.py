import webbrowser
import os
import sys
import logging
import subprocess
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

def clear_browser_cache():
    """Clear browser cache for localhost:5001"""
    try:
        # For Windows
        if os.name == 'nt':
            # Clear Chrome cache
            chrome_cache = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache')
            if os.path.exists(chrome_cache):
                subprocess.run(['rmdir', '/s', '/q', chrome_cache], shell=True)
            
            # Clear Firefox cache
            firefox_cache = os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles\*\cache2')
            if os.path.exists(firefox_cache):
                subprocess.run(['rmdir', '/s', '/q', firefox_cache], shell=True)
            
            # Clear Edge cache
            edge_cache = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache')
            if os.path.exists(edge_cache):
                subprocess.run(['rmdir', '/s', '/q', edge_cache], shell=True)
        
        logging.info("Browser cache cleared successfully")
    except Exception as e:
        logging.error(f"Failed to clear browser cache: {str(e)}")

def open_browser():
    try:
        clear_browser_cache()
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