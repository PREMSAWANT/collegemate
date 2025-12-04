import sqlite3

def update_schema():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    
    try:
        # Add department column
        cursor.execute("ALTER TABLE users ADD COLUMN department TEXT")
        print("Added 'department' column.")
    except sqlite3.OperationalError as e:
        print(f"Error adding 'department' column: {e}")

    try:
        # Add year column
        cursor.execute("ALTER TABLE users ADD COLUMN year TEXT")
        print("Added 'year' column.")
    except sqlite3.OperationalError as e:
        print(f"Error adding 'year' column: {e}")

    conn.commit()
    conn.close()
    print("Database schema update complete.")

if __name__ == "__main__":
    update_schema()
