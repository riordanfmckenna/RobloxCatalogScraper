import requests
import json
import time
import os
import random

# --- Configuration ---
# IMPORTANT: You must get your .ROBLOSECURITY cookie from your browser and paste it here.
# This version REQUIRES a cookie to use the more efficient batch API endpoint.
ROBLOX_COOKIE = '_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_CAEaAhAB.F78DF203F19E4B769C76E46E4B5142EFF2C827B6839F2F3E47516E8EB172A3691019A507B29F7316820124B42F2E1A3D1C3208C8406C2E915043C96FA10AFB8400306E76564F6B21F848AED76A85B45E373B7557CCB9702BF84D03A3DD480D7215A591814EE27A58DB03F45B3C797AF5FEBCB0558E6EFA32266E1666064272622A4F13E68F80302CC67BF4C41282F9BB8C8E3B5A1B9A5AF6058AB19E71A02F053464B56C1FFE986FECC83B92E0162C2603481895E83CDD883AB4BB48FA3A0BBB5D04EE8556956047219329EB95F0BFDFC9F14B11875572BCC373D14224898DD435B0CA8A2706DC38845EDAF833BAB3B23A5C1CD08D8152AE87F62CCE0CB378E7A27B6D7A5B79AF640741A4FB3DC4E19B5FA794A40EE8D45FEF592BC39E4419F58F4C3207E8EE1F0A7EFDF39968A7F3A23EFB361D92CC88E54C0697E1AF85661684A2A342B1672E4C720EF446C1F08EBD6B786BDE2AA77BF1902C97B8E2F88C6E5E7C7C2EF4E7CF9445BABEE37A39C7552A7831DC1B0E38D955806035CD6E28091115B32B26CF15BC5EE5A241F2F442D980DA164C328FB3746AE827D89F9C0BF02CF71BA4458E1009C99B9D9C96EB9F80D28C0B3C9FE375BF01C89B1A6D22CC325A4B42510C39B75F49A28D2B5040FE0C4EFC3D7A5A59A86D3D21B6D468F89C6FD1B3717D6A93AA1C87FEA53D961FC6EDB2C9F0710D083801C0F4116B8C84A133475DD0115206F1A3F3D02B284C7ACA329B92249C8DB35A12E294F0E7A471B7598672879DDB1A3D6FFD6526A5DD4075011B08B9E0564CA241A0FDDAD72FD2BA42B4C6AFC759BDD7724EEFF7C6F52942C7822A94C68D20CE22DD6D96A3ADBD783F38C72DC713BB512F0643368B85A67A7F00FC6C7F16E0097D50ADED10895A167BAA04C7BAD1C7D7C59BBE0440FAA38883D20AE21EB39F1BB0A2E864FC3D9D137776FE9270385A34F02CA8575E5931D500F37BCD88CC644450A5046B9601AE5F58FBB1A082FE0C109300C2CC72DF9A6E279216042F0EC61A4E00DA25A280072D0B8EF5CAF9E209D241D7A1B3A6E8E81BCEBC48386372C03F470F5CAC9D7D0EE6385DBC105FB12211F759216E6F8EF4F561677E7821DED62E11062024C7D7601AC12BB4C1D17E8046079B470F4F3D69BF4911C1B732C4F6D905A26B76B4D583D7586286528B6EF58956F17AD1BEE869F3BCAB05D493A6F11F8EB095BD0599B477FAE2AF1FEADF36F4341528F21258B46D7A3CC09B3F'

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
    'wood', 'fire', 'upon', 'done', 'English', 'road', 'halt', 'ten', 'fly', 'gave', 
    'box', 'finally', 'wait', 'correct', 'oh', 'quickly', 'person', 'became', 'shown', 
    'minutes', 'strong', 'verb', 'stars', 'front', 'feel', 'fact', 'inches', 'street', 
    'decided', 'contain', 'course', 'surface', 'produce', 'building', 'ocean', 'class', 
    'note', 'nothing', 'rest', 'carefully', 'scientists', 'inside', 'wheels', 'stay', 
    'green', 'known', 'island', 'week', 'less', 'machine', 'base', 'ago', 'plain'
]

def fetch_item_details_batch(session, items_to_fetch):
    """
    Fetches full details for a batch of items using the catalog API.
    """
    payload = {"items": items_to_fetch}
    try:
        response = session.post(DETAILS_URL, json=payload)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"      ! Error fetching item details batch: {e}")
        return []
    except json.JSONDecodeError:
        print("      ! Failed to parse JSON from details response.")
        return []

def get_csrf_token(session):
    """
    Gets a CSRF token from Roblox to authenticate POST requests.
    """
    response = session.post(AUTH_URL)
    token = response.headers.get("x-csrf-token")
    if not token:
        raise Exception("Failed to get CSRF token. Check if your .ROBLOSECURITY cookie is valid.")
    return token

def scrape_roblox_catalog():
    """
    Scrapes the Roblox catalog, gets full item details, and saves the results.
    """
    if 'YOUR_COOKIE_HERE' in ROBLOX_COOKIE:
        print("Error: Please replace 'YOUR_COOKIE_HERE' with your actual .ROBLOSECURITY cookie in the script.")
        return

    print("Starting Roblox catalog scraper...")

    session = requests.Session()
    session.cookies['.ROBLOSECURITY'] = ROBLOX_COOKIE
    
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
                response = session.get(BASE_SEARCH_URL, params=request_params)
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
