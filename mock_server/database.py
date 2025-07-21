import sqlite3

class Database:
    def __init__(self, db_name="tsm.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                creation_date INTEGER NOT NULL,
                last_used_date INTEGER NOT NULL,
                size INTEGER NOT NULL,
                is_encrypted BOOLEAN NOT NULL,
                encrypted_data BLOB,
                tags TEXT
            )
        """)
        self.conn.commit()

    def upsert_session(self, session):
        cursor = self.conn.cursor()
        tags = ",".join(session.tags)
        cursor.execute("""
            INSERT INTO sessions (id, name, creation_date, last_used_date, size, is_encrypted, encrypted_data, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                last_used_date=excluded.last_used_date,
                size=excluded.size,
                is_encrypted=excluded.is_encrypted,
                encrypted_data=excluded.encrypted_data,
                tags=excluded.tags
        """, (session.id, session.name, session.created_timestamp, session.created_timestamp, session.size_bytes, session.is_encrypted, None, tags))
        self.conn.commit()

    def get_session(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
        return cursor.fetchone()

    def get_all_sessions(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions")
        return cursor.fetchall()
