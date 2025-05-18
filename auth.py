import sqlite3, hashlib
from database import get_connection

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(first_name: str, last_name: str, username: str, password: str) -> bool:
    hashed = hash_password(password)
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users')
        count = c.fetchone()[0]
        role = 'admin' if count == 0 else 'user'
        try:
            c.execute(
                'INSERT INTO users (first_name, last_name, username, password, role) VALUES (?, ?, ?, ?, ?)',
                (first_name, last_name, username, hashed, role)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  

def authenticate(username: str, password: str):
    hashed = hash_password(password)
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            'SELECT id, first_name, last_name, username, role FROM users WHERE username = ? AND password = ?',
            (username, hashed)
        )
        return c.fetchone() 
