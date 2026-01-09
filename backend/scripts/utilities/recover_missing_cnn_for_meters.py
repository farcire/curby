 """
Attempt to recover missing CNNs for the 14 unmatched meters
by matching against Active Streets dataset using street name + address range.
"""
import os
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
from pymongo import MongoClient
import re

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METERS_DATASET_ID = "8vzz-qzz9"
METERED_BLOCKFACES_ID = "mk27-a5x2"
STREETS_DATASET_ID = "3psu-pn9h"  # Active Streets - Master CNN dataset

def fetch_data_as_dataframe(dataset_id: str, app_token: str, limit: int = 200000) -> pd.DataFrame:
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(dataset_id, limit=limit)
        df = pd.DataFrame.from_records(results)
        return df
    except Exception as e:
        print(f"Error fetching dataset {dataset_id}: {e}")
        return pd.DataFrame()

def normalize_street_name(name):
    """Normalize street name for matching."""
    if not name or pd.isna(name):
        return ""
    name = str(name).upper().strip()
    # Remove common suffixes for matching
    name = name.replace(" STREET", " ST")
    name = name.replace(" AVENUE", " AVE")
    return name

def extract_address_number(addr_str):
    """Extract numeric part of address."""
    if not addr_str or pd.isna(addr_str):
        return None
    try:
        return int(re.sub(r'\D', '', str(addr_str)))
    except:
        return None

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    
    # Load all datasets
    print("Loading Active Streets (Master CNN dataset)...")
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token)
    print(f"Loaded {len(streets_df)} street segments")
    
    print("\nLoading Metered Blockfaces...")
    metered_blockfaces_df = fetch_data_as_dataframe(METERED_BLOCKFACES_ID, app_token)
    
    print("\nLoading Meters...")
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    
    # Find the 14 meters with missing CNNs (excluding the test record 000-00000)
    unmatched_meters = meters_df[
        (meters_df['street_seg_ctrln_id'].isna()) & 
        (meters_df['post_id'] != '000-00000')
    ]
    
    print(f"\n=== Found {len(unmatched_meters)} meters with missing CNNs ===\n")
    
    recovered_count = 0
    
    for idx, meter in unmatched_meters.iterrows():
        post_id = meter.get('post_id')
        blockface_id = str(meter.get('blockface_id'))
        meter_street_num = meter.get('street_num')
        meter_street_name = meter.get('street_name')
        
        print(f"Meter {post_id}: {meter_street_num} {meter_street_name}")
        
        # Get side from metered blockfaces
        bf_match = metered_blockfaces_df[metered_blockfaces_df['blockface_id'] == blockface_id]
        
        if bf_match.empty:
            print(f"  ✗ Blockface {blockface_id} not found")
            continue
        
        bf = bf_match.iloc[0]
        side = bf.get('str_seg_orientation')
        bf_street_name = bf.get('street_name')
        bf_from_addr = bf.get('fm_addr_no')
        bf_to_addr = bf.get('to_addr_no')
        
        print(f"  Blockface: {bf_street_name} {side}, range {bf_from_addr}-{bf_to_addr}")
        
        # Try to find matching CNN in Active Streets
        # Match by: street name + address range overlap + side
        norm_bf_street = normalize_street_name(bf_street_name)
        
        # Filter streets by name
        street_matches = streets_df[
            streets_df['streetname'].apply(normalize_street_name) == norm_bf_street
        ]
        
        print(f"  Found {len(street_matches)} streets matching '{bf_street_name}'")
        
        # Check address range overlap
        bf_from_num = extract_address_number(bf_from_addr)
        bf_to_num = extract_address_number(bf_to_addr)
        
        if bf_from_num is None or bf_to_num is None:
            print(f"  ✗ Cannot parse blockface address range")
            continue
        
        # Check both left and right sides of each CNN
        for _, street in street_matches.iterrows():
            cnn = street.get('cnn')
            
            # Check left side
            lf_from = extract_address_number(street.get('lf_fadd'))
            lf_to = extract_address_number(street.get('lf_toadd'))
            
            if lf_from and lf_to and side == 'L':
                # Check if ranges overlap
                if not (bf_to_num < lf_from or bf_from_num > lf_to):
                    print(f"  ✓ MATCH FOUND: CNN {cnn}, side L, range {lf_from}-{lf_to}")
                    recovered_count += 1
                    break
            
            # Check right side
            rt_from = extract_address_number(street.get('rt_fadd'))
            rt_to = extract_address_number(street.get('rt_toadd'))
            
            if rt_from and rt_to and side == 'R':
                # Check if ranges overlap
                if not (bf_to_num < rt_from or bf_from_num > rt_to):
                    print(f"  ✓ MATCH FOUND: CNN {cnn}, side R, range {rt_from}-{rt_to}")
                    recovered_count += 1
                    break
        else:
            print(f"  ✗ No matching CNN found in Active Streets")
        
        print()
    
    print(f"\n=== Summary ===")
    print(f"Total meters with missing CNNs: {len(unmatched_meters)}")
    print(f"Successfully recovered CNNs: {recovered_count}")
    print(f"Still unmatched: {len(unmatched_meters) - recovered_count}")
    
    if recovered_count > 0:
        print(f"\n✓ We CAN recover {recovered_count} meters by matching against Active Streets!")
        print(f"  This would improve success rate from 99.96% to {(38341 + recovered_count) / 38356 * 100:.2f}%")

if __name__ == "__main__":
    main()