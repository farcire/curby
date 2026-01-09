"""
Analyze On-Street Meter Coverage
Verify that 100% of ON STREET meters can be matched to CNN segments
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METERS_DATASET_ID = "8vzz-qzz9"        # All parking meters
METERED_BLOCKFACES_ID = "mk27-a5x2"    # Metered blockfaces metadata
STREETS_DATASET_ID = "3psu-pn9h"       # Active streets (CNN backbone)

def analyze_on_street_meter_coverage():
    """Analyze if all ON STREET meters can be matched to CNNs"""
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("ON-STREET METER COVERAGE ANALYSIS")
    print("="*80)
    
    # 1. Fetch ALL meters
    print("\n1. Fetching ALL parking meters...")
    print("-"*80)
    
    meters = client.get(METERS_DATASET_ID, limit=50000)
    meters_df = pd.DataFrame.from_records(meters)
    
    print(f"✓ Fetched {len(meters_df)} total meters")
    print(f"\nColumns: {list(meters_df.columns)}")
    
    # 2. Filter for ON STREET meters only
    print("\n2. Filtering for ON STREET meters...")
    print("-"*80)
    
    # Check if there's a field indicating on-street vs off-street
    location_fields = [col for col in meters_df.columns if 'location' in col.lower() or 'type' in col.lower() or 'street' in col.lower()]
    print(f"Location-related fields: {location_fields}")
    
    # Show sample records to understand the data
    print("\nSample meter records:")
    for i in range(min(3, len(meters_df))):
        print(f"\nMeter {i+1}:")
        sample = meters_df.iloc[i]
        for col in ['post_id', 'street_name', 'street_num', 'street_seg_ctrln_id', 'blockface_id', 'meter_type', 'on_offstreet_type']:
            if col in sample:
                print(f"  {col:25s}: {sample[col]}")
    
    # Filter for on-street meters
    if 'on_offstreet_type' in meters_df.columns:
        on_street_meters = meters_df[meters_df['on_offstreet_type'].str.upper() == 'ON']
        print(f"\n✓ Found {len(on_street_meters)} ON STREET meters")
        print(f"  Off-street meters: {len(meters_df) - len(on_street_meters)}")
    else:
        print("\n⚠ No 'on_offstreet_type' field found")
        print("  Assuming all meters are on-street for analysis")
        on_street_meters = meters_df
    
    # 3. Check CNN coverage
    print("\n3. Checking CNN coverage for ON STREET meters...")
    print("-"*80)
    
    has_cnn = on_street_meters['street_seg_ctrln_id'].notna().sum()
    total_on_street = len(on_street_meters)
    
    print(f"ON STREET meters with CNN: {has_cnn}/{total_on_street} ({has_cnn/total_on_street*100:.2f}%)")
    
    if has_cnn < total_on_street:
        missing_cnn = on_street_meters[on_street_meters['street_seg_ctrln_id'].isna()]
        print(f"\n⚠ {len(missing_cnn)} ON STREET meters WITHOUT CNN:")
        print("\nSample meters without CNN:")
        for i in range(min(5, len(missing_cnn))):
            meter = missing_cnn.iloc[i]
            print(f"  - Post ID: {meter.get('post_id')}, Street: {meter.get('street_name')} {meter.get('street_num')}")
    
    # 4. Check blockface_id coverage
    print("\n4. Checking blockface_id coverage for ON STREET meters...")
    print("-"*80)
    
    has_blockface = on_street_meters['blockface_id'].notna().sum()
    print(f"ON STREET meters with blockface_id: {has_blockface}/{total_on_street} ({has_blockface/total_on_street*100:.2f}%)")
    
    if has_blockface < total_on_street:
        missing_blockface = on_street_meters[on_street_meters['blockface_id'].isna()]
        print(f"\n⚠ {len(missing_blockface)} ON STREET meters WITHOUT blockface_id")
    
    # 5. Check if meters with CNN can be matched to active streets
    print("\n5. Validating CNN matches against Active Streets...")
    print("-"*80)
    
    # Fetch active streets
    print("Fetching active streets (CNN backbone)...")
    streets = client.get(STREETS_DATASET_ID, limit=50000)
    streets_df = pd.DataFrame.from_records(streets)
    
    valid_cnns = set(streets_df['cnn'].dropna().astype(str))
    print(f"✓ Loaded {len(valid_cnns)} unique CNNs from active streets")
    
    # Check meter CNNs against valid CNNs
    meters_with_cnn = on_street_meters[on_street_meters['street_seg_ctrln_id'].notna()]
    meter_cnns = set(meters_with_cnn['street_seg_ctrln_id'].astype(str))
    
    valid_meter_cnns = meter_cnns.intersection(valid_cnns)
    invalid_meter_cnns = meter_cnns - valid_cnns
    
    print(f"\nMeter CNNs that exist in Active Streets: {len(valid_meter_cnns)}/{len(meter_cnns)}")
    
    if invalid_meter_cnns:
        print(f"⚠ {len(invalid_meter_cnns)} meter CNNs NOT found in Active Streets:")
        print(f"  Sample invalid CNNs: {list(invalid_meter_cnns)[:5]}")
    
    # 6. Fetch metered blockfaces to check mapping
    print("\n6. Checking Metered Blockfaces dataset...")
    print("-"*80)
    
    metered_bf = client.get(METERED_BLOCKFACES_ID, limit=50000)
    metered_bf_df = pd.DataFrame.from_records(metered_bf)
    
    print(f"✓ Loaded {len(metered_bf_df)} metered blockface records")
    print(f"  Columns: {list(metered_bf_df.columns)}")
    
    # Check if metered blockfaces have CNN
    if 'cnn' in metered_bf_df.columns or 'cnn_id' in metered_bf_df.columns:
        cnn_field = 'cnn' if 'cnn' in metered_bf_df.columns else 'cnn_id'
        has_cnn_bf = metered_bf_df[cnn_field].notna().sum()
        print(f"  Metered blockfaces with CNN: {has_cnn_bf}/{len(metered_bf_df)} ({has_cnn_bf/len(metered_bf_df)*100:.2f}%)")
    
    # 7. FINAL ANALYSIS
    print("\n" + "="*80)
    print("FINAL ANALYSIS: CAN WE MATCH 100% OF ON STREET METERS?")
    print("="*80)
    
    # Calculate matchability
    meters_with_valid_cnn = on_street_meters[
        on_street_meters['street_seg_ctrln_id'].notna() &
        on_street_meters['street_seg_ctrln_id'].astype(str).isin(valid_cnns)
    ]
    
    matchable_count = len(meters_with_valid_cnn)
    matchable_pct = matchable_count / total_on_street * 100
    
    print(f"\nON STREET Meters: {total_on_street}")
    print(f"Matchable to CNN (have valid CNN): {matchable_count} ({matchable_pct:.2f}%)")
    print(f"NOT matchable: {total_on_street - matchable_count} ({100-matchable_pct:.2f}%)")
    
    if matchable_pct < 100:
        print(f"\n⚠ CRITICAL: {100-matchable_pct:.2f}% of ON STREET meters CANNOT be matched!")
        print("\nReasons for unmatchable meters:")
        
        unmatchable = on_street_meters[
            ~(on_street_meters['street_seg_ctrln_id'].notna() &
              on_street_meters['street_seg_ctrln_id'].astype(str).isin(valid_cnns))
        ]
        
        no_cnn = unmatchable[unmatchable['street_seg_ctrln_id'].isna()]
        invalid_cnn = unmatchable[unmatchable['street_seg_ctrln_id'].notna()]
        
        print(f"  - No CNN field: {len(no_cnn)} meters")
        print(f"  - Invalid CNN (not in Active Streets): {len(invalid_cnn)} meters")
        
        print("\nSample unmatchable meters:")
        for i in range(min(10, len(unmatchable))):
            meter = unmatchable.iloc[i]
            print(f"  {i+1}. Post: {meter.get('post_id')}, "
                  f"Street: {meter.get('street_name')} {meter.get('street_num')}, "
                  f"CNN: {meter.get('street_seg_ctrln_id')}, "
                  f"Blockface: {meter.get('blockface_id')}")
    else:
        print(f"\n✓ SUCCESS: 100% of ON STREET meters can be matched to CNNs!")
    
    # 8. Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if matchable_pct < 100:
        print("\n1. INVESTIGATE unmatchable meters:")
        print("   - Are these meters truly on-street?")
        print("   - Are the CNNs outdated/incorrect in the meters dataset?")
        print("   - Do we need to update the Active Streets dataset?")
        
        print("\n2. FALLBACK STRATEGY for unmatchable meters:")
        print("   - Use street name + address matching")
        print("   - Use spatial proximity (lat/lon)")
        print("   - Manual review and correction")
        
        print("\n3. DATA QUALITY:")
        print("   - Report unmatchable meters to SFMTA")
        print("   - Request CNN updates for these meters")
    else:
        print("\n✓ Current data quality is sufficient for 100% meter matching")
    
    client.close()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    analyze_on_street_meter_coverage()