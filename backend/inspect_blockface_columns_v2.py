import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

print("Starting inspection script...")

load_dotenv()
print("Environment loaded.")

try:
    app_token = os.getenv("SFMTA_APP_TOKEN")
    print(f"App Token present: {bool(app_token)}")
    
    client = Socrata("data.sfgov.org", app_token)
    print("Socrata client initialized.")
    
    # Blockfaces with Meters dataset
    dataset_id = "mk27-a5x2" 
    
    print(f"Fetching first 1 records from {dataset_id}...")
    results = client.get(dataset_id, limit=1)
    print(f"Results fetched. Count: {len(results)}")
    
    if results:
        df = pd.DataFrame.from_records(results)
        print("\n--- Columns in Blockface Dataset ---")
        print(df.columns.tolist())
        
        print("\n--- Sample Record ---")
        print(df.iloc[0].to_dict())
    else:
        print("No results returned.")

except Exception as e:
    print(f"An error occurred: {e}")

print("Script finished.")