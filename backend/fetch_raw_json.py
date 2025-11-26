import requests
import json

def fetch_raw_json(api_url):
    """
    Fetches and prints the raw JSON response from a URL.
    """
    headers = {
        "X-App-Token": "ApbiUQbkvnyKHOVCHUw1Dh4ic"
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        # Pretty-print the JSON content
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {api_url}: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {api_url}. Raw response text:")
        print(response.text)

if __name__ == "__main__":
    # Using the correct metadata endpoint, not the query endpoint
    parking_reg_url = "https://data.sfgov.org/api/views/hi6h-neyh.json"
    fetch_raw_json(parking_reg_url)