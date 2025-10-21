# -*- coding: utf-8 -*-
"""
Database Migration Script
Add active_email_accounts column to existing database
"""

import sqlite3

db_path = "pc_monitoring.db"

print("Migrating database...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if active_email_accounts column exists
    cursor.execute("PRAGMA table_info(pc_reports)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'active_email_accounts' not in columns:
        print("Adding active_email_accounts column...")
        cursor.execute('''
            ALTER TABLE pc_reports
            ADD COLUMN active_email_accounts TEXT
        ''')
        print("[OK] Column added successfully!")
    else:
        print("active_email_accounts column already exists")

    # Create user_mappings table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            computer_name TEXT NOT NULL UNIQUE,
            windows_user TEXT NOT NULL,
            display_name TEXT NOT NULL,
            last_archive_date TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("[OK] user_mappings table created/verified")

    # Add last_archive_date column if it doesn't exist
    cursor.execute("PRAGMA table_info(user_mappings)")
    mapping_columns = [col[1] for col in cursor.fetchall()]

    if 'last_archive_date' not in mapping_columns:
        print("Adding last_archive_date column to user_mappings...")
        cursor.execute('''
            ALTER TABLE user_mappings
            ADD COLUMN last_archive_date TEXT
        ''')
        print("[OK] last_archive_date column added!")

    # Create index
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_mapping_computer
        ON user_mappings(computer_name)
    ''')
    print("[OK] Index created")

    conn.commit()
    print("\n[SUCCESS] Migration completed successfully!")

except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
