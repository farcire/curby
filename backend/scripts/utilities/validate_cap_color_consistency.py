#!/usr/bin/env python3
"""
Validate Cap Color Consistency Between Datasets

Verify that cap_color in Parking Meters matches capcolor in Meter Policies
for the same postID. Since a postID can have multiple policies, we check if
the meter's cap color appears in ANY of the policies for that postID.
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_POLICIES_ID = "qq7v-hds4"
PARKING_METERS_ID = "8vzz-qzz9"

def validate_cap_color_consistency():
    """Validate cap color consistency between datasets"""
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("CAP COLOR CONSISTENCY VALIDATION")
    print("="*80)
    
    # Fetch Parking Meters
    print("\n1. Fetching Parking Meters...")
    meters = client.get(PARKING_METERS_ID, limit=50000)
    meters_df = pd.DataFrame.from_records(meters)
    
    # Create lookup: postID -> cap_color from meters
    meters_cap_color = {}
    for _, row in meters_df.iterrows():
        post_id = str(row.get('post_id', ''))
        cap_color = row.get('cap_color', '')
        if post_id:
            meters_cap_color[post_id] = cap_color
    
    print(f"✓ Loaded {len(meters_cap_color)} meters with cap colors")
    
    # Fetch Meter Policies
    print("\n2. Fetching Meter Policies...")
    policies = client.get(METER_POLICIES_ID, limit=50000)
    policies_df = pd.DataFrame.from_records(policies)
    
    print(f"✓ Loaded {len(policies_df)} policy records")
    
    # Group policies by postID and collect all cap colors
    print("\n3. Grouping Policies by PostID...")
    print("-"*80)
    
    policies_by_post = {}
    for _, policy in policies_df.iterrows():
        post_id = str(policy.get('postid', ''))
        policy_cap = policy.get('capcolor', '')
        
        if not post_id or not policy_cap:
            continue
        
        if post_id not in policies_by_post:
            policies_by_post[post_id] = set()
        
        # Normalize and add to set
        policy_cap_norm = str(policy_cap).strip().upper()
        policies_by_post[post_id].add(policy_cap_norm)
    
    print(f"✓ Grouped {len(policies_by_post)} unique postIDs with cap colors")
    
    # Show sample of postIDs with multiple cap colors in policies
    multi_cap_posts = {pid: caps for pid, caps in policies_by_post.items() if len(caps) > 1}
    if multi_cap_posts:
        print(f"\n  Note: {len(multi_cap_posts)} postIDs have multiple cap colors across policies")
        print("  Sample postIDs with multiple policy cap colors:")
        for i, (pid, caps) in enumerate(list(multi_cap_posts.items())[:3]):
            print(f"    {i+1}. PostID {pid}: {caps}")
    
    # Compare: Check if meter cap color exists in ANY policy for that postID
    print("\n4. Comparing Cap Colors...")
    print("-"*80)
    
    consistent_posts = []
    inconsistent_posts = []
    yellow_consistent = []
    yellow_inconsistent = []
    red_consistent = []
    red_inconsistent = []
    
    for post_id, policy_caps in policies_by_post.items():
        meter_cap = meters_cap_color.get(post_id)
        
        if not meter_cap:
            continue
        
        meter_cap_norm = str(meter_cap).strip().upper()
        
        # Check if meter cap exists in ANY of the policies for this postID
        is_consistent = meter_cap_norm in policy_caps
        
        if is_consistent:
            consistent_posts.append({
                'post_id': post_id,
                'meter_cap': meter_cap,
                'policy_caps': policy_caps
            })
            
            # Track Yellow and Red
            if meter_cap_norm == 'YELLOW':
                yellow_consistent.append(post_id)
            elif meter_cap_norm == 'RED':
                red_consistent.append(post_id)
        else:
            inconsistent_posts.append({
                'post_id': post_id,
                'meter_cap': meter_cap,
                'policy_caps': policy_caps
            })
            
            # Track Yellow and Red inconsistencies
            if meter_cap_norm == 'YELLOW':
                yellow_inconsistent.append({
                    'post_id': post_id,
                    'meter_cap': meter_cap,
                    'policy_caps': policy_caps
                })
            elif meter_cap_norm == 'RED':
                red_inconsistent.append({
                    'post_id': post_id,
                    'meter_cap': meter_cap,
                    'policy_caps': policy_caps
                })
    
    total_compared = len(consistent_posts) + len(inconsistent_posts)
    
    print(f"\nTotal postIDs compared: {total_compared}")
    print(f"Consistent (meter cap in policies): {len(consistent_posts)} ({len(consistent_posts)/total_compared*100:.1f}%)")
    print(f"Inconsistent (meter cap NOT in policies): {len(inconsistent_posts)} ({len(inconsistent_posts)/total_compared*100:.1f}%)")
    
    # Report on Yellow caps
    print("\n5. Yellow Cap Color Analysis...")
    print("-"*80)
    
    print(f"Total Yellow cap postIDs checked: {len(yellow_consistent) + len(yellow_inconsistent)}")
    print(f"  Consistent: {len(yellow_consistent)}")
    print(f"  Inconsistent: {len(yellow_inconsistent)}")
    
    if yellow_inconsistent:
        print(f"\n⚠ WARNING: {len(yellow_inconsistent)} Yellow cap inconsistencies found!")
        print("\nSample Yellow inconsistencies:")
        for i, item in enumerate(yellow_inconsistent[:5]):
            print(f"  {i+1}. PostID: {item['post_id']}")
            print(f"     Meter cap: {item['meter_cap']}")
            print(f"     Policy caps: {item['policy_caps']}")
    else:
        print("\n✓ All Yellow caps are consistent between datasets!")
    
    # Report on Red caps
    print("\n6. Red Cap Color Analysis...")
    print("-"*80)
    
    print(f"Total Red cap postIDs checked: {len(red_consistent) + len(red_inconsistent)}")
    print(f"  Consistent: {len(red_consistent)}")
    print(f"  Inconsistent: {len(red_inconsistent)}")
    
    if red_inconsistent:
        print(f"\n⚠ WARNING: {len(red_inconsistent)} Red cap inconsistencies found!")
        print("\nSample Red inconsistencies:")
        for i, item in enumerate(red_inconsistent[:5]):
            print(f"  {i+1}. PostID: {item['post_id']}")
            print(f"     Meter cap: {item['meter_cap']}")
            print(f"     Policy caps: {item['policy_caps']}")
    else:
        print("\n✓ All Red caps are consistent between datasets!")
    
    # Show general inconsistencies
    if inconsistent_posts:
        print("\n7. General Cap Color Inconsistencies...")
        print("-"*80)
        print(f"\nSample of all inconsistencies (first 10):")
        for i, item in enumerate(inconsistent_posts[:10]):
            print(f"  {i+1}. PostID: {item['post_id']}")
            print(f"     Parking Meters cap: {item['meter_cap']}")
            print(f"     Meter Policies caps: {item['policy_caps']}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if len(inconsistent_posts) == 0:
        print("\n✓ PERFECT CONSISTENCY: All meter cap colors appear in their policies!")
    elif len(inconsistent_posts) / total_compared < 0.01:
        print(f"\n✓ EXCELLENT CONSISTENCY: {len(consistent_posts)/total_compared*100:.1f}% match rate")
        print(f"  Only {len(inconsistent_posts)} inconsistencies out of {total_compared} postIDs")
    else:
        print(f"\n⚠ CONSISTENCY ISSUES: {len(inconsistent_posts)/total_compared*100:.1f}% inconsistency rate")
    
    print("\n✓ RECOMMENDATION:")
    if len(yellow_inconsistent) == 0 and len(red_inconsistent) == 0:
        print("  ✓ Use Parking Meters dataset as the authoritative source for cap_color")
        print("  ✓ Yellow and Red caps are 100% consistent - SAFE to use for vehicle restrictions")
        print("  ✓ Cap color is a meter-level attribute (one per postID)")
    else:
        print("  ⚠ INVESTIGATE inconsistencies before using cap_color for restrictions")
        print("  ⚠ Manual review required for Yellow and Red cap discrepancies")
    
    client.close()
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    validate_cap_color_consistency()