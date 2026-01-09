#!/usr/bin/env python3
"""
Analyze Meter Policies Temporal Characteristics

This script validates whether Meter Policies is a temporal modification system by:
1. Analyzing StartDate and EndDate ranges
2. Identifying expired, active, and future policies
3. Comparing with Meter Operating Schedules dataset
"""

import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
from datetime import datetime

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_POLICIES_ID = "qq7v-hds4"
METER_OPERATING_SCHEDULES_ID = "6cqg-dxku"
PARKING_METERS_ID = "8vzz-qzz9"

def analyze_temporal_characteristics():
    """Analyze temporal characteristics of Meter Policies"""
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("ERROR: SFMTA_APP_TOKEN not found in environment")
        sys.exit(1)
    
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("METER POLICIES TEMPORAL ANALYSIS")
    print("="*80)
    
    # Fetch Meter Policies
    print("\n1. Fetching Meter Policies Dataset...")
    print("-"*80)
    
    try:
        policies = client.get(METER_POLICIES_ID, limit=50000)
        policies_df = pd.DataFrame.from_records(policies)
        
        print(f"✓ Fetched {len(policies_df)} meter policy records")
        print(f"✓ Unique postIDs: {policies_df['postid'].nunique()}")
        
    except Exception as e:
        print(f"ERROR fetching meter policies: {e}")
        return
    
    # Analyze Date Fields
    print("\n2. Analyzing Date Fields...")
    print("-"*80)
    
    # Convert dates
    policies_df['startdate'] = pd.to_datetime(policies_df['startdate'], errors='coerce')
    policies_df['enddate'] = pd.to_datetime(policies_df['enddate'], errors='coerce')
    policies_df['revisiondate'] = pd.to_datetime(policies_df['revisiondate'], errors='coerce')
    
    today = pd.Timestamp.now()
    
    print(f"\nCurrent date: {today.date()}")
    print(f"\nDate field coverage:")
    print(f"  - StartDate populated: {policies_df['startdate'].notna().sum()} ({policies_df['startdate'].notna().sum()/len(policies_df)*100:.1f}%)")
    print(f"  - EndDate populated: {policies_df['enddate'].notna().sum()} ({policies_df['enddate'].notna().sum()/len(policies_df)*100:.1f}%)")
    print(f"  - RevisionDate populated: {policies_df['revisiondate'].notna().sum()} ({policies_df['revisiondate'].notna().sum()/len(policies_df)*100:.1f}%)")
    
    # Sample dates
    print(f"\nSample StartDates:")
    print(policies_df['startdate'].dropna().head(10).tolist())
    
    print(f"\nSample EndDates:")
    print(policies_df['enddate'].dropna().head(10).tolist())
    
    # Temporal Classification
    print("\n3. Temporal Status Classification...")
    print("-"*80)
    
    policies_with_dates = policies_df[
        policies_df['startdate'].notna() & 
        policies_df['enddate'].notna()
    ]
    
    print(f"\nPolicies with valid date ranges: {len(policies_with_dates)} ({len(policies_with_dates)/len(policies_df)*100:.1f}%)")
    
    if len(policies_with_dates) > 0:
        # Classify by temporal status
        active = policies_with_dates[
            (policies_with_dates['startdate'] <= today) & 
            (policies_with_dates['enddate'] >= today)
        ]
        
        expired = policies_with_dates[policies_with_dates['enddate'] < today]
        future = policies_with_dates[policies_with_dates['startdate'] > today]
        
        print(f"\nTemporal Status:")
        print(f"  - ACTIVE (current): {len(active)} policies ({len(active)/len(policies_with_dates)*100:.1f}%)")
        print(f"  - EXPIRED (past): {len(expired)} policies ({len(expired)/len(policies_with_dates)*100:.1f}%)")
        print(f"  - FUTURE (scheduled): {len(future)} policies ({len(future)/len(policies_with_dates)*100:.1f}%)")
        
        # Key finding
        if len(expired) > 0:
            print(f"\n  🔍 KEY FINDING: {len(expired)} EXPIRED policies found!")
            print(f"     This CONFIRMS temporal modification hypothesis")
            
            # Show sample expired
            sample_expired = expired.head(3)
            print(f"\n     Sample expired policies:")
            for idx, row in sample_expired.iterrows():
                print(f"       PostID: {row['postid']}")
                print(f"       Valid: {row['startdate'].date()} to {row['enddate'].date()}")
                print(f"       Schedule: {row['scheduletype']}, {row['dayofweek']}, {row['starttime']}-{row['endtime']}")
                print()
        
        if len(future) > 0:
            print(f"\n  🔍 KEY FINDING: {len(future)} FUTURE policies found!")
            print(f"     This CONFIRMS pre-scheduling capability")
            
            # Show sample future
            sample_future = future.head(3)
            print(f"\n     Sample future policies:")
            for idx, row in sample_future.iterrows():
                print(f"       PostID: {row['postid']}")
                print(f"       Valid: {row['startdate'].date()} to {row['enddate'].date()}")
                print(f"       Schedule: {row['scheduletype']}, {row['dayofweek']}, {row['starttime']}-{row['endtime']}")
                print()
        
        # Duration analysis
        print("\n4. Policy Duration Analysis...")
        print("-"*80)
        
        policies_with_dates['duration_days'] = (
            policies_with_dates['enddate'] - policies_with_dates['startdate']
        ).dt.days
        
        print(f"\nDuration statistics:")
        print(f"  - Mean: {policies_with_dates['duration_days'].mean():.0f} days")
        print(f"  - Median: {policies_with_dates['duration_days'].median():.0f} days")
        print(f"  - Min: {policies_with_dates['duration_days'].min():.0f} days")
        print(f"  - Max: {policies_with_dates['duration_days'].max():.0f} days")
        
        # Categorize by duration
        very_short = policies_with_dates[policies_with_dates['duration_days'] < 30]  # < 1 month
        short = policies_with_dates[(policies_with_dates['duration_days'] >= 30) & (policies_with_dates['duration_days'] < 90)]  # 1-3 months
        medium = policies_with_dates[(policies_with_dates['duration_days'] >= 90) & (policies_with_dates['duration_days'] < 365)]  # 3-12 months
        long = policies_with_dates[(policies_with_dates['duration_days'] >= 365) & (policies_with_dates['duration_days'] < 3650)]  # 1-10 years
        very_long = policies_with_dates[policies_with_dates['duration_days'] >= 3650]  # > 10 years
        
        print(f"\nDuration categories:")
        print(f"  - Very short (< 1 month): {len(very_short)} ({len(very_short)/len(policies_with_dates)*100:.1f}%)")
        print(f"  - Short (1-3 months): {len(short)} ({len(short)/len(policies_with_dates)*100:.1f}%)")
        print(f"  - Medium (3-12 months): {len(medium)} ({len(medium)/len(policies_with_dates)*100:.1f}%)")
        print(f"  - Long (1-10 years): {len(long)} ({len(long)/len(policies_with_dates)*100:.1f}%)")
        print(f"  - Very long (> 10 years): {len(very_long)} ({len(very_long)/len(policies_with_dates)*100:.1f}%)")
        
        if len(very_long) > 0:
            print(f"\n  ℹ {len(very_long)} policies have duration > 10 years")
            print(f"    These may be 'permanent' policies (end date: 2200-12-31)")
    
    # Fetch Meter Operating Schedules for comparison
    print("\n5. Fetching Meter Operating Schedules for Comparison...")
    print("-"*80)
    
    try:
        schedules = client.get(METER_OPERATING_SCHEDULES_ID, limit=100000)
        schedules_df = pd.DataFrame.from_records(schedules)
        
        print(f"✓ Fetched {len(schedules_df)} meter operating schedule records")
        
        # Find postID field
        post_id_col = None
        for col in ['post_id', 'postid', 'post_ID', 'POST_ID']:
            if col in schedules_df.columns:
                post_id_col = col
                break
        
        if post_id_col:
            schedule_post_ids = set(schedules_df[post_id_col].dropna().astype(str))
            policy_post_ids = set(policies_df['postid'].dropna().astype(str))
            
            print(f"✓ Unique postIDs in Operating Schedules: {len(schedule_post_ids)}")
            print(f"✓ Unique postIDs in Policies: {len(policy_post_ids)}")
            
            # Overlap analysis
            in_both = policy_post_ids.intersection(schedule_post_ids)
            only_policies = policy_post_ids - schedule_post_ids
            only_schedules = schedule_post_ids - policy_post_ids
            
            print(f"\nOverlap Analysis:")
            print(f"  - PostIDs in BOTH datasets: {len(in_both)} ({len(in_both)/len(policy_post_ids)*100:.1f}% of policies)")
            print(f"  - PostIDs ONLY in Policies: {len(only_policies)} ({len(only_policies)/len(policy_post_ids)*100:.1f}%)")
            print(f"  - PostIDs ONLY in Schedules: {len(only_schedules)} ({len(only_schedules)/len(schedule_post_ids)*100:.1f}%)")
            
            if len(only_policies) > 0:
                print(f"\n  🔍 {len(only_policies)} postIDs have policies but NO base schedules")
                print(f"     Sample postIDs:")
                for pid in list(only_policies)[:5]:
                    print(f"       - {pid}")
            
            # Check for date fields in Operating Schedules
            print(f"\nOperating Schedules columns:")
            for col in sorted(schedules_df.columns):
                print(f"  - {col}")
            
            # Look for date fields
            date_cols = [col for col in schedules_df.columns if any(x in col.lower() for x in ['date', 'start', 'end'])]
            if date_cols:
                print(f"\nDate-related fields in Operating Schedules: {date_cols}")
            else:
                print(f"\n  ℹ No date fields found in Operating Schedules")
                print(f"    This suggests Operating Schedules are PERMANENT/BASE schedules")
                print(f"    while Policies are TEMPORAL modifications")
        
    except Exception as e:
        print(f"ERROR fetching meter operating schedules: {e}")
    
    client.close()
    
    # Final Conclusion
    print("\n" + "="*80)
    print("CONCLUSION: IS METER POLICIES A TEMPORAL MODIFICATION SYSTEM?")
    print("="*80)
    
    evidence = []
    
    if len(expired) > 0:
        evidence.append(f"✅ Contains {len(expired)} expired policies")
    if len(future) > 0:
        evidence.append(f"✅ Contains {len(future)} future/scheduled policies")
    if len(very_short) > 0 or len(short) > 0:
        evidence.append(f"✅ Contains {len(very_short) + len(short)} short-term policies (< 3 months)")
    if len(policy_post_ids) < len(schedule_post_ids):
        evidence.append(f"✅ Low coverage ({len(policy_post_ids)/len(schedule_post_ids)*100:.1f}% of schedules) suggests supplemental system")
    if 'revisiondate' in policies_df.columns:
        evidence.append(f"✅ Tracks revisions via RevisionDate field")
    
    print("\nEvidence:")
    for e in evidence:
        print(f"  {e}")
    
    if len(evidence) >= 3:
        print("\n🎯 VERDICT: YES - Strong evidence that Meter Policies is a TEMPORAL")
        print("   MODIFICATION/OVERRIDE system for Meter Operating Schedules")
        print("\n📋 RECOMMENDATION:")
        print("   - Keep CNN Master with base Operating Schedules (6cqg-dxku)")
        print("   - Fetch and apply active Meter Policies dynamically at query time")
        print("   - Filter policies by: startdate <= TODAY <= enddate")
    else:
        print("\n⚠️  VERDICT: INCONCLUSIVE - Need more evidence")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    analyze_temporal_characteristics()