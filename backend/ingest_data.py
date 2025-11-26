import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict, Any, Optional

# --- Constants ---
SFMTA_DOMAIN = "data.sfgov.org"

# Dataset IDs (Ordered per instructions)
STREETS_DATASET_ID = "3psu-pn9h"       # 1. Active Streets (Primary Backbone)
STREET_NODES_ID = "vd6w-dq8r"          # 2. Street Nodes
INTERSECTIONS_DATASET_ID = "sw2d-qfup"  # 3. List of Intersections
INTERSECTION_PERMUTATIONS_ID = "jfxm-zeee" # 4. Intersection Permutations
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"    # 5. Blockface Geometries (Link cnn -> blockface_id)
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs" # 6. Street Cleaning Schedules
PARKING_REGULATIONS_ID = "hi6h-neyh"   # 7. Parking Regulations
METERED_BLOCKFACES_ID = "mk27-a5x2"    # 8. Metered Blockfaces (Metadata)
METERS_DATASET_ID = "8vzz-qzz9"        # 9. Parking Meters (Link meters to streets)
METER_SCHEDULES_DATASET_ID = "6cqg-dxku" # 10. Meter Schedules

# --- Data Models ---
Blockface = Dict[str, Any]

def fetch_data_as_dataframe(dataset_id: str, app_token: Optional[str], limit: int = 200000) -> pd.DataFrame:
    """Fetches a dataset and returns it as a pandas DataFrame."""
    print(f"Fetching dataset {dataset_id}...")
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(dataset_id, limit=limit)
        df = pd.DataFrame.from_records(results)
        print(f"Successfully fetched {len(df)} records from {dataset_id}.")
        return df
    except Exception as e:
        print(f"Error fetching dataset {dataset_id}: {e}")
        return pd.DataFrame()

