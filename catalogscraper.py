import requests
import json
import time
import os
import random

# --- Configuration ---
# The script will now pull the .ROBLOSECURITY cookie from your credentials file.
CREDENTIALS_FILENAME = "credentials.json"
BASE_SEARCH_URL = "https://catalog.roblox.com/v1/search/items"
DETAILS_URL = "https://catalog.roblox.com/v1/catalog/items/details"
AUTH_URL = "https://auth.roblox.com/v2/logout" # Used to get a CSRF token
PARAMS = {
    "category": "Clothing",
    "subcategory": "ClassicShirts",
    "sortType": "Favorited",
    "limit": 100,
    "MinPrice": 5,
    "MaxPrice": 5
}
OUTPUT_FILENAME = "roblox_classic_shirts.json"
NUMBER_OF_PAGES_TO_FETCH = 10

# A list of user agents to rotate through to avoid bot detection.
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
]

KEYWORDS = [
    # Aesthetics & "Cores"
    'aesthetic', 'y2k', 'grunge', 'preppy', 'emo', 'vintage', 'streetwear',
    'goth', 'cute', 'kawaii', 'cottagecore', 'fairycore', 'dark academia', 
    'light academia', 'soft girl', 'e-girl', 'baddie', 'kidcore', 'weirdcore', 
    'royalcore', 'angelcore', 'devilcore', 'cyber', 'cybergoth',
    # Styles & Genres
    'punk', 'skater', 'hip hop', 'techwear', 'futuristic', 'sci-fi', 'military', 
    'army', 'tactical', 'uniform', 'school', 'business', 'formal', 'casual', 
    'lounge', 'sporty', 'blokecore', 'suit', 'tuxedo',
    # Clothing Items
    'sweater', 'vest', 't-shirt', 'jeans', 'pants', 'trousers', 'shorts', 'skirt', 
    'dress', 'flannel', 'polo', 'button-up', 'corset', 'blazer', 'cardigan', 
    'tracksuit', 'bomber', 'hoodie', 'jacket', 'oversized', 'cropped',
    # Patterns & Textures
    'plaid', 'checkered', 'striped', 'floral', 'camo', 'camouflage', 'denim', 
    'leather', 'knit', 'silk', 'satin', 'velvet', 'lace', 'argyle', 'polka dot', 
    'flame', 'fire', 'galaxy', 'space',
    # Brands (often used as keywords)
    'adidas', 'nike',
    # Colors
    'black', 'white', 'red', 'blue', 'green', 'pink', 'purple', 'orange', 'yellow', 
    'brown', 'beige', 'pastel', 'neon', 'dark', 'light', 'vibrant', 'monochrome',
    # General & Roblox-Specific
    'old roblox', 'retro', 'future', 'simple', 'basic', 'detailed', 'layered', 
    'korblox', 'headless', 'stitchface', 'slender', 'copy paste', 'meme', 'funny', 
    'matching', 'bloxy', 'style',
    # Manual Additions
    '2010', '2011', '2012', '2013', '1900s', '2000s', 'bypass', 'dahood', 'troll', 
    '10s','20s','30s','40s','50s','60s','70s','80s','90s',' ',
    # Top Something Words
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'I', 'it', 'for', 'not', 
    'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 
    'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 
    'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 
    'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 
    'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 
    'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 
    'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 
    'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 
    'us', 'man', 'find', 'here', 'thing', 'tell', 'many', 'very', 'down', 'through', 
    'should', 'call', 'before', 'long', 'where', 'get', 'much', 'mean', 'old', 'feel', 
    'own', 'life', 'right', 'same', 'still', 'every', 'put', 'live', 'high', 'why', 
    'turn', 'such', 'set', 'part', 'home', 'read', 'hand', 'port', 'large', 'spell', 
    'add', 'end', 'must', 'land', 'house', 'point', 'off', 'play', 'last', 'school', 
    'move', 'what', 'try', 'kind', 'picture', 'again', 'change', 'air', 'away', 
    'animal', 'page', 'letter', 'mother', 'answer', 'found', 'study', 'learn', 'world', 
    'near', 'food', 'between', 'below', 'country', 'plant', 'father', 'keep', 'tree', 
    'never', 'start', 'city', 'earth', 'eye', 'light', 'thought', 'head', 'under', 
    'story', 'saw', 'left', 'dont', 'few', 'while', 'along', 'might', 'close', 
    'something', 'seem', 'next', 'hard', 'open', 'example', 'begin', 'always', 'those', 
    'both', 'paper', 'together', 'got', 'group', 'often', 'run', 'important', 'until', 
    'children', 'side', 'feet', 'car', 'mile', 'night', 'walk', 'white', 'sea', 'began', 
    'grow', 'took', 'river', 'four', 'carry', 'state', 'once', 'book', 'hear', 'stop', 
    'without', 'second', 'later', 'miss', 'idea', 'enough', 'eat', 'face', 'watch', 
    'far', 'Indian', 'really', 'almost', 'let', 'above', 'girl', 'sometimes', 'mountain', 
    'cut', 'young', 'talk', 'soon', 'list', 'song', 'being', 'leave', 'family', 'body', 
    'music', 'color', 'stand', 'sun', 'question', 'fish', 'area', 'mark', 'dog', 'horse', 
    'birds', 'problem', 'complete', 'room', 'knew', 'since', 'ever', 'piece', 'told', 
    'usually', 'didnt', 'friends', 'easy', 'heard', 'order', 'red', 'door', 'sure', 
    'become', 'top', 'ship', 'across', 'today', 'during', 'short', 'better', 'best', 
    'however', 'low', 'hours', 'black', 'products', 'happened', 'whole', 'measure', 
    'remember', 'early', 'waves', 'reached', 'listen', 'wind', 'rock', 'space', 
    'covered', 'fast', 'several', 'hold', 'himself', 'toward', 'five', 'step', 
    'morning', 'passed', 'vowel', 'true', 'hundred', 'against', 'pattern', 'numeral', 
    'table', 'north', 'slowly', 'money', 'map', 'farm', 'pulled', 'draw', 'voice', 
    'seen', 'cold', 'cried', 'plan', 'notice', 'south', 'sing', 'war', 'ground', 
    'fall', 'king', 'town', 'ill', 'unit', 'figure', 'certain', 'field', 'travel', 
    'wood', 'fire', '2on', 'done', 'English', 'road', 'halt', 'ten', 'fly', 'gave', 
    'box', 'finally', 'wait', 'correct', 'oh', 'quickly', 'person', 'became', 's  n', 
    'minutes', 'strong', 'verb', 'stars', 'front', 'feel', 'fact', 'inches', 'street', 
    'decided', 'contain', 'course', 'surface', 'produce', 'building', 'ocean', 'class', 
    'note', 'nothing', 'rest', 'carefully', 'scientists', 'inside', 'wheels', 'stay', 
    'green', 'known', 'island', 'week', 'less', 'machine', 'base', 'ago', 'plain'
]

