import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dealerships (
    id INTEGER PRIMARY KEY,
    name TEXT,
    account_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dealer_selections (
    dealer_id INTEGER PRIMARY KEY,
    selected_logo TEXT,
    selected_panel TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully")