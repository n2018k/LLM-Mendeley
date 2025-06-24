import sqlite3, sys

def delete_entry_by_title(title, db_path="pdf_database.db"):
    """Deletes entries with a specific title."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM pdfs WHERE title = ?", (title,))
        conn.commit()
        print(f"Entries with title '{title}' deleted successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

# Example usage:
delete_entry_by_title(sys.argv[1])