async def main():
    """Main function to orchestrate the data ingestion process."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    # Dictionary to hold all blockfaces, keyed by CNN (Universal ID)
    # Structure: { cnn_id: { id: cnn, geometry: ..., rules: [], ... } }
    blockfaces_map = {}

    # ==========================================
    # 1. Ingest Active Streets (The Backbone) - 3psu-pn9h
    # ==========================================
    print("\n--- 1. Processing Active Streets (The Backbone) ---")
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token)
    
    if not streets_df.empty:
        # Save raw collection
        await db.streets.delete_many({})
        await db.streets.insert_many(streets_df.to_dict('records'))
        print("Saved raw 'streets' collection.")

        # Initialize blockfaces_map
        for _, row in streets_df.iterrows():
            cnn = row.get("cnn")
            if not cnn: continue
            
            # Shape comes as 'line' in this dataset
            geometry = row.get("line")
            
            blockfaces_map[cnn] = {
                "id": cnn,  # CNN is our internal primary key
                "cnn": cnn,
                "streetName": row.get("streetname"),
                "geometry": geometry,
                "blockfaceId": None, # To be filled by pep9 or mk27
                "rules": [],
                "schedules": []
            }
        print(f"Initialized {len(blockfaces_map)} blockfaces from Active Streets.")

    # ==========================================
    # 2. Ingest Street Nodes - vd6w-dq8r
    # ==========================================
    print("\n--- 2. Processing Street Nodes ---")
    nodes_df = fetch_data_as_dataframe(STREET_NODES_ID, app_token)
    if not nodes_df.empty:
        await db.street_nodes.delete_many({})
        await db.street_nodes.insert_many(nodes_df.to_dict('records'))
        print("Saved 'street_nodes'.")

    # ==========================================
    # 3. Ingest Intersections - sw2d-qfup
    # ==========================================
    print("\n--- 3. Processing Intersections ---")
    intersections_df = fetch_data_as_dataframe(INTERSECTIONS_DATASET_ID, app_token)
    if not intersections_df.empty:
        await db.intersections.delete_many({})
        await db.intersections.insert_many(intersections_df.to_dict('records'))
        print("Saved 'intersections'.")

    # ==========================================
    # 4. Ingest Intersection Permutations - jfxm-zeee
    # ==========================================
    print("\n--- 4. Processing Intersection Permutations ---")
    perms_df = fetch_data_as_dataframe(INTERSECTION_PERMUTATIONS_ID, app_token)
    if not perms_df.empty:
        await db.intersection_permutations.delete_many({})
        await db.intersection_permutations.insert_many(perms_df.to_dict('records'))
        print("Saved 'intersection_permutations'.")

    # ==========================================
    # 5. Enrich with Blockface Geometries - pep9-66vw
    # ==========================================
    print("\n--- 5. Linking Blockface IDs (pep9-66vw) ---")
    geo_df = fetch_data_as_dataframe(BLOCKFACE_GEOMETRY_ID, app_token)
    if not geo_df.empty:
        count = 0
        for _, row in geo_df.iterrows():
            cnn = row.get("cnn_id")
            # 'blockface_' seems to be the ID column based on typical Socrata shapefiles, 
            # but let's be safe and check 'globalid' or others if needed.
            # Based on standard mappings, cnn is the join key.
            
            if cnn in blockfaces_map:
                # If pep9 has a geometry ('shape'), we might prefer it or keep 'line' from streets.
                # Usually 'line' from Active Streets is the "centerline". 
                # 'shape' from pep9 might be the specific blockface line.
                # Let's keep Active Streets geometry for now as the "Graph" backbone, 
                # but we could store this as 'blockface_geometry'.
                pass
                # blockfaces_map[cnn]["blockfaceGeometry"] = row.get("shape")
                count += 1
        print(f"Matched {count} records from pep9-66vw to Active Streets.")

    # ==========================================
    # 6. Enrich with Street Cleaning - yhqp-riqs
    # ==========================================
    print("\n--- 6. Enriching with Street Cleaning ---")
    sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    if not sweeping_df.empty:
        await db.street_cleaning_schedules.delete_many({})
        await db.street_cleaning_schedules.insert_many(sweeping_df.to_dict('records'))
        print("Saved 'street_cleaning_schedules' collection.")

        count = 0
        for _, row in sweeping_df.iterrows():
            cnn = row.get("cnn")
            if cnn in blockfaces_map:
                rule = {
                    "type": "street-sweeping",
                    "day": row.get("weekday"),
                    "startTime": row.get("fromhour"),
                    "endTime": row.get("tohour"),
                    "side": row.get("cnnrightleft"), # R or L
                    "description": f"Street Cleaning {row.get('weekday')} {row.get('fromhour')}-{row.get('tohour')}"
                }
                blockfaces_map[cnn]["rules"].append(rule)
                count += 1
        print(f"Added {count} sweeping rules to blockfaces.")

    # ==========================================
    # 7. Ingest Parking Regulations - hi6h-neyh
    # ==========================================
    print("\n--- 7. Processing Parking Regulations ---")
    regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, app_token)
    if not regulations_df.empty:
        await db.parking_regulations.delete_many({})
        # Convert to dicts
        reg_records = regulations_df.to_dict('records')
        
        # Insert raw
        await db.parking_regulations.insert_many(reg_records)
        
        # Create geospatial index for querying
        try:
            await db.parking_regulations.create_index([("geometry", "2dsphere")])
            print("Ensured 2dsphere index on 'parking_regulations'.")
        except Exception as e:
            print(f"Warning: Could not create index on regulations: {e}")
            
        print(f"Saved {len(reg_records)} parking regulations (to be spatially joined at runtime).")

    # ==========================================
    # 8. Metered Blockfaces (Metadata) - mk27-a5x2
    # ==========================================
    print("\n--- 8. Processing Metered Blockfaces (Metadata) ---")
    metered_bf_df = fetch_data_as_dataframe(METERED_BLOCKFACES_ID, app_token)
    # We mostly use this for linking if needed, or supplementary data.
    # Currently relying on Meters dataset for the actual meter info.

    # ==========================================
    # 9 & 10. Meters & Schedules
    # ==========================================
    print("\n--- 9-10. Enriching with Meters & Schedules ---")
    
    # 10. Meter Schedules (Lookup by post_id)
    schedules_df = fetch_data_as_dataframe(METER_SCHEDULES_DATASET_ID, app_token)
    schedules_by_post = {}
    if not schedules_df.empty:
        for _, row in schedules_df.iterrows():
            post_id = row.get("post_id")
            if post_id:
                if post_id not in schedules_by_post:
                    schedules_by_post[post_id] = []
                schedules_by_post[post_id].append({
                    "type": "meter-schedule",
                    "start": row.get("beg_time_dt"),
                    "end": row.get("end_time_dt"),
                    "rate": row.get("rate"),
                    "days": row.get("days_applied") # if available
                })

    # 9. Meters (Link post_id -> cnn)
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    if not meters_df.empty:
        count = 0
        for _, row in meters_df.iterrows():
            cnn = row.get("street_seg_ctrln_id") # This is CNN
            post_id = row.get("post_id")
            
            if cnn in blockfaces_map and post_id:
                # Add meter info
                meter_info = {
                    "type": "meter",
                    "postId": post_id,
                    "active": row.get("active_meter_flag"),
                    "schedules": schedules_by_post.get(post_id, [])
                }
                blockfaces_map[cnn]["schedules"].append(meter_info)
                count += 1
        print(f"Linked {count} meters to blockfaces.")

    # ==========================================
    # Final Save
    # ==========================================
    print("\n--- Saving Unified Blockfaces to MongoDB ---")
    final_blockfaces = list(blockfaces_map.values())
    
    # Filter out invalid geometries just in case
    # (Active Streets usually has good geometries, but safe to check)
    final_blockfaces = [b for b in final_blockfaces if b.get("geometry")]

    if final_blockfaces:
        await db.blockfaces.delete_many({})
        
        # Batch insert
        chunk_size = 1000
        total = len(final_blockfaces)
        for i in range(0, total, chunk_size):
            chunk = final_blockfaces[i:i + chunk_size]
            await db.blockfaces.insert_many(chunk)
            print(f"Inserted batch {i} to {min(i+chunk_size, total)}")
        
        # Create Geospatial Index
        print("Creating geospatial index...")
        await db.blockfaces.create_index([("geometry", "2dsphere")])
        print(f"Successfully saved {total} unified blockfaces.")
    else:
        print("No blockfaces to save!")

    client.close()
    print("\nIngestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())