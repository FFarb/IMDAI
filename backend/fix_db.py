import sqlite3
from pathlib import Path

# Path to the database
DB_PATH = Path("C:/Users/chern/Desktop/IMDAI-expiremental version/backend/data/pod_swarm.db")

def migrate_db():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(generations)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "metadata_json_str" in columns:
            print("Column 'metadata_json_str' already exists.")
        else:
            print("Adding column 'metadata_json_str'...")
            cursor.execute("ALTER TABLE generations ADD COLUMN metadata_json_str TEXT DEFAULT '{}'")
            conn.commit()
            print("Migration successful.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
