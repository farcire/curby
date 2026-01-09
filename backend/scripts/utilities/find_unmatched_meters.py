"""
Find the 15 meters that failed to match during ingestion.
"""
import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
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
    
    # Load metered blockfaces
    print("Loading metered blockfaces...")
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
    
    # Find unmatched meters
    unmatched_meters = []
    
    for idx, meter_row in meters_df.iterrows():
        cnn = meter_row.get("street_seg_ctrln_id")
        post_id = meter_row.get("post_id")
        blockface_id = meter_row.get("blockface_id")
        
        # Check if this meter would fail to match
        failed = False
        reason = ""
        
        if not cnn or not post_id:
            failed = True
            reason = "Missing CNN or post_id"
        elif blockface_id and str(blockface_id) not in blockface_to_cnn_side:
            # Has blockface_id but it's not in our lookup
            failed = True
            reason = "Blockface ID not in metered blockfaces dataset"
        elif not blockface_id:
            # No blockface_id, would need address fallback
            street_num = meter_row.get("street_num")
            if not street_num:
                failed = True
                reason = "No blockface_id and no street_num for fallback"
        
        if failed:
            unmatched_meters.append({
                "post_id": post_id,
                "cnn": cnn,
                "blockface_id": blockface_id,
                "street_name": meter_row.get("street_name"),
                "street_num": meter_row.get("street_num"),
                "latitude": meter_row.get("latitude"),
                "longitude": meter_row.get("longitude"),
                "reason": reason
            })
    
    print(f"\n=== Found {len(unmatched_meters)} Unmatched Meters ===\n")
    
    for i, meter in enumerate(unmatched_meters, 1):
        print(f"{i}. Post ID: {meter['post_id']}")
        print(f"   CNN: {meter['cnn']}")
        print(f"   Blockface ID: {meter['blockface_id']}")
        print(f"   Location: {meter['street_num']} {meter['street_name']}")
        print(f"   Coordinates: ({meter['latitude']}, {meter['longitude']})")
        print(f"   Reason: {meter['reason']}")
        print()

if __name__ == "__main__":
    asyncio.run(main())