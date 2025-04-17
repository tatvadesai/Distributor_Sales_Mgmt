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
    
    app.run(host="0.0.0.0", port=8080, debug=True)
