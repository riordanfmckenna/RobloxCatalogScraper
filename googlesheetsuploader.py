import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd
import os
from datetime import datetime

# --- Configuration ---
# The name of the Google Sheet workbook you created and shared.
WORKBOOK_NAME = "Roblox Shirts Megabase" 
# The names of the two sheets (tabs) within your workbook.
MASTER_SHEET_NAME = "Items Master List"
HISTORY_SHEET_NAME = "Favorite History"
# The name of the JSON file created by your scraper script.
JSON_FILENAME = "roblox_classic_shirts.json"
# The JSON key file you downloaded from Google Cloud.
CREDENTIALS_FILENAME = "credentials.json"
# The column number where the 'id' is located in the History sheet (A=1, B=2, etc.)
ID_COLUMN_IN_HISTORY = 4 

def upload_data_to_google_sheet():
    """
    Reads data from a JSON file and updates two Google Sheets:
    1. A master list of all unique items ever found.
    2. A historical log of favorite counts, with a new column for each time interval.
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
            master_sheet.append_rows(new_rows, value_input_option='USER_ENTERED')
            print("Successfully added new items to the master list.")
        else:
            print("No new items to add to the master list.")

    except Exception as e:
        print(f"An error occurred while updating the master list: {e}")
        return

    # --- 2. Update the Favorite History Sheet ---
    print("\n--- Updating Favorite History ---")
    try:
        now = datetime.now()
        timestamp_header = now.strftime(f"%Y-%m-%d {now.hour // 2 * 2:02d}:00")

        history_headers = history_sheet.row_values(1)
        
        if not history_headers:
            # Initialize headers if sheet is completely empty
            history_sheet.update_cell(1, ID_COLUMN_IN_HISTORY, 'id')
            history_headers = [''] * (ID_COLUMN_IN_HISTORY - 1) + ['id']

        if timestamp_header not in history_headers:
            print(f"Adding new timestamp column to history: {timestamp_header}")
            col_num = len(history_headers) + 1
            history_sheet.update_cell(1, col_num, timestamp_header)
            history_headers.append(timestamp_header)
        else:
            print(f"Timestamp column '{timestamp_header}' already exists.")
        
        timestamp_col_index = history_headers.index(timestamp_header) + 1
        
        all_id_column_values = history_sheet.col_values(ID_COLUMN_IN_HISTORY)
        history_item_ids = set(all_id_column_values[1:]) # Skip header

        new_history_items_df = scraped_df[~scraped_df['id'].isin(history_item_ids)]
        if not new_history_items_df.empty:
            print(f"Adding {len(new_history_items_df)} new items to the history sheet.")
            # Create a full row with empty placeholders for trend columns
            new_rows_for_history = []
            for item_id in new_history_items_df['id']:
                row = [''] * (ID_COLUMN_IN_HISTORY - 1) + [item_id]
                new_rows_for_history.append(row)

            history_sheet.append_rows(new_rows_for_history, value_input_option='USER_ENTERED')
            all_id_column_values = history_sheet.col_values(ID_COLUMN_IN_HISTORY)

        cell_updates = []
        print(f"Updating favorite counts for {len(scraped_df)} items under timestamp '{timestamp_header}'...")
        for index, row in scraped_df.iterrows():
            item_id = row['id']
            favorite_count = row['favoriteCount']
            
            try:
                row_index = all_id_column_values.index(str(item_id)) + 1
                cell_updates.append(gspread.Cell(row_index, timestamp_col_index, str(favorite_count)))
            except ValueError:
                print(f"Warning: Could not find row for item ID {item_id}. It may have just been added.")
                continue

        if cell_updates:
            history_sheet.update_cells(cell_updates)
            print("Successfully updated favorite counts.")
        else:
            print("No favorite counts to update.")

        print("\nUpload complete!")

    except Exception as e:
        print(f"An error occurred while updating the history sheet: {e}")

if __name__ == "__main__":
    upload_data_to_google_sheet()
