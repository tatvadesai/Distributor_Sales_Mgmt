from app import app, db
import sqlite3

# Migration script to add week_start_date and week_end_date columns to target table
def migrate_target_table():
    # Use app context
    with app.app_context():
        try:
            # Connect to SQLite database
            conn = sqlite3.connect('instance/distributor_tracker.db')
            cursor = conn.cursor()
            
            # Check if the columns already exist
            cursor.execute("PRAGMA table_info(target)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add week_start_date column if it doesn't exist
            if "week_start_date" not in columns:
                cursor.execute("ALTER TABLE target ADD COLUMN week_start_date VARCHAR(10)")
                print("Added week_start_date column to target table")
            
            # Add week_end_date column if it doesn't exist
            if "week_end_date" not in columns:
                cursor.execute("ALTER TABLE target ADD COLUMN week_end_date VARCHAR(10)")
                print("Added week_end_date column to target table")
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_target_table() 