import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

APP_TOKEN = os.getenv("SFMTA_APP_TOKEN")

def get_socrata_metadata(dataset_id):
    url = f"https://data.sfgov.org/api/views/{dataset_id}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching metadata for {dataset_id}: {response.status_code}")
        return None

def inspect_dataset(dataset_id, name):
    print(f"\n{'='*80}")
    print(f"Inspecting {name} ({dataset_id})")
    print(f"{'='*80}")
    
    metadata = get_socrata_metadata(dataset_id)
    if metadata:
        print(f"Dataset Name: {metadata.get('name')}")
        print(f"Description: {metadata.get('description')}")
        
        print("\nColumns:")
        for col in metadata.get('columns', []):
            print(f"  - {col.get('name')} ({col.get('fieldName')}) [{col.get('dataTypeName')}]")
            
        # Get sample data
        data_url = f"https://data.sfgov.org/resource/{dataset_id}.json?$limit=5"
        if APP_TOKEN:
            headers = {"X-App-Token": APP_TOKEN}
            response = requests.get(data_url, headers=headers)
        else:
            response = requests.get(data_url)
            
        if response.status_code == 200:
            print("\nSample Data (First Record):")
            data = response.json()
            if data:
                print(json.dumps(data[0], indent=2))
        else:
            print(f"Error fetching sample data: {response.status_code}")

if __name__ == "__main__":
    # Inspect Parking Meters (8vzz-qzz9)
    inspect_dataset("8vzz-qzz9", "Parking Meters")
    
    # Inspect Parking Meter Schedules (6cqg-dxku - commonly associated)
    # Note: 6cqg-dxku might be the old one. Let's check "Meter Operating Schedules"
    # Often "v25n-h9k5" or similar. I'll stick to what we suspect first.
    # Actually, let's try to find if there's a separate schedule dataset mentioned in docs
    # Backend README mentions: "Meters (8vzz-qzz9, 6cqg-dxku)"
    inspect_dataset("6cqg-dxku", "Parking Meter Operating Schedules")