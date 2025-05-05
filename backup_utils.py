import os
import json
import logging
import sqlite3
import pandas as pd
from datetime import datetime
import shutil
import os
from apscheduler.schedulers.background import BackgroundScheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_backup_dir():
    """Create backups directory if it doesn't exist"""
    backup_dir = os.path.join(os.getcwd(), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir

def backup_table(db_path, table_name):
    """
    Extract data from a SQLite table and convert to a list of dictionaries.
    
    Args:
        db_path: Path to the SQLite database
        table_name: Name of the table to backup
        
    Returns:
        List of dictionaries representing the rows
    """
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        # Read the table into a DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        # Convert to list of dictionaries
        records = df.to_dict(orient='records')
        
        # Close connection
        conn.close()
        
        return records
    except Exception as e:
        logger.error(f"Error backing up table {table_name}: {str(e)}")
        return []

def perform_backup():
    """Perform a full backup of the database to local storage"""
    backup_dir = ensure_backup_dir()
    db_path = os.environ.get("DATABASE_PATH", "instance/distributor_tracker.db")
    tables = ["distributor", "target", "actual", "user"]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_id = f"backup_{timestamp}"
    
    try:
        # Create backup directory for this backup
        backup_path = os.path.join(backup_dir, backup_id)
        os.makedirs(backup_path)
        
        # Backup each table
        for table in tables:
            data = backup_table(db_path, table)
            if not data:
                continue
                
            # Save as JSON file
            file_path = os.path.join(backup_path, f"{table}.json")
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            logger.info(f"Saved {table} backup with {len(data)} records to {file_path}")
        
        # Copy database file
        db_backup_path = os.path.join(backup_path, "database.db")
        shutil.copy2(db_path, db_backup_path)
        
        logger.info(f"Local backup completed: {backup_id}")
        return True
    
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return False

def start_backup_scheduler():
    """Start a scheduler to run backups three times a week."""
    scheduler = BackgroundScheduler()
    
    # Run backups three times a week:
    # 1. Monday at 3 PM
    # 2. Wednesday at 12 PM
    # 3. Saturday at 11 AM
    scheduler.add_job(perform_backup, 'cron', day_of_week='mon', hour=15)  # Monday 3 PM
    scheduler.add_job(perform_backup, 'cron', day_of_week='wed', hour=12)  # Wednesday 12 PM
    scheduler.add_job(perform_backup, 'cron', day_of_week='sat', hour=11)  # Saturday 11 AM
    
    # Start the scheduler
    scheduler.start()
    logger.info("Backup scheduler started. Backups will run three times a week: Monday at 3 PM, Wednesday at 12 PM, and Saturday at 11 AM.")
    
    return scheduler

def restore_from_backup(backup_id):
    """
    Restore database from a local backup
    
    Args:
        backup_id: ID of the backup to restore
        
    Returns:
        bool: Success status
    """
    backup_dir = os.path.join(os.getcwd(), 'backups')
    backup_path = os.path.join(backup_dir, backup_id)
    db_path = os.environ.get("DATABASE_PATH", "instance/distributor_tracker.db")
    
    if not os.path.exists(backup_path):
        logger.error(f"Backup {backup_id} not found")
        return False
    
    try:
        # Restore database file
        db_backup = os.path.join(backup_path, "database.db")
        if os.path.exists(db_backup):
            shutil.copy2(db_backup, db_path)
            logger.info("Database file restored successfully")
            return True
        
        # Fallback to JSON restoration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION")
        
        for table in ["distributor", "target", "actual", "user"]:
            json_file = os.path.join(backup_path, f"{table}.json")
            if not os.path.exists(json_file):
                continue
            
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            cursor.execute(f"DELETE FROM {table}")
            columns = list(data[0].keys())
            placeholders = ", ".join(["?" for _ in columns])
            column_str = ", ".join(columns)
            sql = f"INSERT INTO {table} ({column_str}) VALUES ({placeholders})"
            
            for record in data:
                values = [record[col] for col in columns]
                cursor.execute(sql, values)
            
            logger.info(f"Restored {len(data)} {table} records")
        
        conn.commit()
        conn.close()
        logger.info(f"Successfully restored from backup {backup_id}")
        return True
    
    except Exception as e:
        logger.error(f"Restore failed: {str(e)}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

# Function to get list of available backups
def get_available_backups():
    """
    Get list of local backups
    
    Returns:
        list: Sorted backup IDs with timestamps
    """
    backup_dir = os.path.join(os.getcwd(), 'backups')
    backups = []
    
    try:
        if os.path.exists(backup_dir):
            for dir_name in os.listdir(backup_dir):
                if dir_name.startswith("backup_"):
                    timestamp_str = dir_name.split("_", 1)[1]
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                    backups.append({
                        "id": dir_name,
                        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        return []