import os
from dotenv import load_dotenv
from app import app
from routes import *
from backup_utils import start_backup_scheduler

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Start the backup scheduler if Supabase is configured
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
        backup_scheduler = start_backup_scheduler()
        app.logger.info("Backup scheduler started")
    else:
        app.logger.warning("Supabase not configured. Automated backups are disabled.")
    
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
