"""
Investigate why blockface IDs exist but no matching segment is found.
This happens when the meter's CNN field is NaN/missing.
"""
import os
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
from pymongo import MongoClient

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METERS_DATASET_ID = "8vzz-qzz9"
METERED_BLOCKFACES_ID = "mk27-a5x2"

def fetch_data_as_dataframe(dataset_id: str, app_token: str, limit: int = 200000) -> pd.DataFrame:
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(dataset_id, limit=limit)
        df = pd.DataFrame.from_records(results)
        return df
    except Exception as e:
        print(f"Error fetching dataset {dataset_id}: {e}")
        return pd.DataFrame()

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")
    
    # Connect to MongoDB
    client = MongoClient(mongodb_uri)
    db = client["curby"]
    
    # Load metered blockfaces
    print("Loading metered blockfaces...")
    metered_blockfaces_df = fetch_data_as_dataframe(METERED_BLOCKFACES_ID, app_token)
    
    # Load meters
    print("Loading meters...")
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    
    # Example: Investigate meter 491-06001 (blockface 491061)
    print("\n=== Investigating Meter 491-06001 ===")
    meter = meters_df[meters_df['post_id'] == '491-06001'].iloc[0]
    
    print(f"\nMeter Details:")
    print(f"  Post ID: {meter.get('post_id')}")
    print(f"  CNN: {meter.get('street_seg_ctrln_id')} (type: {type(meter.get('street_seg_ctrln_id'))})")
    print(f"  Blockface ID: {meter.get('blockface_id')}")
    print(f"  Location: {meter.get('street_num')} {meter.get('street_name')}")
    
    # Look up this blockface in metered blockfaces dataset
    blockface_id = str(meter.get('blockface_id'))
    print(f"\n=== Looking up Blockface {blockface_id} ===")
    
    blockface_matches = metered_blockfaces_df[metered_blockfaces_df['blockface_id'] == blockface_id]
    
    if not blockface_matches.empty:
        bf = blockface_matches.iloc[0]
        print(f"✓ Found in metered blockfaces dataset:")
        print(f"  Street: {bf.get('street_name')}")
        print(f"  Side: {bf.get('str_seg_orientation')}")
        print(f"  Address Range: {bf.get('fm_addr_no')} - {bf.get('to_addr_no')}")
        
        # The metered blockfaces dataset doesn't have CNN!
        # That's why we need the meter's CNN field
        print(f"\n⚠️  PROBLEM: Metered blockfaces dataset does NOT contain CNN")
        print(f"  We need the meter's CNN field to match to segments")
        print(f"  But meter's CNN is: {meter.get('street_seg_ctrln_id')}")
    else:
        print(f"✗ NOT found in metered blockfaces dataset")
    
    # Check what fields metered blockfaces has
    print(f"\n=== Metered Blockfaces Dataset Fields ===")
    print(f"Available fields: {list(metered_blockfaces_df.columns)}")
    print(f"Has 'cnn' field: {'cnn' in metered_blockfaces_df.columns}")
    print(f"Has 'street_seg_ctrln_id' field: {'street_seg_ctrln_id' in metered_blockfaces_df.columns}")
    
    # Show the matching logic flow
    print(f"\n=== Matching Logic Flow ===")
    print(f"1. Meter has blockface_id: {blockface_id}")
    print(f"2. Look up blockface_id in metered blockfaces → Found: {not blockface_matches.empty}")
    if not blockface_matches.empty:
        print(f"3. Get side from blockface: {bf.get('str_seg_orientation')}")
        print(f"4. Need CNN to find segment with (CNN={meter.get('street_seg_ctrln_id')}, side={bf.get('str_seg_orientation')})")
        print(f"5. ❌ FAIL: Meter's CNN is NaN/missing, cannot complete match")
    
    print(f"\n=== Why This Happens ===")
    print(f"The matching algorithm is:")
    print(f"  blockface_id → (side) from metered_blockfaces")
    print(f"  meter.CNN + side → find matching segment")
    print(f"\nBut if meter.CNN is missing:")
    print(f"  blockface_id → (side) ✓")
    print(f"  NaN + side → ✗ Cannot find segment")
    
    client.close()

if __name__ == "__main__":
    main()