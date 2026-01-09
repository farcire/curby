"""
Check if meters without schedules can be mapped to a CNN
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_OPERATING_SCHEDULES_ID = "6cqg-dxku"
PARKING_METERS_ID = "8vzz-qzz9"
ACTIVE_STREETS_ID = "3psu-pn9h"  # Active Streets with CNN

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("CHECKING CNN MAPPING FOR METERS WITHOUT SCHEDULES")
    print("="*80)
    
    # 1. Get meters without schedules
    print("\n1. Identifying meters without schedules...")
    print("-"*80)
    
    # Fetch schedules
    schedules = client.get(METER_OPERATING_SCHEDULES_ID, limit=100000)
    schedules_df = pd.DataFrame.from_records(schedules)
    schedule_postids = set(schedules_df['post_id'].unique())
    print(f"✓ Found {len(schedule_postids)} unique postIDs with schedules")
    
    # Fetch active On Street meters
    meters = client.get(PARKING_METERS_ID, limit=100000)
    meters_df = pd.DataFrame.from_records(meters)
    
    # Filter for active meters
    meters_df = meters_df[meters_df['active_meter_flag'].isin(['M', 'T'])]
    print(f"✓ Found {len(meters_df)} active meters")
    
    # Find meters without schedules
    meters_without_schedules = meters_df[~meters_df['post_id'].isin(schedule_postids)]
    print(f"\n📊 {len(meters_without_schedules)} meters do NOT have operating schedules")
    
    # 2. Check CNN mapping
    print("\n\n2. Checking CNN mapping for meters without schedules...")
    print("-"*80)
    
    # Check if meters have street_seg_ctrln_id (CNN)
    if 'street_seg_ctrln_id' in meters_without_schedules.columns:
        print(f"✓ Found CNN column: 'street_seg_ctrln_id'")
        
        # Count meters with CNN
        meters_with_cnn = meters_without_schedules[meters_without_schedules['street_seg_ctrln_id'].notna()]
        meters_without_cnn = meters_without_schedules[meters_without_schedules['street_seg_ctrln_id'].isna()]
        
        print(f"\n📊 CNN MAPPING RESULTS:")
        print(f"  ✓ {len(meters_with_cnn)} meters WITHOUT schedules HAVE a CNN")
        print(f"  ✓ {len(meters_without_cnn)} meters WITHOUT schedules DO NOT have a CNN")
        
        pct_with_cnn = (len(meters_with_cnn) / len(meters_without_schedules) * 100)
        print(f"\n  📈 {pct_with_cnn:.1f}% of meters without schedules can be mapped to a CNN")
        
        # Show sample CNNs
        if len(meters_with_cnn) > 0:
            print(f"\n  Sample meters with CNN:")
            for idx, row in meters_with_cnn.head(10).iterrows():
                print(f"    - PostID {row['post_id']}: CNN {row['street_seg_ctrln_id']} ({row.get('street_name', 'N/A')})")
        
        # Show sample without CNN
        if len(meters_without_cnn) > 0:
            print(f"\n  Sample meters WITHOUT CNN:")
            for idx, row in meters_without_cnn.head(10).iterrows():
                print(f"    - PostID {row['post_id']}: {row.get('street_name', 'N/A')} {row.get('street_num', 'N/A')}")
        
        # 3. Verify CNNs exist in Active Streets
        if len(meters_with_cnn) > 0:
            print(f"\n\n3. Verifying CNNs exist in Active Streets dataset...")
            print("-"*80)
            
            unique_cnns = meters_with_cnn['street_seg_ctrln_id'].unique()
            print(f"✓ {len(unique_cnns)} unique CNNs found in meters without schedules")
            
            # Sample check - verify a few CNNs
            print(f"\nVerifying sample CNNs in Active Streets dataset...")
            sample_cnns = list(unique_cnns)[:5]
            
            for cnn in sample_cnns:
                try:
                    cnn_str = str(int(float(cnn)))
                    streets = client.get(ACTIVE_STREETS_ID, cnn=cnn_str, limit=5)
                    if streets:
                        street_name = streets[0].get('streetname', 'Unknown')
                        print(f"  ✓ CNN {cnn_str}: Found in Active Streets ({street_name})")
                    else:
                        print(f"  ⚠ CNN {cnn_str}: NOT found in Active Streets")
                except Exception as e:
                    print(f"  ❌ CNN {cnn}: Error checking - {e}")
        
    else:
        print("⚠ No CNN column found in meters dataset")
        print(f"Available columns: {list(meters_without_schedules.columns)}")
    
    # 4. Summary
    print("\n\n4. FINAL SUMMARY")
    print("="*80)
    print(f"\n✅ Total meters without schedules: {len(meters_without_schedules)}")
    
    if 'street_seg_ctrln_id' in meters_without_schedules.columns:
        print(f"✅ Meters with CNN mapping: {len(meters_with_cnn)} ({pct_with_cnn:.1f}%)")
        print(f"✅ Meters without CNN mapping: {len(meters_without_cnn)} ({100-pct_with_cnn:.1f}%)")
        
        if pct_with_cnn > 90:
            print(f"\n🎯 CONCLUSION: YES - Nearly all meters without schedules can be mapped to a CNN")
        elif pct_with_cnn > 50:
            print(f"\n🎯 CONCLUSION: MOSTLY - Most meters without schedules can be mapped to a CNN")
        else:
            print(f"\n🎯 CONCLUSION: NO - Most meters without schedules cannot be mapped to a CNN")
    
    client.close()

if __name__ == "__main__":
    main()