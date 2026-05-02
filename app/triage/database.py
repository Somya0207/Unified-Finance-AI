import sqlite3
import json
from datetime import datetime

class SQLiteCollection:
    def __init__(self, db_path="tickets.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                parsed TEXT,
                response TEXT,
                status TEXT,
                created_at TIMESTAMP
            )
        ''')
        self.conn.commit()

    def insert_one(self, ticket):
        cursor = self.conn.cursor()
        created_at = ticket.get("created_at", datetime.utcnow())
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
            
        cursor.execute('''
            INSERT INTO tickets (query, parsed, response, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            ticket.get("query"),
            json.dumps(ticket.get("parsed", {})),
            ticket.get("response"),
            ticket.get("status"),
            created_at
        ))
        self.conn.commit()
        
        class Result:
            inserted_id = cursor.lastrowid
        return Result()

    def find(self):
        class Cursor:
            def __init__(self, conn):
                self.conn = conn
                self._sort = None
                self._limit = None
            
            def sort(self, field, direction):
                self._sort = (field, "DESC" if direction == -1 else "ASC")
                return self
            
            def limit(self, limit):
                self._limit = limit
                return self
                
            def __iter__(self):
                query = "SELECT * FROM tickets"
                if self._sort:
                    query += f" ORDER BY {self._sort[0]} {self._sort[1]}"
                if self._limit:
                    query += f" LIMIT {self._limit}"
                    
                cursor = self.conn.cursor()
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                for row in cursor.fetchall():
                    data = dict(zip(columns, row))
                    data["parsed"] = json.loads(data["parsed"])
                    if isinstance(data["created_at"], str):
                        try:
                            data["created_at"] = datetime.fromisoformat(data["created_at"])
                        except Exception:
                            pass
                    yield data

        return Cursor(self.conn)

collection = SQLiteCollection()