#!/usr/bin/env python3
"""
Validate Meter Policies Coverage

This script verifies:
1. All postIDs in Meter Policies (qq7v-hds4) exist in Parking Meters (8vzz-qzz9)
2. Cap color is available in Parking Meters dataset
3. Data hierarchy: Parking Meters (primary) → Meter Policies (supplement)
"""

import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_POLICIES_ID = "qq7v-hds4"
PARKING_METERS_ID = "8vzz-qzz9"

def validate_meter_policies_coverage():
    """Validate that all meter policies reference valid parking meters"""
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("ERROR: SFMTA_APP_TOKEN not found in environment")
        sys.exit(1)
    
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("METER POLICIES COVERAGE VALIDATION")
    print("="*80)
    
    # Step 1: Fetch Parking Meters (Primary Source)
    print("\n1. Fetching Parking Meters Dataset (8vzz-qzz9)...")
    print("-"*80)
    
    try:
        meters = client.get(PARKING_METERS_ID, limit=50000)
        meters_df = pd.DataFrame.from_records(meters)
        
        print(f"✓ Fetched {len(meters_df)} parking meter records")
        print(f"\nAvailable columns in Parking Meters:")
        for col in sorted(meters_df.columns):
            print(f"  - {col}")
        
        # Find postID field
        post_id_col = None
        for col in ['post_id', 'postid', 'post_ID', 'POST_ID']:
            if col in meters_df.columns:
                post_id_col = col
                break
        
        if not post_id_col:
            print("ERROR: Could not find postID field in Parking Meters")
            return
        
        print(f"\n✓ Using postID field: '{post_id_col}'")
        
        # Get unique postIDs from meters
        meter_post_ids = set(meters_df[post_id_col].dropna().astype(str))
        print(f"✓ Found {len(meter_post_ids)} unique postIDs in Parking Meters")
        
        # Check for cap_color field
        cap_color_col = None
        for col in ['cap_color', 'capcolor', 'cap_colour', 'color']:
            if col in meters_df.columns:
                cap_color_col = col
                break
        
        if cap_color_col:
            print(f"✓ Found cap color field: '{cap_color_col}'")
            
            # Show cap color distribution
            cap_colors = meters_df[cap_color_col].value_counts()
            print(f"\nCap color distribution in Parking Meters:")
            for color, count in cap_colors.items():
                print(f"  - {color}: {count} meters ({count/len(meters_df)*100:.1f}%)")
            
            # Check for missing cap colors
            missing_cap = meters_df[cap_color_col].isna().sum()
            if missing_cap > 0:
                print(f"\n⚠ {missing_cap} meters ({missing_cap/len(meters_df)*100:.1f}%) have no cap_color")
        else:
            print("⚠ WARNING: No cap_color field found in Parking Meters dataset")
        
        # Check for parking_space_id
        space_id_col = None
        for col in ['parking_space_id', 'parkingspaceid', 'space_id']:
            if col in meters_df.columns:
                space_id_col = col
                break
        
        if space_id_col:
            print(f"✓ Found parking space ID field: '{space_id_col}'")
            missing_space = meters_df[space_id_col].isna().sum()
            if missing_space > 0:
                print(f"  ⚠ {missing_space} meters ({missing_space/len(meters_df)*100:.1f}%) have no parking_space_id")
        else:
            print("⚠ WARNING: No parking_space_id field found in Parking Meters dataset")
        
    except Exception as e:
        print(f"ERROR fetching parking meters: {e}")
        return
    
    # Step 2: Fetch Meter Policies (Supplemental Source)
    print("\n2. Fetching Meter Policies Dataset (qq7v-hds4)...")
    print("-"*80)
    
    try:
        policies = client.get(METER_POLICIES_ID, limit=50000)
        policies_df = pd.DataFrame.from_records(policies)
        
        print(f"✓ Fetched {len(policies_df)} meter policy records")
        
        # Find postID field in policies
        policy_post_id_col = None
        for col in ['post_id', 'postid', 'post_ID', 'POST_ID']:
            if col in policies_df.columns:
                policy_post_id_col = col
                break
        
        if not policy_post_id_col:
            print("ERROR: Could not find postID field in Meter Policies")
            return
        
        print(f"✓ Using postID field: '{policy_post_id_col}'")
        
        # Get unique postIDs from policies
        policy_post_ids = set(policies_df[policy_post_id_col].dropna().astype(str))
        print(f"✓ Found {len(policy_post_ids)} unique postIDs in Meter Policies")
        
    except Exception as e:
        print(f"ERROR fetching meter policies: {e}")
        return
    
    # Step 3: Validate Coverage
    print("\n3. Validating PostID Coverage...")
    print("-"*80)
    
    # Check if all policy postIDs exist in meters
    policies_in_meters = policy_post_ids.intersection(meter_post_ids)
    policies_not_in_meters = policy_post_ids - meter_post_ids
    
    print(f"\nPostIDs in Meter Policies: {len(policy_post_ids)}")
    print(f"PostIDs also in Parking Meters: {len(policies_in_meters)} ({len(policies_in_meters)/len(policy_post_ids)*100:.1f}%)")
    print(f"PostIDs NOT in Parking Meters: {len(policies_not_in_meters)} ({len(policies_not_in_meters)/len(policy_post_ids)*100:.1f}%)")
    
    if policies_not_in_meters:
        print(f"\n⚠ WARNING: {len(policies_not_in_meters)} postIDs in Meter Policies are NOT in Parking Meters!")
        print("\nSample missing postIDs:")
        for i, pid in enumerate(list(policies_not_in_meters)[:10]):
            print(f"  {i+1}. {pid}")
            
            # Show policies for this missing postID
            missing_policies = policies_df[policies_df[policy_post_id_col].astype(str) == pid]
            print(f"     Has {len(missing_policies)} policies")
    else:
        print("\n✓ CONFIRMED: All postIDs in Meter Policies exist in Parking Meters!")
    
    # Check reverse: meters without policies
    meters_without_policies = meter_post_ids - policy_post_ids
    print(f"\nPostIDs in Parking Meters without policies: {len(meters_without_policies)} ({len(meters_without_policies)/len(meter_post_ids)*100:.1f}%)")
    
    if meters_without_policies:
        print(f"  ℹ {len(meters_without_policies)} meters have no operating schedule policies")
        print("  Sample postIDs without policies:")
        for i, pid in enumerate(list(meters_without_policies)[:5]):
            print(f"    {i+1}. {pid}")
    
    # Step 4: Show actual column names
    print("\n4. Meter Policies Dataset Columns...")
    print("-"*80)
    print("\nAll available columns in Meter Policies:")
    for col in sorted(policies_df.columns):
        print(f"  - {col}")
    
    # Step 5: Analyze Schedule Types with correct field names
    print("\n5. Analyzing Schedule Types in Meter Policies...")
    print("-"*80)
    
    schedule_type_col = None
    for col in ['schedule_type', 'scheduletype', 'type', 'schedtype']:
        if col in policies_df.columns:
            schedule_type_col = col
            break
    
    if schedule_type_col:
        schedule_counts = policies_df[schedule_type_col].value_counts()
        print(f"\nSchedule type distribution:")
        for stype, count in schedule_counts.items():
            print(f"  - {stype}: {count} policies ({count/len(policies_df)*100:.1f}%)")
        
        # Show sample for each type with correct field names
        print("\nSample policies by schedule type (with actual field names):")
        for stype in ['FREE', 'PRE', 'OP']:
            sample = policies_df[policies_df[schedule_type_col] == stype].head(2)
            if not sample.empty:
                print(f"\n  {stype} Schedule:")
                for _, row in sample.iterrows():
                    print(f"    PostID: {row.get(policy_post_id_col)}")
                    
                    # Get actual field values
                    day = row.get('dayofweek', 'N/A')
                    start = row.get('starttime', 'N/A')
                    end = row.get('endtime', 'N/A')
                    limit = row.get('timelimitminutes', 'N/A')
                    rate = row.get('hourlyrate', 'N/A')
                    space_id = row.get('parkingspaceid', 'N/A')
                    
                    print(f"    ParkingSpaceID: {space_id}")
                    print(f"    DayOfWeek: {day}")
                    print(f"    StartTime: {start}, EndTime: {end}")
                    print(f"    TimeLimitMinutes: {limit}")
                    if rate != 'N/A':
                        print(f"    HourlyRate: {rate}")
                    
                    # Show validity dates
                    start_date = (row.get('startdate') or row.get('start_date') or
                                 row.get('StartDate') or 'N/A')
                    end_date = (row.get('enddate') or row.get('end_date') or
                               row.get('EndDate') or 'N/A')
                    print(f"    Valid: {start_date} to {end_date}")
                    
                    if 'rate' in row:
                        print(f"    Rate: {row.get('rate', 'N/A')}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    print("\n✓ DATA HIERARCHY CONFIRMED:")
    print("  1. Parking Meters (8vzz-qzz9) = PRIMARY source")
    print(f"     - Contains: postID, parking_space_id, cap_color, location, etc.")
    print(f"     - {len(meter_post_ids)} unique meters")
    
    print("\n  2. Meter Policies (qq7v-hds4) = SUPPLEMENTAL source")
    print(f"     - Contains: Operating schedules (Free/PRE/OP), time windows, rates")
    print(f"     - {len(policy_post_ids)} unique postIDs with policies")
    print(f"     - {len(policies_df)} total policy records")
    
    if len(policies_not_in_meters) == 0:
        print("\n✓ VALIDATION PASSED: All meter policies reference valid parking meters")
    else:
        print(f"\n⚠ VALIDATION WARNING: {len(policies_not_in_meters)} policy postIDs not found in meters")
    
    print("\n✓ INTEGRATION STRATEGY:")
    print("  1. Load Parking Meters first (get postID, parking_space_id, cap_color)")
    print("  2. Load Meter Policies and group by postID")
    print("  3. Attach policies to meters using postID as join key")
    print("  4. Cap color comes from Parking Meters, NOT from policies")
    
    client.close()
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    validate_meter_policies_coverage()