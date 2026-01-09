"""
Investigate Meter Operating Schedule Dataset (6cqg-dxku)
- Count unique postIDs
- Verify if all postIDs map to PostIds in Meters dataset (8vzz-qzz9)
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_OPERATING_SCHEDULES_ID = "6cqg-dxku"
PARKING_METERS_ID = "8vzz-qzz9"

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("METER OPERATING SCHEDULE DATASET INVESTIGATION")
    print("="*80)
    
    # 1. Fetch Meter Operating Schedules
    print("\n1. Fetching Meter Operating Schedules (6cqg-dxku)...")
    print("-"*80)
    
    try:
        schedules = client.get(METER_OPERATING_SCHEDULES_ID, limit=100000)
        schedules_df = pd.DataFrame.from_records(schedules)
        
        print(f"✓ Fetched {len(schedules_df)} meter operating schedule records")
        print(f"\nColumns in dataset: {list(schedules_df.columns)}")
        
        # Check for postID field (might be post_id, postid, PostID, etc.)
        postid_col = None
        for col in schedules_df.columns:
            if 'post' in col.lower() and 'id' in col.lower():
                postid_col = col
                break
        
        if not postid_col:
            print("\n⚠ WARNING: Could not find postID column!")
            print("Available columns:", list(schedules_df.columns))
            return
        
        print(f"\n✓ Found postID column: '{postid_col}'")
        
        # Count unique postIDs
        unique_postids = schedules_df[postid_col].nunique()
        total_records = len(schedules_df)
        
        print(f"\n📊 UNIQUE postIDs: {unique_postids}")
        print(f"📊 Total records: {total_records}")
        print(f"📊 Average records per postID: {total_records / unique_postids:.2f}")
        
        # Get all unique postIDs
        schedule_postids = set(schedules_df[postid_col].unique())
        
        # Sample of postIDs
        print(f"\nSample postIDs from schedules:")
        for pid in list(schedule_postids)[:10]:
            print(f"  - {pid}")
        
    except Exception as e:
        print(f"❌ ERROR fetching meter operating schedules: {e}")
        return
    
    # 2. Fetch Parking Meters
    print("\n\n2. Fetching Parking Meters (8vzz-qzz9)...")
    print("-"*80)
    
    try:
        meters = client.get(PARKING_METERS_ID, limit=100000)
        meters_df = pd.DataFrame.from_records(meters)
        
        print(f"✓ Fetched {len(meters_df)} total parking meter records")
        
        # Filter for On Street and active meters only
        print("\nFiltering for On Street and active meters (active_met = 'M' or 'T')...")
        
        # Check column names
        print(f"\nColumns in dataset: {list(meters_df.columns)}")
        
        # Filter for On Street meters
        if 'on_offstreet' in meters_df.columns or 'on_off_street' in meters_df.columns:
            street_col = 'on_offstreet' if 'on_offstreet' in meters_df.columns else 'on_off_street'
            meters_df = meters_df[meters_df[street_col] == 'ON']
            print(f"✓ Filtered to {len(meters_df)} On Street meters")
        
        # Filter for active meters
        if 'active_meter_flag' in meters_df.columns:
            meters_df = meters_df[meters_df['active_meter_flag'].isin(['M', 'T'])]
            print(f"✓ Filtered to {len(meters_df)} active meters (active_meter_flag = 'M' or 'T')")
        elif 'active_met' in meters_df.columns:
            meters_df = meters_df[meters_df['active_met'].isin(['M', 'T'])]
            print(f"✓ Filtered to {len(meters_df)} active meters (active_met = 'M' or 'T')")
        
        print(f"\n✓ Final filtered count: {len(meters_df)} On Street active meters")
        
        # Check for PostId field
        meter_postid_col = None
        for col in meters_df.columns:
            if 'post' in col.lower() and 'id' in col.lower():
                meter_postid_col = col
                break
        
        if not meter_postid_col:
            print("\n⚠ WARNING: Could not find PostId column in Meters!")
            print("Available columns:", list(meters_df.columns))
            return
        
        print(f"\n✓ Found PostId column: '{meter_postid_col}'")
        
        # Get all unique PostIds from meters
        meter_postids = set(meters_df[meter_postid_col].unique())
        unique_meter_postids = len(meter_postids)
        
        print(f"\n📊 UNIQUE PostIds in Meters: {unique_meter_postids}")
        
        # Sample of PostIds
        print(f"\nSample PostIds from meters:")
        for pid in list(meter_postids)[:10]:
            print(f"  - {pid}")
        
    except Exception as e:
        print(f"❌ ERROR fetching parking meters: {e}")
        return
    
    # 3. Compare the two datasets
    print("\n\n3. COMPARISON ANALYSIS")
    print("="*80)
    
    # Find schedules with postIDs not in meters
    orphaned_schedules = schedule_postids - meter_postids
    
    # Find meters with PostIds not in schedules
    meters_without_schedules = meter_postids - schedule_postids
    
    # Find matching postIDs
    matching_postids = schedule_postids & meter_postids
    
    print(f"\n📊 PostIDs in BOTH datasets: {len(matching_postids)}")
    print(f"📊 PostIDs ONLY in Schedules (orphaned): {len(orphaned_schedules)}")
    print(f"📊 PostIDs ONLY in Meters (no schedule): {len(meters_without_schedules)}")
    
    # Calculate percentages
    schedule_coverage = (len(matching_postids) / len(schedule_postids) * 100) if schedule_postids else 0
    meter_coverage = (len(matching_postids) / len(meter_postids) * 100) if meter_postids else 0
    
    print(f"\n📈 Coverage Analysis:")
    print(f"  - {schedule_coverage:.1f}% of schedule postIDs exist in Meters dataset")
    print(f"  - {meter_coverage:.1f}% of meter PostIds have operating schedules")
    
    # Show orphaned schedules
    if orphaned_schedules:
        print(f"\n⚠ ORPHANED SCHEDULES (postIDs not in Meters):")
        print(f"  Total: {len(orphaned_schedules)}")
        print(f"  Sample (first 20):")
        for pid in list(orphaned_schedules)[:20]:
            count = len(schedules_df[schedules_df[postid_col] == pid])
            print(f"    - {pid} ({count} schedule records)")
    
    # Show meters without schedules
    if meters_without_schedules:
        print(f"\n⚠ METERS WITHOUT SCHEDULES:")
        print(f"  Total: {len(meters_without_schedules)}")
        print(f"  Sample (first 20):")
        for pid in list(meters_without_schedules)[:20]:
            print(f"    - {pid}")
    
    # 4. Final Answer
    print("\n\n4. FINAL ANSWER")
    print("="*80)
    print(f"\n✅ Number of unique postIDs in Meter Operating Schedules (6cqg-dxku): {unique_postids}")
    
    if len(orphaned_schedules) == 0:
        print(f"\n✅ YES - All {unique_postids} postIDs map to PostIds in the Meters dataset (8vzz-qzz9)")
    else:
        print(f"\n❌ NO - {len(orphaned_schedules)} postIDs ({len(orphaned_schedules)/len(schedule_postids)*100:.1f}%) do NOT map to PostIds in the Meters dataset")
        print(f"   These are likely historical/inactive meters that have been removed.")
    
    client.close()

if __name__ == "__main__":
    main()