import os
import pandas as pd
from sodapy import Socrata
from dotenv import load_dotenv
import pprint
import sys

print("Script started.", flush=True)

try:
    load_dotenv()
    print("Environment loaded.", flush=True)
except Exception as e:
    print(f"Error loading .env: {e}", flush=True)

STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs"
SFMTA_DOMAIN = "data.sfgov.org"

def inspect_sweeping():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("Warning: SFMTA_APP_TOKEN not found in environment.", flush=True)
    
    print(f"Connecting to Socrata...", flush=True)
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print(f"Fetching {STREET_CLEANING_SCHEDULES_ID}...", flush=True)
    # York St CNN is 13766000
    try:
        results = client.get(STREET_CLEANING_SCHEDULES_ID, cnn="13766000", limit=5)
    except Exception as e:
        print(f"Error fetching data: {e}", flush=True)
        return

    print(f"\nFound {len(results)} records.", flush=True)
    
    if results:
        first_record = results[0]
        print("\n--- First Record Structure ---", flush=True)
        pprint.pprint(first_record)
        
        print("\n--- Keys available ---", flush=True)
        print(list(first_record.keys()), flush=True)

        print("\n--- Critical Fields ---", flush=True)
        print(f"cnn: {first_record.get('cnn')}", flush=True)
        print(f"cnnrightleft: {first_record.get('cnnrightleft')}", flush=True)
        print(f"blockside: {first_record.get('blockside')}", flush=True)
    else:
        print("No results found. Trying without filter...", flush=True)
        results = client.get(STREET_CLEANING_SCHEDULES_ID, limit=1)
        if results:
            print(f"Sample record keys: {list(results[0].keys())}", flush=True)

if __name__ == "__main__":
    inspect_sweeping()