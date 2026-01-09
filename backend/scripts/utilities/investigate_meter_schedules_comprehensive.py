"""
Comprehensive Meter Operating Schedule Investigation
1. Count unique postIDs in Meter Operating Schedules (6cqg-dxku)
2. Check mapping to active On Street Meters (8vzz-qzz9)
3. For meters without schedules, check if they're within geo boundaries of itv4-r6g6
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
from shapely.geometry import Point, shape
import json

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_OPERATING_SCHEDULES_ID = "6cqg-dxku"
PARKING_METERS_ID = "8vzz-qzz9"
GEO_BOUNDARY_ID = "itv4-r6g6"  # Need to identify what this dataset is

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("COMPREHENSIVE METER OPERATING SCHEDULE INVESTIGATION")
    print("="*80)
    
    # 1. Fetch Meter Operating Schedules
    print("\n1. Fetching Meter Operating Schedules (6cqg-dxku)...")
    print("-"*80)
    
    try:
        schedules = client.get(METER_OPERATING_SCHEDULES_ID, limit=100000)
        schedules_df = pd.DataFrame.from_records(schedules)
        
        print(f"✓ Fetched {len(schedules_df)} meter operating schedule records")
        print(f"\nColumns: {list(schedules_df.columns)}")
        
        # Find postID column
        postid_col = None
        for col in schedules_df.columns:
            if 'post' in col.lower() and 'id' in col.lower():
                postid_col = col
                break
        
        if not postid_col:
            print("\n⚠ WARNING: Could not find postID column!")
            return
        
        print(f"\n✓ Found postID column: '{postid_col}'")
        
        # Count unique postIDs
        unique_postids = schedules_df[postid_col].nunique()
        total_records = len(schedules_df)
        
        print(f"\n📊 UNIQUE postIDs in Schedules: {unique_postids}")
        print(f"📊 Total schedule records: {total_records}")
        print(f"📊 Average records per postID: {total_records / unique_postids:.2f}")
        
        schedule_postids = set(schedules_df[postid_col].unique())
        
    except Exception as e:
        print(f"❌ ERROR fetching meter operating schedules: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Fetch Active On Street Parking Meters
    print("\n\n2. Fetching Active On Street Parking Meters (8vzz-qzz9)...")
    print("-"*80)
    
    try:
        meters = client.get(PARKING_METERS_ID, limit=100000)
        meters_df = pd.DataFrame.from_records(meters)
        
        print(f"✓ Fetched {len(meters_df)} total parking meter records")
        print(f"\nColumns: {list(meters_df.columns)}")
        
        # Filter for On Street meters
        if 'on_offstreet' in meters_df.columns:
            street_col = 'on_offstreet'
        elif 'on_off_street' in meters_df.columns:
            street_col = 'on_off_street'
        else:
            print("⚠ Could not find on/off street column")
            street_col = None
        
        if street_col:
            meters_df = meters_df[meters_df[street_col] == 'ON']
            print(f"✓ Filtered to {len(meters_df)} On Street meters")
        
        # Filter for active meters
        if 'active_meter_flag' in meters_df.columns:
            active_col = 'active_meter_flag'
        elif 'active_met' in meters_df.columns:
            active_col = 'active_met'
        else:
            print("⚠ Could not find active meter column")
            active_col = None
        
        if active_col:
            meters_df = meters_df[meters_df[active_col].isin(['M', 'T'])]
            print(f"✓ Filtered to {len(meters_df)} active meters ({active_col} = 'M' or 'T')")
        
        print(f"\n✓ Final: {len(meters_df)} active On Street meters")
        
        # Find PostId column
        meter_postid_col = None
        for col in meters_df.columns:
            if 'post' in col.lower() and 'id' in col.lower():
                meter_postid_col = col
                break
        
        if not meter_postid_col:
            print("\n⚠ WARNING: Could not find PostId column in Meters!")
            return
        
        print(f"✓ Found PostId column: '{meter_postid_col}'")
        
        meter_postids = set(meters_df[meter_postid_col].unique())
        
    except Exception as e:
        print(f"❌ ERROR fetching parking meters: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Compare datasets
    print("\n\n3. COMPARISON ANALYSIS")
    print("="*80)
    
    orphaned_schedules = schedule_postids - meter_postids
    meters_without_schedules = meter_postids - schedule_postids
    matching_postids = schedule_postids & meter_postids
    
    print(f"\n📊 PostIDs in BOTH datasets: {len(matching_postids)}")
    print(f"📊 PostIDs ONLY in Schedules (orphaned): {len(orphaned_schedules)}")
    print(f"📊 PostIDs ONLY in Meters (no schedule): {len(meters_without_schedules)}")
    
    schedule_coverage = (len(matching_postids) / len(schedule_postids) * 100) if schedule_postids else 0
    meter_coverage = (len(matching_postids) / len(meter_postids) * 100) if meter_postids else 0
    
    print(f"\n📈 Coverage:")
    print(f"  - {schedule_coverage:.1f}% of schedule postIDs exist in active On Street meters")
    print(f"  - {meter_coverage:.1f}% of active On Street meters have operating schedules")
    
    # 4. Check geo boundaries for meters without schedules
    if meters_without_schedules:
        print(f"\n\n4. CHECKING GEO BOUNDARIES FOR METERS WITHOUT SCHEDULES")
        print("="*80)
        print(f"\nInvestigating {len(meters_without_schedules)} meters without schedules...")
        
        try:
            # First, let's see what dataset itv4-r6g6 is
            print(f"\nFetching geo boundary dataset (itv4-r6g6)...")
            geo_sample = client.get(GEO_BOUNDARY_ID, limit=5)
            
            if geo_sample:
                print(f"✓ Dataset found! Sample record columns:")
                sample_df = pd.DataFrame.from_records(geo_sample)
                print(f"  {list(sample_df.columns)}")
                
                # Fetch full geo boundary dataset
                geo_data = client.get(GEO_BOUNDARY_ID, limit=50000)
                geo_df = pd.DataFrame.from_records(geo_data)
                print(f"\n✓ Fetched {len(geo_df)} geo boundary records")
                
                # Get meters without schedules
                meters_no_sched_df = meters_df[meters_df[meter_postid_col].isin(meters_without_schedules)]
                
                # Check if meters have location data
                if 'location' in meters_no_sched_df.columns or 'the_geom' in meters_no_sched_df.columns:
                    loc_col = 'location' if 'location' in meters_no_sched_df.columns else 'the_geom'
                    print(f"\n✓ Found location column: '{loc_col}'")
                    
                    # Count meters with valid locations
                    meters_with_loc = meters_no_sched_df[meters_no_sched_df[loc_col].notna()]
                    print(f"  {len(meters_with_loc)} of {len(meters_no_sched_df)} meters have location data")
                    
                    # Sample locations
                    print(f"\nSample meter locations:")
                    for idx, row in meters_with_loc.head(5).iterrows():
                        print(f"  PostID {row[meter_postid_col]}: {row[loc_col]}")
                    
                else:
                    print("\n⚠ Meters dataset doesn't have location column")
                    print(f"Available columns: {list(meters_no_sched_df.columns)}")
                
            else:
                print(f"⚠ Could not fetch dataset itv4-r6g6")
                
        except Exception as e:
            print(f"❌ ERROR checking geo boundaries: {e}")
            import traceback
            traceback.print_exc()
    
    # 5. Final Summary
    print("\n\n5. FINAL SUMMARY")
    print("="*80)
    print(f"\n✅ ANSWER TO QUESTION 1:")
    print(f"   Number of unique postIDs in Meter Operating Schedules (6cqg-dxku): {unique_postids}")
    
    print(f"\n✅ ANSWER TO QUESTION 2:")
    if len(orphaned_schedules) == 0:
        print(f"   YES - All {unique_postids} postIDs map to active On Street meters")
    else:
        print(f"   NO - {len(orphaned_schedules)} postIDs ({len(orphaned_schedules)/len(schedule_postids)*100:.1f}%) do NOT map to active On Street meters")
        print(f"   (These are likely historical/inactive meters)")
    
    print(f"\n📊 METERS WITHOUT SCHEDULES:")
    print(f"   {len(meters_without_schedules)} active On Street meters have no operating schedule")
    print(f"   This represents {len(meters_without_schedules)/len(meter_postids)*100:.1f}% of all active On Street meters")
    
    if meters_without_schedules:
        print(f"\n   Sample PostIDs without schedules:")
        for pid in list(meters_without_schedules)[:10]:
            print(f"     - {pid}")
    
    client.close()

if __name__ == "__main__":
    main()