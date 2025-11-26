import requests
import json

# --- Configuration ---
APP_TOKEN = "ApbiUQbkvnyKHOVCHUw1Dh4ic"

# API Endpoints
# --- CORE MASTER DATASETS ---
ACTIVE_STREETS_URL = "https://data.sfgov.org/resource/3psu-pn9h.json"    # Master geometry
BLOCKFACE_GEOMETRY_URL = "https://data.sfgov.org/resource/pep9-66vw.json" # Secondary/Supplemental geometry

# --- SUBSET DATASETS ---
PARKING_REGULATIONS_URL = "https://data.sfgov.org/resource/hi6h-neyh.json" # Regulations
METER_SCHEDULES_URL = "https://data.sfgov.org/resource/6cqg-dxku.json"     # Schedules
PARKING_METERS_URL = "https://data.sfgov.org/resource/8vzz-qzz9.json"       # Meters (link table)
METERED_BLOCKFACES_URL = "https://data.sfgov.org/resource/mk27-a5x2.json"   # Blockfaces with meters
STREET_CLEANING_URL = "https://data.sfgov.org/resource/yhqp-riqs.json"      # Street Cleaning Schedules

# --- ADDITIONAL DATASETS (Nodes, Intersections) ---
STREET_NODES_URL = "https://data.sfgov.org/resource/vd6w-dq8r.json"
INTERSECTIONS_URL = "https://data.sfgov.org/resource/sw2d-qfup.json"
INTERSECTION_PERMUTATIONS_URL = "https://data.sfgov.org/resource/jfxm-zeee.json"

# Number of sample records to fetch
SAMPLE_SIZE = 5

# --- Functions ---

def fetch_data_sample(url: str, token: str, limit: int):
    """Fetches a limited number of records from a Socrata API endpoint."""
    headers = {"X-App-Token": token}
    params = {"$limit": limit}
    
    print(f"--> Fetching sample data from: {url}")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"--> Successfully fetched {len(data)} records.\n")
        return data
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

def analyze_sample(data, dataset_name):
    """Prints the column names and the first record of a dataset sample."""
    if not data:
        print(f"No data to analyze for {dataset_name}.\n")
        return

    print(f"--- Analysis for: {dataset_name} ---")
    
    # Access the first record in the list
    first_record = data[0]
    
    print("Available Columns:")
    print(", ".join(sorted(first_record.keys())))
    print("-" * 20)

    print("First Record Sample:")
    print(json.dumps(first_record, indent=2))
    print("\n" + "="*50 + "\n")

# --- Main Execution ---

if __name__ == "__main__":
    print("Starting data source validation...\n")

    # 1. Active Streets (Master Geometry)
    streets_data = fetch_data_sample(ACTIVE_STREETS_URL, APP_TOKEN, SAMPLE_SIZE)
    if streets_data:
        analyze_sample(streets_data, "Active Streets (3psu-pn9h)")

    # 2. Blockface Geometries (Master/Supplemental Geometry)
    geo_data = fetch_data_sample(BLOCKFACE_GEOMETRY_URL, APP_TOKEN, SAMPLE_SIZE)
    if geo_data:
        analyze_sample(geo_data, "Blockface Geometries (pep9-66vw)")

    # 3. Parking Meters
    meters_data = fetch_data_sample(PARKING_METERS_URL, APP_TOKEN, SAMPLE_SIZE)
    if meters_data:
        analyze_sample(meters_data, "Parking Meters (8vzz-qzz9)")

    # 4. Meter Schedules
    meter_sched_data = fetch_data_sample(METER_SCHEDULES_URL, APP_TOKEN, SAMPLE_SIZE)
    if meter_sched_data:
        analyze_sample(meter_sched_data, "Meter Schedules (6cqg-dxku)")

    # 5. Metered Blockfaces (Subset)
    metered_bf_data = fetch_data_sample(METERED_BLOCKFACES_URL, APP_TOKEN, SAMPLE_SIZE)
    if metered_bf_data:
        analyze_sample(metered_bf_data, "Metered Blockfaces (mk27-a5x2)")

    # 6. Street Cleaning Schedules (Subset)
    cleaning_data = fetch_data_sample(STREET_CLEANING_URL, APP_TOKEN, SAMPLE_SIZE)
    if cleaning_data:
        analyze_sample(cleaning_data, "Street Cleaning Schedules (yhqp-riqs)")

    # 7. Street Nodes
    nodes_data = fetch_data_sample(STREET_NODES_URL, APP_TOKEN, SAMPLE_SIZE)
    if nodes_data:
        analyze_sample(nodes_data, "Street Nodes (vd6w-dq8r)")

    # 8. Intersections
    intersections_data = fetch_data_sample(INTERSECTIONS_URL, APP_TOKEN, SAMPLE_SIZE)
    if intersections_data:
        analyze_sample(intersections_data, "Intersections (sw2d-qfup)")

    # 9. Intersection Permutations
    perms_data = fetch_data_sample(INTERSECTION_PERMUTATIONS_URL, APP_TOKEN, SAMPLE_SIZE)
    if perms_data:
        analyze_sample(perms_data, "Intersection Permutations (jfxm-zeee)")

    print("Validation script finished.")
