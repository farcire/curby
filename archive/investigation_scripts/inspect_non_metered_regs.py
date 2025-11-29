import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def inspect_regulations():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    # Non-Metered Parking Regulations dataset (hi6h-neyh)
    dataset_id = "hi6h-neyh"
    
    print(f"Fetching first 1 records from Regulations ({dataset_id})...")
    try:
        results = client.get(dataset_id, limit=1)
        if results:
            df = pd.DataFrame.from_records(results)
            print("\n--- Columns in Regulations Dataset ---")
            print(df.columns.tolist())
            
            print("\n--- Sample Record ---")
            print(df.iloc[0].to_dict())
        else:
            print("No results returned.")
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    inspect_regulations()