"""
Find ALL meters that failed to match during ingestion.
This replicates the exact matching logic from ingest_data_cnn_segments.py
"""
import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
import re

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METERS_DATASET_ID = "8vzz-qzz9"
METERED_BLOCKFACES_ID = "mk27-a5x2"

def fetch_data_as_dataframe(dataset_id: str, app_token: str, limit: int = 200000) -> pd.DataFrame:
    """Fetches a dataset and returns it as a pandas DataFrame."""
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(dataset_id, limit=limit)
        df = pd.DataFrame.from_records(results)
        return df
    except Exception as e:
        print(f"Error fetching dataset {dataset_id}: {e}")
        return pd.DataFrame()

async def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")
    
    # Connect to MongoDB to get segments
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    # Load all segments
    print("Loading street segments from database...")
    segments_cursor = db.street_segments.find({})
    all_segments = await segments_cursor.to_list(length=None)
    print(f"Loaded {len(all_segments)} segments")
    
    # Load metered blockfaces
    print("\nLoading metered blockfaces...")
    metered_blockfaces_df = fetch_data_as_dataframe(METERED_BLOCKFACES_ID, app_token)
    
    blockface_to_cnn_side = {}
    if not metered_blockfaces_df.empty:
        for _, bf_row in metered_blockfaces_df.iterrows():
            blockface_id = bf_row.get("blockface_id")
            side = bf_row.get("str_seg_orientation")
            
            if blockface_id and side:
                blockface_to_cnn_side[str(blockface_id)] = {
                    "side": side,
                    "street_name": bf_row.get("street_name"),
                    "from_addr": bf_row.get("fm_addr_no"),
                    "to_addr": bf_row.get("to_addr_no")
                }
    
    print(f"Loaded {len(blockface_to_cnn_side)} metered blockface mappings")
    
    # Load meters
    print("\nLoading meters...")
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    print(f"Loaded {len(meters_df)} meters")
    
    # Replicate exact matching logic from ingestion
    unmatched_meters = []
    match_stats = {
        "blockface_match": 0,
        "cnn_fallback": 0,
        "failed": 0,
        "total_meters": len(meters_df)
    }
    
    for idx, meter_row in meters_df.iterrows():
        cnn = meter_row.get("street_seg_ctrln_id")
        post_id = meter_row.get("post_id")
        blockface_id = meter_row.get("blockface_id")
        
        # FAILURE POINT 1: Missing CNN or post_id
        if not cnn or not post_id:
            match_stats["failed"] += 1
            unmatched_meters.append({
                "post_id": post_id,
                "cnn": cnn,
                "blockface_id": blockface_id,
                "street_name": meter_row.get("street_name"),
                "street_num": meter_row.get("street_num"),
                "latitude": meter_row.get("latitude"),
                "longitude": meter_row.get("longitude"),
                "reason": "Missing CNN or post_id",
                "failure_point": "Initial validation"
            })
            continue
        
        matched_segment = None
        match_method = None
        
        # METHOD 1: Blockface ID Match
        if blockface_id and str(blockface_id) in blockface_to_cnn_side:
            bf_info = blockface_to_cnn_side[str(blockface_id)]
            target_side = bf_info["side"]
            
            # Find segment with matching CNN and side
            for segment in all_segments:
                if segment["cnn"] == cnn and segment["side"] == target_side:
                    matched_segment = segment
                    match_method = "blockface_match"
                    break
        
        # METHOD 2: CNN-only fallback
        if not matched_segment:
            street_num = meter_row.get("street_num")
            
            if street_num:
                try:
                    meter_address = int(re.sub(r'\D', '', str(street_num)))
                    
                    for segment in all_segments:
                        if segment["cnn"] != cnn:
                            continue
                        
                        from_addr = segment.get("fromAddress")
                        to_addr = segment.get("toAddress")
                        
                        if from_addr and to_addr:
                            try:
                                from_num = int(re.sub(r'\D', '', str(from_addr)))
                                to_num = int(re.sub(r'\D', '', str(to_addr)))
                                
                                if from_num <= meter_address <= to_num:
                                    matched_segment = segment
                                    match_method = "cnn_fallback"
                                    break
                            except:
                                continue
                except:
                    pass
        
        # FAILURE POINT 2: No match found
        if matched_segment:
            match_stats[match_method] += 1
        else:
            match_stats["failed"] += 1
            
            # Determine specific reason
            reason = "Unknown"
            if blockface_id and str(blockface_id) not in blockface_to_cnn_side:
                reason = "Blockface ID not in metered blockfaces dataset"
            elif not blockface_id:
                reason = "No blockface_id and address fallback failed"
            else:
                reason = "Blockface ID exists but no matching segment found"
            
            unmatched_meters.append({
                "post_id": post_id,
                "cnn": cnn,
                "blockface_id": blockface_id,
                "street_name": meter_row.get("street_name"),
                "street_num": meter_row.get("street_num"),
                "latitude": meter_row.get("latitude"),
                "longitude": meter_row.get("longitude"),
                "reason": reason,
                "failure_point": "Matching logic"
            })
    
    # Print statistics
    print(f"\n=== Matching Statistics ===")
    print(f"Total meters: {match_stats['total_meters']}")
    print(f"Matched by blockface_id: {match_stats['blockface_match']}")
    print(f"Matched by CNN+address fallback: {match_stats['cnn_fallback']}")
    print(f"Failed to match: {match_stats['failed']}")
    
    print(f"\n=== Found {len(unmatched_meters)} Unmatched Meters ===\n")
    
    for i, meter in enumerate(unmatched_meters, 1):
        print(f"{i}. Post ID: {meter['post_id']}")
        print(f"   CNN: {meter['cnn']}")
        print(f"   Blockface ID: {meter['blockface_id']}")
        print(f"   Location: {meter['street_num']} {meter['street_name']}")
        print(f"   Coordinates: ({meter['latitude']}, {meter['longitude']})")
        print(f"   Failure Point: {meter['failure_point']}")
        print(f"   Reason: {meter['reason']}")
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())