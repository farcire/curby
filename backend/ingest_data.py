import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict, Any, Optional

# --- Constants ---
SFMTA_DOMAIN = "data.sfgov.org"
BLOCKFACES_DATASET_ID = "mk27-a5x2"      # Primary source: Blockfaces with Meters
METERS_DATASET_ID = "8vzz-qzz9"          # Parking Meters (links schedules to blockfaces)
METER_SCHEDULES_DATASET_ID = "6cqg-dxku"  # Meter operating schedules
INTERSECTIONS_DATASET_ID = "sw2d-qfup"  # List of Intersections
STREETS_DATASET_ID = "3psu-pn9h"       # Streets - Active and Retired
STREET_NODES_ID = "vd6w-dq8r"          # Street Nodes
INTERSECTION_PERMUTATIONS_ID = "jfxm-zeee" # Intersections by Each Cross Street Permutation
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs" # Street Cleaning Schedules

# --- Data Models ---
Blockface = Dict[str, Any]
Intersection = Dict[str, Any]
Street = Dict[str, Any]
StreetNode = Dict[str, Any]
IntersectionPermutation = Dict[str, Any]

def fetch_data_as_dataframe(dataset_id: str, app_token: Optional[str]) -> pd.DataFrame:
    """Fetches a dataset and returns it as a pandas DataFrame."""
    print(f"Fetching dataset {dataset_id}...")
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(dataset_id, limit=200000)
        df = pd.DataFrame.from_records(results)
        print(f"Raw record count for {dataset_id}: {len(results)}")
        print(f"Successfully fetched {len(df)} records from {dataset_id}.")
        return df
    except Exception as e:
        print(f"Error fetching dataset {dataset_id}: {e}")
        return pd.DataFrame()

def process_blockfaces(blockfaces_df: pd.DataFrame, meters_df: pd.DataFrame, meter_schedules_df: pd.DataFrame) -> List[Blockface]:
    """Processes raw dataframes to create a list of Blockface documents."""
    print("Processing and combining blockface, meter, and schedule data...")
    if blockfaces_df.empty:
        print("Blockfaces dataframe is empty. Cannot create blockfaces.")
        return []

    # 1. Create a mapping of meter schedules by post_id
    schedules_by_post_id = {}
    if not meter_schedules_df.empty:
        print(f"Processing {len(meter_schedules_df)} meter schedule records...")
        for _, sched_row in meter_schedules_df.iterrows():
            post_id = sched_row.get("post_id")
            if post_id:
                schedule = {
                    "beginTime": sched_row.get("beg_time_dt"),
                    "endTime": sched_row.get("end_time_dt"),
                    "rate": sched_row.get("rate"),
                    "rateQualifier": sched_row.get("rate_qualifier"),
                    "rateUnit": sched_row.get("rate_unit"),
                }
                schedule = {k: v for k, v in schedule.items() if v is not None}
                if post_id not in schedules_by_post_id:
                    schedules_by_post_id[post_id] = []
                schedules_by_post_id[post_id].append(schedule)
        print(f"Created schedule mapping for {len(schedules_by_post_id)} post_ids.")

    # 2. Create a mapping of blockface_id to a list of post_ids
    posts_by_blockface_id = {}
    if not meters_df.empty:
        print(f"Processing {len(meters_df)} meter records...")
        for _, meter_row in meters_df.iterrows():
            blockface_id = meter_row.get("blockface_id")
            post_id = meter_row.get("post_id")
            if blockface_id and post_id:
                if blockface_id not in posts_by_blockface_id:
                    posts_by_blockface_id[blockface_id] = []
                posts_by_blockface_id[blockface_id].append(post_id)
        print(f"Created post_id mapping for {len(posts_by_blockface_id)} blockface_ids.")

    # 3. Create blockface documents and attach schedules
    blockfaces = []
    for _, row in blockfaces_df.iterrows():
        blockface_id = row.get("blockface_id")
        geometry = row.get("shape")
        
        # Skip if geometry is missing or invalid (e.g. NaN)
        if not isinstance(geometry, dict) or "coordinates" not in geometry:
            continue

        blockface = {
            "id": blockface_id,
            "streetName": row.get("street_name"),
            "fromStreet": row.get("fm_addr_no"), # Using address numbers as a proxy
            "toStreet": row.get("to_addr_no"),
            "side": row.get("blockface_orientation"),
            "geometry": geometry,
            "rules": [],  # Regulations are unlinked for now
            "schedules": []
        }

        # Attach schedules if available for this blockface_id
        if blockface_id in posts_by_blockface_id:
            post_ids = posts_by_blockface_id[blockface_id]
            for post_id in post_ids:
                if post_id in schedules_by_post_id:
                    blockface["schedules"].extend(schedules_by_post_id[post_id])
        
        blockface = {k: v for k, v in blockface.items() if v is not None}
        blockfaces.append(blockface)

    print(f"Successfully created {len(blockfaces)} blockface documents.")
    return blockfaces