def get_csrf_token(session):
    """
    Gets a CSRF token from Roblox to authenticate POST requests.
    """
    response = session.post(AUTH_URL, timeout=15)
    token = response.headers.get("x-csrf-token")
    if not token:
        raise Exception("Failed to get CSRF token. Check if your .ROBLOSECURITY cookie is valid.")
    return token

def fetch_item_details_batch(session, items_to_fetch):
    """
    Fetches full details for a batch of items, with a retry mechanism for expired CSRF tokens.
    """
    retries = 2 # Try once, then retry once more after a token refresh
    for attempt in range(retries):
        try:
            payload = {"items": items_to_fetch}
            response = session.post(DETAILS_URL, json=payload, timeout=15)
            response.raise_for_status()
            return response.json().get('data', []) # Success, return data
        except requests.exceptions.HTTPError as e:
            # If we get a 403 Forbidden error, it's likely a stale CSRF token.
            if e.response.status_code == 403 and attempt < retries - 1:
                print("      ! 403 Forbidden error detected. Refreshing CSRF token and retrying...")
                try:
                    new_token = get_csrf_token(session)
                    session.headers["X-Csrf-Token"] = new_token
                    print("      > New CSRF token obtained. Retrying request...")
                    time.sleep(2) # Wait a moment before retrying
                    continue # Go to the next attempt in the loop
                except Exception as token_e:
                    print(f"      ! Failed to refresh CSRF token: {token_e}")
                    break # Stop trying if we can't get a new token
            else:
                print(f"      ! Error fetching item details batch: {e}")
                break # Break on other errors or after the last retry
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"      ! Non-HTTP error fetching item details: {e}")
            break
    return [] # Return empty list if all attempts fail


