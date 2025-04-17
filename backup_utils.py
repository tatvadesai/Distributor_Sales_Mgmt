import os
import json
import logging
import sqlite3
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from apscheduler.schedulers.background import BackgroundScheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Get a Supabase client using environment variables."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase URL and key must be set as environment variables.")
        return None
    
    try:
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"Error creating Supabase client: {str(e)}")
        return None

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
    """Perform a full backup of the database to Supabase."""
    # Get Supabase client
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase client not available. Backup aborted.")
        return False
    
    # Define database path (same as in app.py)
    db_path = os.environ.get("DATABASE_PATH", "instance/distributor_tracker.db")
    
    # Tables to backup
    tables = ["distributor", "target", "actual", "user"]
    
    # Timestamp for the backup
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    try:
        # Create a backup record
        backup_id = f"backup_{timestamp}"
        
        # Backup each table
        for table in tables:
            # Get table data
            data = backup_table(db_path, table)
            
            if not data:
                logger.warning(f"No data found for table {table}")
                continue
                
            # Store in Supabase
            table_backup = {
                "backup_id": backup_id,
                "table_name": table,
                "timestamp": timestamp,
                "data": json.dumps(data)
            }
            
            # Insert into Supabase
            result = supabase.table("backups").insert(table_backup).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error storing {table} backup: {result.error}")
            else:
                logger.info(f"Successfully backed up {table} with {len(data)} records")
        
        logger.info(f"Backup completed successfully: {backup_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error during backup: {str(e)}")
        return False

def start_backup_scheduler():
    """Start a scheduler to run weekly backups."""
    scheduler = BackgroundScheduler()
    
    # Run backup every Sunday at 2 AM
    scheduler.add_job(perform_backup, 'cron', day_of_week='sun', hour=2)
    
    # Start the scheduler
    scheduler.start()
    logger.info("Backup scheduler started. Backups will run every Sunday at 2 AM.")
    
    return scheduler

def restore_from_backup(backup_id):
    """
    Restore database from a specific backup.
    
    Args:
        backup_id: ID of the backup to restore
        
    Returns:
        bool: Success status
    """
    # Get Supabase client
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    # Define database path
    db_path = os.environ.get("DATABASE_PATH", "instance/distributor_tracker.db")
    
    try:
        # Get all tables from the backup
        result = supabase.table("backups").select("*").eq("backup_id", backup_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error retrieving backup: {result.error}")
            return False
            
        backup_tables = result.data
        
        if not backup_tables:
            logger.error(f"No backup found with ID {backup_id}")
            return False
            
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        for table_backup in backup_tables:
            table_name = table_backup["table_name"]
            data = json.loads(table_backup["data"])
            
            if not data:
                logger.warning(f"No data to restore for table {table_name}")
                continue
                
            # Clear existing data from table
            cursor.execute(f"DELETE FROM {table_name}")
            
            # Get column names from first record
            columns = list(data[0].keys())
            
            # Build insert statement
            placeholders = ", ".join(["?" for _ in columns])
            column_str = ", ".join(columns)
            sql = f"INSERT INTO {table_name} ({column_str}) VALUES ({placeholders})"
            
            # Insert data
            for record in data:
                values = [record[col] for col in columns]
                cursor.execute(sql, values)
                
            logger.info(f"Restored {len(data)} records to table {table_name}")
            
        # Commit transaction
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully restored from backup {backup_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error during restore: {str(e)}")
        
        # Try to rollback if connection exists
        try:
            conn.rollback()
            conn.close()
        except:
            pass
            
        return False

# Function to get list of available backups
def get_available_backups():
    """
    Get a list of all available backups from Supabase.
    
    Returns:
        list: List of backup IDs with timestamps
    """
    # Get Supabase client
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    try:
        # Get unique backup IDs
        result = supabase.table("backups").select("backup_id, timestamp").execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error retrieving backups: {result.error}")
            return []
            
        # Get unique backups
        backups = []
        seen = set()
        
        for record in result.data:
            if record["backup_id"] not in seen:
                backups.append({
                    "id": record["backup_id"],
                    "timestamp": record["timestamp"]
                })
                seen.add(record["backup_id"])
                
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
        
    except Exception as e:
        logger.error(f"Error retrieving backups: {str(e)}")
        return [] 