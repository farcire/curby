import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()

def inspect_columns():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    # Blockfaces with Meters dataset
    dataset_id = "mk27-a5x2" 
    
    print(f"Fetching first 1 records from {dataset_id}...")
    results = client.get(dataset_id, limit=1)
    df = pd.DataFrame.from_records(results)
    
    print("\n--- Columns in Blockface Dataset ---")
    print(df.columns.tolist())
    
    print("\n--- Sample Record ---")
    print(df.iloc[0].to_dict())

if __name__ == "__main__":
    inspect_columns()