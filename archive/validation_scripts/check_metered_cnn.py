import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def check_cnn():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    # Metered Blockfaces
    dataset_id = "mk27-a5x2"
    
    print(f"Fetching record from {dataset_id}...")
    results = client.get(dataset_id, limit=1)
    if results:
        row = results[0]
        print(f"Keys: {list(row.keys())}")
        if 'cnn' in row:
            print(f"✅ CNN found: {row['cnn']}")
        else:
            print("❌ No CNN column found.")
    else:
        print("No results.")

if __name__ == "__main__":
    check_cnn()