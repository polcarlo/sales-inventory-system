import sqlite3

DB_NAME = 'system.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def migrate_add_columns():
    tables = [
        'users', 'categories', 'warehouses', 'products',
        'departments', 'suppliers', 'expenses',
        'debts', 'damage_products', 'sales'
    ]

    with get_connection() as conn:
        c = conn.cursor()

        for table in tables:
            c.execute(f"PRAGMA table_info({table})")
            existing = [row[1] for row in c.fetchall()]

            if 'created_at' not in existing:
                c.execute(f"""
                    ALTER TABLE {table}
                    ADD COLUMN created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
                """)

            if 'updated_at' not in existing:
                c.execute(f"""
                    ALTER TABLE {table}
                    ADD COLUMN updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
                """)

            if 'is_active' not in existing:
                c.execute(f"""
                    ALTER TABLE {table}
                    ADD COLUMN is_active INTEGER NOT NULL
                    DEFAULT 1
                """)

            trig = f"{table}_updated_at"
            c.execute(f"DROP TRIGGER IF EXISTS {trig}")
            c.execute(f"""
                CREATE TRIGGER {trig}
                AFTER UPDATE ON {table}
                FOR EACH ROW
                BEGIN
                    UPDATE {table}
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = OLD.id;
                END;
            """)

        conn.commit()

if __name__ == '__main__':
    migrate_add_columns()
