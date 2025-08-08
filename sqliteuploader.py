import sqlite3
import json
import os
from datetime import datetime, timedelta

# --- Configuration ---
# The name of the SQLite database file that will be created.
DB_FILENAME = "roblox_data.db"
# The name of the JSON file created by your scraper script.
JSON_FILENAME = "roblox_classic_shirts.json"

def create_database_tables(cursor):
    """
    Creates the necessary tables in the SQLite database if they don't already exist.
    """
    # Create the master list of items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price INTEGER,
            creatorName TEXT,
            creatorTargetId INTEGER,
            searchedKeyword TEXT,
            firstUploadTimestamp TEXT
        )
    ''')
    # Create the historical log of favorite counts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorite_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            favoriteCount INTEGER,
            timestamp TEXT,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
    ''')

def upload_data_to_sqlite():
    """
    Reads data from a JSON file and updates two tables in an SQLite database:
    1. A master list of all unique items ever found.
    2. A historical log of favorite counts in a "long" format.
    """
    print("Starting upload to SQLite database...")

    # --- Read and Clean the Scraped Data ---
    if not os.path.exists(JSON_FILENAME):
        print(f"Error: The file '{JSON_FILENAME}' was not found. Please run the scraper script first.")
        return
        
    try:
        with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        if not scraped_data:
            print("The JSON file is empty. Nothing to upload.")
            return
        
        # Clean the data before processing
        for item in scraped_data:
            for key, value in item.items():
                if isinstance(value, list):
                    item[key] = ", ".join(map(str, value))
            if 'description' in item and isinstance(item['description'], str):
                item['description'] = item['description'].replace('\n', ' ').replace('\r', ' ')

        print(f"Successfully loaded and cleaned {len(scraped_data)} items from '{JSON_FILENAME}'.")
    except Exception as e:
        print(f"Error reading or processing the JSON file: {e}")
        return

    # --- Connect to the Database and Create Tables ---
    try:
        conn = sqlite3.connect(DB_FILENAME)
        cursor = conn.cursor()
        create_database_tables(cursor)
        print(f"Successfully connected to database '{DB_FILENAME}'.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    # --- 1. Update the Items Master List ---
    print("\n--- Updating Master List ---")
    try:
        # Get a set of all existing IDs from the database for a fast lookup
        cursor.execute("SELECT id FROM items")
        existing_ids = {str(row[0]) for row in cursor.fetchall()}
        print(f"Found {len(existing_ids)} existing items in the master list.")

        new_items = [item for item in scraped_data if str(item.get('id')) not in existing_ids]

        if new_items:
            print(f"Found {len(new_items)} new items to add to the master list.")
            upload_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            items_to_insert = []
            for item in new_items:
                items_to_insert.append((
                    item.get('id'),
                    item.get('name'),
                    item.get('description'),
                    item.get('price'),
                    item.get('creatorName'),
                    item.get('creatorTargetId'),
                    item.get('searchedKeyword'),
                    upload_timestamp
                ))
            
            cursor.executemany('''
                INSERT INTO items (id, name, description, price, creatorName, creatorTargetId, searchedKeyword, firstUploadTimestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', items_to_insert)
            
            conn.commit()
            print(f"Successfully added {len(new_items)} new items to the master list.")
        else:
            print("No new items to add to the master list.")

    except Exception as e:
        print(f"An error occurred while updating the master list: {e}")
        conn.close()
        return

    # --- 2. Update the Favorite History (Long Format) ---
    print("\n--- Updating Favorite History ---")
    try:
        now = datetime.now()
        # Generate a timestamp rounded to the nearest 4 hours
        timestamp = (now - timedelta(hours=now.hour % 4)).strftime("%Y-%m-%d %H:00")

        history_to_insert = []
        for item in scraped_data:
            history_to_insert.append((
                item.get('id'),
                item.get('favoriteCount'),
                timestamp
            ))
            
        cursor.executemany('''
            INSERT INTO favorite_history (item_id, favoriteCount, timestamp)
            VALUES (?, ?, ?)
        ''', history_to_insert)
        
        conn.commit()
        print(f"Successfully inserted {len(history_to_insert)} new history records for timestamp '{timestamp}'.")

    except Exception as e:
        print(f"An error occurred while updating the history sheet: {e}")
    finally:
        # Always close the connection
        conn.close()
        print("\nDatabase connection closed. Upload complete!")

if __name__ == "__main__":
    upload_data_to_sqlite()
