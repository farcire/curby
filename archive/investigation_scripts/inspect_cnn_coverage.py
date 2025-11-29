import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def inspect_coverage():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    datasets = {
        "Active Streets": "3psu-pn9h",
        "Parking Meters": "8vzz-qzz9",
        "Parking Regulations": "hi6h-neyh"
    }
    
    for name, dataset_id in datasets.items():
        print(f"\n--- {name} ({dataset_id}) ---")
        try:
            # Fetch one record to see columns
            results = client.get(dataset_id, limit=1)
            if results:
                df = pd.DataFrame.from_records(results)
                cols = df.columns.tolist()
                
                # Check for CNN or similar identifiers
                cnn_cols = [c for c in cols if 'cnn' in c.lower() or 'ctrln' in c.lower() or 'street_key' in c.lower()]
                print(f"Potential Join Keys found: {cnn_cols}")
                
                # Print first record's values for these keys
                if cnn_cols:
                    print(f"Sample values: {df.iloc[0][cnn_cols].to_dict()}")
            else:
                print("No records found.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    inspect_coverage()