import requests
import json

def inspect_schema(api_url):
    """
    Fetches and prints the schema of a Socrata dataset.
    """
    try:
        # The .json endpoint for views provides metadata including columns
        metadata_url = api_url.replace('/query.json', '.json')
        response = requests.get(metadata_url)
        response.raise_for_status()
        data = response.json()
        
        if 'columns' in data:
            print(f"Schema for {api_url}:\n")
            for column in data['columns']:
                print(f"  - {column['name']} ({column.get('dataTypeName', 'N/A')})")
        else:
            print(f"Could not find schema information in the response from {metadata_url}")
            print("Response snippet:", json.dumps(data, indent=2)[:500])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {metadata_url}: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {metadata_url}")

if __name__ == "__main__":
    parking_reg_url = "https://data.sfgov.org/api/v3/views/hi6h-neyh/query.json"
    rpp_parcels_url = "https://data.sfgov.org/api/v3/views/i886-hxz9/query.json"

    print("--- Inspecting Parking Regulation Schema ---")
    inspect_schema(parking_reg_url)
    print("\n" + "="*50 + "\n")
    print("--- Inspecting RPP Parcels Schema ---")
    inspect_schema(rpp_parcels_url)