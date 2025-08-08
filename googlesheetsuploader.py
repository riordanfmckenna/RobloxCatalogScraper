import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd
import os
from datetime import datetime
import time

# --- Configuration ---
# The name of the Google Sheet workbook you created and shared.
WORKBOOK_NAME = "Roblox Shirts Megabase" 
# The names of the two sheets (tabs) within your workbook.
MASTER_SHEET_NAME = "Items Master List"
HISTORY_SHEET_NAME = "Favorite History (Long)" # Renamed for clarity
# The name of the JSON file created by your scraper script.
JSON_FILENAME = "roblox_classic_shirts.json"
# The JSON key file you downloaded from Google Cloud.
CREDENTIALS_FILENAME = "credentials.json"

def upload_data_to_google_sheet():
    """
    Reads data from a JSON file and updates two Google Sheets:
    1. A master list of all unique items ever found.
    2. A historical log of favorite counts in a "long" format.
    """
    print("Starting advanced upload to Google Sheets...")

    # --- Authenticate with Google Sheets ---
    try:
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILENAME, scope)
        client = gspread.authorize(creds)
        
        workbook = client.open(WORKBOOK_NAME)
        master_sheet = workbook.worksheet(MASTER_SHEET_NAME)
        history_sheet = workbook.worksheet(HISTORY_SHEET_NAME)
        
        print("Successfully authenticated with Google Sheets.")
    except Exception as e:
        print(f"Error: Could not connect to Google Sheets. Please check your configuration.")
        print(f"Error details: {e}")
        return

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
        
        for item in scraped_data:
            for key, value in item.items():
                if isinstance(value, list):
                    item[key] = ", ".join(map(str, value))
            if 'description' in item and isinstance(item['description'], str):
                item['description'] = item['description'].replace('\n', ' ').replace('\r', ' ')

        scraped_df = pd.DataFrame(scraped_data)
        scraped_df = scraped_df.fillna('')
        print(f"Successfully loaded and cleaned {len(scraped_df)} items from '{JSON_FILENAME}'.")
    except Exception as e:
        print(f"Error reading or processing the JSON file: {e}")
        return

    # --- 1. Update the Items Master List ---
    print("\n--- Updating Master List ---")
    try:
        master_records = master_sheet.get_all_records()
        master_df = pd.DataFrame(master_records)
        existing_ids = set(map(str, master_df['id'])) if not master_df.empty else set()
        print(f"Found {len(existing_ids)} existing items in the master list.")

        scraped_df['id'] = scraped_df['id'].astype(str)
        new_items_df = scraped_df[~scraped_df['id'].isin(existing_ids)]

        if not new_items_df.empty:
            print(f"Found {len(new_items_df)} new items to add to the master list.")
            new_items_df['firstUploadTimestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if master_df.empty:
                master_sheet.update([new_items_df.columns.values.tolist()], 'A1')
            
            new_rows = new_items_df.values.tolist()
            chunk_size = 500
            for i in range(0, len(new_rows), chunk_size):
                chunk = new_rows[i:i+chunk_size]
                print(f"  Uploading master list chunk {i//chunk_size + 1}...")
                master_sheet.append_rows(chunk, value_input_option='USER_ENTERED')
                time.sleep(1)
            print("Successfully added new items to the master list.")
        else:
            print("No new items to add to the master list.")

    except Exception as e:
        print(f"An error occurred while updating the master list: {e}")
        return

    # --- 2. Update the Favorite History Sheet (Long Format) ---
    print("\n--- Updating Favorite History (Long Format) ---")
    try:
        now = datetime.now()
        timestamp = now.strftime(f"%Y-%m-%d {now.hour // 2 * 2:02d}:00")

        # Prepare the data for the history sheet
        history_df = scraped_df[['id', 'favoriteCount']].copy()
        history_df['timestamp'] = timestamp
        
        # Check if the history sheet is empty to add headers
        history_headers = history_sheet.row_values(1)
        if not history_headers:
            print("History sheet is empty. Adding headers.")
            history_sheet.update([history_df.columns.values.tolist()], 'A1')

        # Append all new history records in chunks
        history_rows = history_df.values.tolist()
        chunk_size = 5000
        print(f"Appending {len(history_rows)} new history records...")
        for i in range(0, len(history_rows), chunk_size):
            chunk = history_rows[i:i+chunk_size]
            print(f"  Uploading history chunk {i//chunk_size + 1}...")
            history_sheet.append_rows(chunk, value_input_option='USER_ENTERED')
            time.sleep(1)

        print("Successfully appended new history records.")
        print("\nUpload complete!")

    except Exception as e:
        print(f"An error occurred while updating the history sheet: {e}")

if __name__ == "__main__":
    upload_data_to_google_sheet()
