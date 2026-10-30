import sqlite3

def create_database():
    conn = sqlite3.connect("farm_history.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_name TEXT,
            confidence REAL,
            timestamp TEXT,
            image_path TEXT
        )
    """)
    conn.close()


def save_alert(object_name, confidence, timestamp, image_path):
    conn = sqlite3.connect("farm_history.db")
    conn.execute("""
        INSERT INTO alerts
        (object_name, confidence, timestamp, image_path)
        VALUES (?, ?, ?, ?)
    """, (object_name, confidence, timestamp, image_path))
    conn.commit()
    conn.close()


create_database()