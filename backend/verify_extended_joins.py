import requests
import json
from typing import List, Dict, Any

# --- Configuration ---
APP_TOKEN = "ApbiUQbkvnyKHOVCHUw1Dh4ic"

# Dataset IDs
ACTIVE_STREETS_ID = "3psu-pn9h"
PARKING_METERS_ID = "8vzz-qzz9"
PARKING_REGULATIONS_ID = "hi6h-neyh"

def fetch_socrata_data(dataset_id: str, limit: int = 5, filters: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """Fetches data from Socrata API."""
    url = f"https://data.sfgov.org/resource/{dataset_id}.json"
    headers = {"X-App-Token": APP_TOKEN}
    params = {"$limit": limit}
    if filters:
        params.update(filters)
    
    print(f"Fetching {dataset_id}...")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {dataset_id}: {e}")
        return []

def verify_meters_to_streets():
    print("\n--- 1. Verifying Meters -> Active Streets (via CNN) ---")
    
    # 1. Fetch a Meter sample that has a street_seg_ctrln_id
    meters = fetch_socrata_data(PARKING_METERS_ID, limit=5, filters={"$where": "street_seg_ctrln_id IS NOT NULL"})
    
    if not meters:
        print("No meters found with street_seg_ctrln_id.")
        return

    target_meter = meters[0]
    cnn_id = target_meter.get("street_seg_ctrln_id")
    print(f"Target Meter Post ID: {target_meter.get('post_id')}")
    print(f"Target CNN (street_seg_ctrln_id): {cnn_id}")

    # 2. Fetch Active Street with matching CNN
    # Note: 'cnn' in Active Streets is often unique
    streets = fetch_socrata_data(ACTIVE_STREETS_ID, limit=1, filters={"cnn": cnn_id})
    
    if streets:
        street = streets[0]
        print(f"✅ MATCH FOUND: Active Street '{street.get('streetname')}'")
        print(f"   CNN: {street.get('cnn')}")
    else:
        print(f"❌ MATCH FAILED: No Active Street found for CNN {cnn_id}")

def investigate_regulations():
    print("\n--- 2. Investigating Parking Regulations ---")
    
    # Fetch a sample to look closer at keys, especially those that might be CNNs
    # Sometimes fields like 'cnn', 'street_key', 'basemap_id' exist but were missed in initial glance
    regulations = fetch_socrata_data(PARKING_REGULATIONS_ID, limit=5)
    
    if not regulations:
        print("No regulations found.")
        return

    first_reg = regulations[0]
    print("Keys in Regulation Record:")
    print(", ".join(sorted(first_reg.keys())))
    
    # Check for potential join candidates
    candidates = ['cnn', 'street_id', 'block_id', 'eid', 'objectid', 'globalid']
    found_candidates = {k: first_reg[k] for k in candidates if k in first_reg}
    
    print("\nPotential Join Keys Found:")
    if found_candidates:
        for k, v in found_candidates.items():
            print(f"  {k}: {v}")
    else:
        print("  No obvious direct join keys (CNN/Street ID) found.")
        print("  Likely requires SPATIAL JOIN (using 'shape').")

if __name__ == "__main__":
    verify_meters_to_streets()
    investigate_regulations()