def scrape_roblox_catalog():
    """
    Scrapes the Roblox catalog, gets full item details, and saves the results.
    """
    # --- Read Roblox Cookie from credentials ---
    try:
        with open(CREDENTIALS_FILENAME, 'r') as f:
            creds_data = json.load(f)
            roblox_cookie = creds_data.get('roblox_cookie')
            if not roblox_cookie:
                print(f"Error: 'roblox_cookie' not found in {CREDENTIALS_FILENAME}.")
                return
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading Roblox cookie from {CREDENTIALS_FILENAME}: {e}")
        return

    print("Starting Roblox catalog scraper...")

    session = requests.Session()
    session.cookies['.ROBLOSECURITY'] = roblox_cookie
    
    try:
        print("  > Fetching initial CSRF token...")
        csrf_token = get_csrf_token(session)
        session.headers["X-Csrf-Token"] = csrf_token
        print("  > Successfully got initial CSRF token.")
    except Exception as e:
        print(f"  ! Could not get initial CSRF token. Exiting. Error: {e}")
        return

    existing_items = []
    existing_item_ids = set()
    if os.path.exists(OUTPUT_FILENAME):
        try:
            with open(OUTPUT_FILENAME, 'r', encoding='utf-8') as f:
                existing_items = json.load(f)
                for item in existing_items:
                    if 'id' in item:
                        existing_item_ids.add(item['id'])
            print(f"Loaded {len(existing_items)} existing items from '{OUTPUT_FILENAME}'.")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read existing file '{OUTPUT_FILENAME}'. Starting fresh. Error: {e}")
            existing_items = []
            existing_item_ids = set()

    newly_fetched_items = []
    
    for keyword in KEYWORDS:
        session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        print(f"\n--- Scraping for keyword: '{keyword}' (Using User-Agent: {session.headers['User-Agent']}) ---")
        
        next_page_cursor = None
        
        for i in range(NUMBER_OF_PAGES_TO_FETCH):
            print(f"  Fetching page {i + 1}/{NUMBER_OF_PAGES_TO_FETCH} for this keyword...")
            
            request_params = PARAMS.copy()
            request_params['Keyword'] = keyword
            if next_page_cursor:
                request_params['cursor'] = next_page_cursor

            try:
                response = session.get(BASE_SEARCH_URL, params=request_params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                basic_items_on_page = data.get("data", [])
                if not basic_items_on_page:
                    print("    > No more items found for this keyword.")
                    break

                new_items_to_detail = [item for item in basic_items_on_page if item.get('id') not in existing_item_ids]
                
                if new_items_to_detail:
                    print(f"    > Found {len(new_items_to_detail)} new items. Fetching full details in a batch...")
                    detailed_items = fetch_item_details_batch(session, new_items_to_detail)
                    
                    if detailed_items:
                        for detailed_item in detailed_items:
                            detailed_item['searchedKeyword'] = keyword
                            newly_fetched_items.append(detailed_item)
                            existing_item_ids.add(detailed_item['id'])
                        
                        print(f"    > Successfully added {len(detailed_items)} detailed items.")
                else:
                    print("    > No new items on this page. All items already in our list.")

                next_page_cursor = data.get("nextPageCursor")
                if not next_page_cursor:
                    print("    > Reached the end of results for this keyword.")
                    break
            
            except requests.exceptions.RequestException as e:
                print(f"    > An error occurred during the request: {e}")
                break 
            except json.JSONDecodeError:
                print("    > Failed to parse JSON from response.")
                break

            time.sleep(1)
        
        print(f"--- Finished keyword '{keyword}'. Waiting 5 seconds before next keyword. ---")
        time.sleep(5)

    if newly_fetched_items:
        print(f"\nScraping complete. Added {len(newly_fetched_items)} new items.")
        all_items = existing_items + newly_fetched_items
        try:
            with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
                json.dump(all_items, f, indent=4, ensure_ascii=False)
            print(f"File saved successfully! Total items in file: {len(all_items)}")
        except IOError as e:
            print(f"An error occurred while writing to the file: {e}")
    else:
        print("\nScraping complete. No new items were found to add.")

if __name__ == "__main__":
    scrape_roblox_catalog()
