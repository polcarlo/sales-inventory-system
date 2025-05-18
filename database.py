import os
import sqlite3
import runpy
from typing import Optional

DB_NAME = 'system.db'


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def create_schema() -> None:
    with get_connection() as conn:
        c = conn.cursor()

        # USERS
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        # CATEGORIES
        c.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # WAREHOUSES
        c.execute('''
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                capacity INTEGER NOT NULL
            )
        ''')

        # PRODUCTS
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                category_id INTEGER,
                cost_price REAL NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                warehouse_id INTEGER,
                FOREIGN KEY(category_id) REFERENCES categories(id),
                FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
            )
        ''')

        # DEPARTMENTS
        c.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # SUPPLIERS
        c.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                contact TEXT,
                phone TEXT,
                email TEXT,
                address TEXT
            )
        ''')

        # EXPENSES
        c.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                department_id INTEGER,
                description TEXT,
                amount REAL,
                FOREIGN KEY(department_id) REFERENCES departments(id)
            )
        ''')

        # DEBTS
        c.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL,
                due_date TEXT,
                status TEXT
            )
        ''')

        # DAMAGE_PRODUCTS
        c.execute('''
            CREATE TABLE IF NOT EXISTS damage_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prod_id INTEGER,
                date TEXT,
                qty INTEGER,
                reason TEXT,
                FOREIGN KEY(prod_id) REFERENCES products(id)
            )
        ''')

        # SALES
        c.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                prod_id INTEGER,
                qty INTEGER,
                FOREIGN KEY(prod_id) REFERENCES products(id)
            )
        ''')

        conn.commit()


def apply_migrations(migrations_folder: Optional[str] = None) -> None:
    if migrations_folder is None:
        migrations_folder = os.path.join(os.path.dirname(__file__), 'migrations')

    if not os.path.isdir(migrations_folder):
        return

    conn = get_connection()
    cur = conn.cursor()

    for fname in sorted(os.listdir(migrations_folder)):
        if fname.lower().endswith('.sql'):
            path = os.path.join(migrations_folder, fname)
            with open(path, 'r', encoding='utf-8') as f:
                sql = f.read().strip()
                if sql:
                    print(f"[sql migration] applying {fname}…")
                    cur.executescript(sql)

    conn.commit()
    conn.close()


def apply_migrations(scripts_folder: Optional[str] = None) -> None:
    if scripts_folder is None:
        scripts_folder = os.path.join(os.path.dirname(__file__), 'db')

    if not os.path.isdir(scripts_folder):
        return

    for script_name in ('migrate_columns.py', 'migrate_add_columns.py'):
        script_path = os.path.join(scripts_folder, script_name)
        if os.path.isfile(script_path):
            print(f"[python migration] running {script_name}…")
            runpy.run_path(script_path, run_name='__main__')


if __name__ == '__main__':
    create_schema()

    apply_migrations()

    apply_migrations()

    print("✅ Schema created and all migrations applied.")