def process_intersections(df: pd.DataFrame) -> List[Intersection]:
    """Processes the raw intersections dataframe."""
    if df.empty:
        print("Intersections dataframe is empty. Cannot process.")
        return []
    
    print("Processing intersections data...")
    print("Intersection columns available:", df.columns.tolist())
    
    # Basic processing: convert to list of dicts
    records = df.to_dict('records')
    print(f"Processed {len(records)} intersection records.")
    return records

def process_streets(df: pd.DataFrame) -> List[Street]:
    """Processes the raw streets dataframe."""
    if df.empty:
        print("Streets dataframe is empty. Cannot process.")
        return []
    
    print("Processing streets data...")
    print("Street columns available:", df.columns.tolist())
    
    # Filter for active streets only
    active_streets_df = df[df['active'] == True]
    print(f"Filtered down to {len(active_streets_df)} active street records.")

    # Basic processing: convert to list of dicts
    records = active_streets_df.to_dict('records')
    print(f"Processed {len(records)} active street records.")
    return records

def process_street_nodes(df: pd.DataFrame) -> List[StreetNode]:
    """Processes the raw street nodes dataframe."""
    if df.empty:
        print("Street nodes dataframe is empty. Cannot process.")
        return []
    
    print("Processing street nodes data...")
    print("Street node columns available:", df.columns.tolist())
    
    records = df.to_dict('records')
    print(f"Processed {len(records)} street node records.")
    return records

def process_intersection_permutations(df: pd.DataFrame) -> List[IntersectionPermutation]:
    """Processes the raw intersection permutations dataframe."""
    if df.empty:
        print("Intersection permutations dataframe is empty. Cannot process.")
        return []
    
    print("Processing intersection permutations data...")
    print("Intersection permutation columns available:", df.columns.tolist())
    
    records = df.to_dict('records')
    print(f"Processed {len(records)} intersection permutation records.")
    return records

