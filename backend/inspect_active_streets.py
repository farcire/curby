import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def inspect_active_streets():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("Error: SFMTA_APP_TOKEN not found.")
        return

    client = Socrata("data.sfgov.org", app_token)
    
    # Active Streets dataset
    dataset_id = "3psu-pn9h"
    
    print(f"Fetching first 1 records from Active Streets ({dataset_id})...")
    try:
        results = client.get(dataset_id, limit=1)
        if results:
            df = pd.DataFrame.from_records(results)
            print("\n--- Columns in Active Streets Dataset ---")
            print(df.columns.tolist())
            
            print("\n--- Sample Record ---")
            print(df.iloc[0].to_dict())
        else:
            print("No results returned.")
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    inspect_active_streets()