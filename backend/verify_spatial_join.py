import requests
import json
from typing import List, Dict, Any

# --- Configuration ---
APP_TOKEN = "ApbiUQbkvnyKHOVCHUw1Dh4ic"

# Dataset IDs
PARKING_REGULATIONS_ID = "hi6h-neyh" # The spatial-only dataset
ACTIVE_STREETS_ID = "3psu-pn9h"    # The target for spatial join

def fetch_socrata_data(dataset_id: str, limit: int = 5, filters: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """Fetches data from Socrata API."""
    url = f"https://data.sfgov.org/resource/{dataset_id}.json"
    headers = {"X-App-Token": APP_TOKEN}
    params = {"$limit": limit}
    if filters:
        params.update(filters)
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {dataset_id}: {e}")
        return []

def get_coordinates(shape):
    """Recursively extracts the first coordinate pair found in a shape."""
    if not shape:
        return None
    
    coords = shape.get('coordinates')
    if not coords:
        return None

    # Handle MultiLineString vs LineString vs Point
    while isinstance(coords[0], list) and isinstance(coords[0][0], list):
        coords = coords[0]
    
    # Now coords should be [lon, lat] or [[lon, lat], ...]
    if isinstance(coords[0], list):
        return coords[0] # First point of the line
    return coords # It's a point [lon, lat]

def verify_spatial_overlap():
    print("--- Verifying Spatial Join Feasibility (Regulations <-> Streets) ---\n")

    # 1. Fetch a Regulation Sample (limit to one with a shape)
    regulations = fetch_socrata_data(PARKING_REGULATIONS_ID, limit=1, filters={"$where": "shape IS NOT NULL"})
    
    if not regulations:
        print("No regulations found with geometry.")
        return

    reg = regulations[0]
    reg_desc = reg.get('regulation', 'Unknown Regulation')
    reg_shape = reg.get('shape')
    
    print(f"Target Regulation: {reg_desc}")
    
    # Extract a query point from the regulation geometry
    coords = get_coordinates(reg_shape)
    if not coords:
        print("Could not extract coordinates from regulation.")
        return
        
    lon, lat = coords
    print(f"Regulation Start Point: ({lat}, {lon})")

    # 2. Query Active Streets near this point
    # Socrata SoQL supports `within_circle(location_column, lat, lon, radius)`
    # Note: Active Streets geometry column is usually 'line' or 'shape'
    
    print("\nQuerying Active Streets within 50 meters...")
    
    # We try both 'line' and 'shape' as the geometry column name can vary
    filters = {
        "$where": f"within_circle(line, {lat}, {lon}, 50)" 
    }
    
    streets = fetch_socrata_data(ACTIVE_STREETS_ID, limit=5, filters=filters)
    
    if streets:
        print(f"✅ SPATIAL MATCH FOUND: {len(streets)} streets nearby.")
        for s in streets:
            print(f"   - Street Name: {s.get('streetname')}")
            print(f"   - CNN: {s.get('cnn')}")
    else:
        print("❌ NO SPATIAL MATCH FOUND. Trying wider radius (100m)...")
        filters["$where"] = f"within_circle(line, {lat}, {lon}, 100)"
        streets = fetch_socrata_data(ACTIVE_STREETS_ID, limit=5, filters=filters)
        
        if streets:
            print(f"✅ SPATIAL MATCH FOUND (100m): {len(streets)} streets nearby.")
            for s in streets:
                print(f"   - Street Name: {s.get('streetname')}")
        else:
            print("❌ SPATIAL JOIN FAILED. No streets found near regulation geometry.")

if __name__ == "__main__":
    verify_spatial_overlap()