def process_street_cleaning(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Processes the raw street cleaning schedules dataframe."""
    if df.empty:
        print("Street cleaning schedules dataframe is empty. Cannot process.")
        return []
    
    print("Processing street cleaning schedules data...")
    print("Street cleaning columns available:", df.columns.tolist())
    
    records = df.to_dict('records')
    print(f"Processed {len(records)} street cleaning schedule records.")
    return records
 
async def main():
    """Main function to orchestrate the data ingestion process."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")

    if not app_token:
        print("Warning: SFMTA_APP_TOKEN not found. Proceeding with unauthenticated request.")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    # --- Connect to MongoDB ---
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    # --- Ingest Metered Parking (Blockfaces) ---
    blockfaces_df = fetch_data_as_dataframe(BLOCKFACES_DATASET_ID, app_token)
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    meter_schedules_df = fetch_data_as_dataframe(METER_SCHEDULES_DATASET_ID, app_token)
    blockfaces = process_blockfaces(blockfaces_df, meters_df, meter_schedules_df)
    if blockfaces:
        print(f"\nProceeding to insert {len(blockfaces)} blockfaces into MongoDB...")
        blockface_collection = db["blockfaces"]
        await blockface_collection.delete_many({})
        print("Cleared existing 'blockfaces' collection.")
        await blockface_collection.insert_many(blockfaces)
        print(f"Successfully inserted {len(blockfaces)} documents.")
    else:
        print("\nNo blockfaces were processed. Ingestion did not write to database.")

    # --- Ingest Intersections ---
    intersections_df = fetch_data_as_dataframe(INTERSECTIONS_DATASET_ID, app_token)
    intersections = process_intersections(intersections_df)
    if intersections:
        print(f"\nProceeding to insert {len(intersections)} intersections into MongoDB...")
        intersections_collection = db["intersections"]
        await intersections_collection.delete_many({})
        print("Cleared existing 'intersections' collection.")
        await intersections_collection.insert_many(intersections)
        print(f"Successfully inserted {len(intersections)} documents.")
    else:
        print("\nNo intersections were processed. Ingestion did not write to database.")

    # --- Ingest Streets ---
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token)
    streets = process_streets(streets_df)
    if streets:
        print(f"\nProceeding to insert {len(streets)} streets into MongoDB...")
        streets_collection = db["streets"]
        await streets_collection.delete_many({})
        print("Cleared existing 'streets' collection.")
        await streets_collection.insert_many(streets)
        print(f"Successfully inserted {len(streets)} documents.")
    else:
        print("\nNo streets were processed. Ingestion did not write to database.")

    # --- Ingest Street Nodes ---
    street_nodes_df = fetch_data_as_dataframe(STREET_NODES_ID, app_token)
    street_nodes = process_street_nodes(street_nodes_df)
    if street_nodes:
        print(f"\nProceeding to insert {len(street_nodes)} street nodes into MongoDB...")
        street_nodes_collection = db["street_nodes"]
        await street_nodes_collection.delete_many({})
        print("Cleared existing 'street_nodes' collection.")
        await street_nodes_collection.insert_many(street_nodes)
        print(f"Successfully inserted {len(street_nodes)} documents.")
    else:
        print("\nNo street nodes were processed. Ingestion did not write to database.")

    # --- Ingest Intersection Permutations ---
    intersection_permutations_df = fetch_data_as_dataframe(INTERSECTION_PERMUTATIONS_ID, app_token)
    intersection_permutations = process_intersection_permutations(intersection_permutations_df)
    if intersection_permutations:
        print(f"\nProceeding to insert {len(intersection_permutations)} intersection permutations into MongoDB...")
        intersection_permutations_collection = db["intersection_permutations"]
        await intersection_permutations_collection.delete_many({})
        print("Cleared existing 'intersection_permutations' collection.")
        await intersection_permutations_collection.insert_many(intersection_permutations)
        print(f"Successfully inserted {len(intersection_permutations)} documents.")
    else:
        print("\nNo intersection permutations were processed. Ingestion did not write to database.")

    # --- Ingest Street Cleaning Schedules ---
    street_cleaning_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    street_cleaning_schedules = process_street_cleaning(street_cleaning_df)
    if street_cleaning_schedules:
        print(f"\nProceeding to insert {len(street_cleaning_schedules)} street cleaning schedules into MongoDB...")
        street_cleaning_collection = db["street_cleaning_schedules"]
        await street_cleaning_collection.delete_many({})
        print("Cleared existing 'street_cleaning_schedules' collection.")
        await street_cleaning_collection.insert_many(street_cleaning_schedules)
        print(f"Successfully inserted {len(street_cleaning_schedules)} documents.")
    else:
        print("\nNo street cleaning schedules were processed. Ingestion did not write to database.")
 
    client.close()
    print("\nData ingestion process finished.")
 
if __name__ == "__main__":
    asyncio.run(main())