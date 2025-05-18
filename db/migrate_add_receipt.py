import sqlite3

DB_PATH = 'system.db'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(sales)")
    existing = [row[1] for row in cur.fetchall()]
    if 'receipt_no' not in existing:
        cur.execute("ALTER TABLE sales ADD COLUMN receipt_no TEXT DEFAULT ''")
        print("→ Added column receipt_no")
    else:
        print("→ Column receipt_no already exists")

    if 'notes' not in existing:
        cur.execute("ALTER TABLE sales ADD COLUMN notes TEXT DEFAULT ''")
        print("→ Added column notes")
    else:
        print("→ Column notes already exists")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
