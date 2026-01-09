#!/usr/bin/env python3
"""
Generate CNN Master File with Meter Mapping

This script:
1. Creates CNN master reference with L/R entries from Active Streets (3psu-pn9h)
2. Maps parking meters (8vzz-qzz9) to CNN L/R entries using:
   - PRIMARY: street_num + street_name → address range matching
   - FALLBACK: street_seg_CNTRLN_ID → CNN mapping (when address missing)
3. Filters for active meters only (active_met='M' OR active_met='T')
4. Includes parking_space_id field for each meter

Based on analysis showing 100% of active streets have both L and R address data.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

# Dataset configuration
ACTIVE_STREETS_ID = "3psu-pn9h"
PARKING_METERS_ID = "8vzz-qzz9"
OUTPUT_MASTER_FILE = "cnn_master_reference.json"
OUTPUT_MASTER_CSV = "cnn_master_reference.csv"
OUTPUT_METER_MAPPING = "meter_to_cnn_mapping.json"
OUTPUT_METER_CSV = "meter_to_cnn_mapping.csv"

def fetch_active_streets():
    """Fetch all active streets from SFMTA Socrata API"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("ERROR: SFMTA_APP_TOKEN not found in environment")
        sys.exit(1)
    
    client = Socrata("data.sfgov.org", app_token)
    
    print("="*80)
    print("CNN MASTER FILE GENERATION WITH METER MAPPING")
    print("="*80)
    print(f"\nStep 1: Fetching Active Streets ({ACTIVE_STREETS_ID})")
    print(f"Filter: active='True' OR active IS NULL")
    
    # Fetch in batches
    all_records = []
    offset = 0
    batch_size = 50000
    
    while True:
        print(f"  Batch at offset {offset}...")
        
        batch = client.get(
            ACTIVE_STREETS_ID,
            limit=batch_size,
            offset=offset,
            where="active='True' OR active IS NULL"
        )
        
        if not batch:
            break
        
        all_records.extend(batch)
        print(f"  Retrieved {len(batch)} records (total: {len(all_records)})")
        
        if len(batch) < batch_size:
            break
        
        offset += batch_size
    
    print(f"\n✓ Total active streets fetched: {len(all_records)}")
    return all_records

def fetch_parking_meters():
    """Fetch all active parking meters from SFMTA Socrata API"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print(f"\nStep 2: Fetching Parking Meters ({PARKING_METERS_ID})")
    print(f"Filter: active_met='M' OR active_met='T'")
    
    # Fetch in batches
    all_records = []
    offset = 0
    batch_size = 50000
    
    while True:
        print(f"  Batch at offset {offset}...")
        
        batch = client.get(
            PARKING_METERS_ID,
            limit=batch_size,
            offset=offset,
            where="active_met='M' OR active_met='T'"
        )
        
        if not batch:
            break
        
        all_records.extend(batch)
        print(f"  Retrieved {len(batch)} records (total: {len(all_records)})")
        
        if len(batch) < batch_size:
            break
        
        offset += batch_size
    
    print(f"\n✓ Total active parking meters fetched: {len(all_records)}")
    return all_records

def create_master_entries(record):
    """
    Create both L and R entries for a single CNN.
    
    Args:
        record: Active Streets record from Socrata
        
    Returns:
        List of two dictionaries (L entry and R entry)
    """
    cnn = record.get('cnn')
    timestamp = datetime.utcnow().isoformat()
    
    # Extract geometry
    geometry = record.get('line')
    
    # CNN-level fields (same for both L and R)
    common_fields = {
        'cnn': cnn,
        'streetname_gc': record.get('streetname_gc'),
        'street': record.get('street'),
        'st_type': record.get('st_type'),
        'f_st': record.get('f_st'),
        't_st': record.get('t_st'),
        'zip_code': record.get('zip_code'),
        'neighborhood': record.get('nhood'),
        'analysis_neighborhood': record.get('analysis_neighborhood'),
        'supervisor_district': record.get('supervisor_district'),
        'geometry': geometry,
        'classcode': record.get('classcode'),
        'layer': record.get('layer'),
        'oneway': record.get('oneway'),
        'f_node_cnn': record.get('f_node_cnn'),
        't_node_cnn': record.get('t_node_cnn'),
        'accepted': record.get('accepted'),
        'active': record.get('active'),
        'date_added': record.get('date_added'),
        'gds_chg_id_add': record.get('gds_chg_id_add'),
        'source_dataset': 'active_streets',
        'created_at': timestamp,
        'updated_at': timestamp
    }
    
    # Create L entry (ODD addresses)
    left_entry = {
        'id': f"{cnn}_L",
        'side': 'L',
        'from_addr': record.get('lf_fadd'),
        'to_addr': record.get('lf_toadd'),
        **common_fields
    }
    
    # Create R entry (EVEN addresses)
    right_entry = {
        'id': f"{cnn}_R",
        'side': 'R',
        'from_addr': record.get('rt_fadd'),
        'to_addr': record.get('rt_toadd'),
        **common_fields
    }
    
    return [left_entry, right_entry]

def normalize_street_name(name):
    """Normalize street name for matching"""
    if not name:
        return None
    return str(name).upper().strip()

def match_meter_to_cnn_lr(meter, master_index):
    """
    Match a parking meter to a CNN L or R entry.
    
    PRIMARY METHOD: Use street_num + street_name to find address range
    FALLBACK METHOD: Use street_seg_CNTRLN_ID when address info missing
    
    Args:
        meter: Parking meter record
        master_index: Dictionary for fast lookup {streetname_gc: [entries]}
        
    Returns:
        Dictionary with match result
    """
    post_id = meter.get('post_id')
    parking_space_id = meter.get('parking_space_id')
    street_num = meter.get('street_num')
    street_name = meter.get('street_name')
    street_seg_ctrln_id = meter.get('street_seg_ctrln_id')
    active_met = meter.get('active_met')
    
    result = {
        'post_id': post_id,
        'parking_space_id': parking_space_id,
        'street_num': street_num,
        'street_name': street_name,
        'street_seg_ctrln_id': street_seg_ctrln_id,
        'active_met': active_met,
        'matched_cnn_lr_id': None,
        'matched_cnn': None,
        'matched_side': None,
        'match_method': None,
        'match_confidence': None
    }
    
    # PRIMARY METHOD: Address-based matching
    if street_num and street_name:
        try:
            street_num_int = int(street_num)
            normalized_street = normalize_street_name(street_name)
            
            # Look up entries for this street
            if normalized_street in master_index:
                candidates = master_index[normalized_street]
                
                # Find entry where street_num falls within address range
                for entry in candidates:
                    from_addr = entry.get('from_addr')
                    to_addr = entry.get('to_addr')
                    
                    if from_addr and to_addr:
                        try:
                            from_int = int(from_addr)
                            to_int = int(to_addr)
                            
                            # Check if street_num is within range
                            if min(from_int, to_int) <= street_num_int <= max(from_int, to_int):
                                result['matched_cnn_lr_id'] = entry['id']
                                result['matched_cnn'] = entry['cnn']
                                result['matched_side'] = entry['side']
                                result['match_method'] = 'address_range'
                                result['match_confidence'] = 'high'
                                return result
                        except (ValueError, TypeError):
                            continue
        except (ValueError, TypeError):
            pass
    
    # FALLBACK METHOD: CNN-based matching (when address info missing)
    if street_seg_ctrln_id and not result['matched_cnn_lr_id']:
        # street_seg_CNTRLN_ID maps to CNN, but we don't know which side
        # We'll need to use additional logic or mark as ambiguous
        result['matched_cnn'] = street_seg_ctrln_id
        result['matched_side'] = 'UNKNOWN'  # Cannot determine L or R without address
        result['matched_cnn_lr_id'] = None  # Cannot assign specific L/R entry
        result['match_method'] = 'cnn_fallback'
        result['match_confidence'] = 'low'
    
    return result

def build_master_index(master_entries):
    """Build index for fast street name lookup"""
    index = {}
    for entry in master_entries:
        street = entry.get('streetname_gc')
        if street:
            if street not in index:
                index[street] = []
            index[street].append(entry)
    return index

def generate_master_file_and_map_meters():
    """Main function to generate CNN master file and map meters"""
    
    # Step 1: Fetch Active Streets
    active_streets = fetch_active_streets()
    
    if not active_streets:
        print("ERROR: No data fetched from Active Streets")
        sys.exit(1)
    
    # Step 2: Generate master file entries
    print("\nStep 3: Generating CNN master file entries...")
    all_entries = []
    
    for i, record in enumerate(active_streets, 1):
        if i % 1000 == 0:
            print(f"  Processed {i}/{len(active_streets)} records...")
        
        entries = create_master_entries(record)
        all_entries.extend(entries)
    
    print(f"\n✓ Generated {len(all_entries):,} entries from {len(active_streets):,} CNNs")
    
    # Step 3: Save master file
    print(f"\nStep 4: Saving master file to {OUTPUT_MASTER_FILE}...")
    with open(OUTPUT_MASTER_FILE, 'w') as f:
        json.dump(all_entries, f, indent=2, default=str)
    print(f"✓ Saved {len(all_entries):,} entries")
    
    # Save CSV
    print(f"\nSaving master file to {OUTPUT_MASTER_CSV}...")
    df_master = pd.DataFrame(all_entries)
    df_master['geometry_type'] = df_master['geometry'].apply(lambda x: x.get('type') if isinstance(x, dict) else None)
    df_master = df_master.drop('geometry', axis=1)
    df_master.to_csv(OUTPUT_MASTER_CSV, index=False)
    print(f"✓ Saved CSV")
    
    # Step 4: Fetch parking meters
    parking_meters = fetch_parking_meters()
    
    if not parking_meters:
        print("ERROR: No parking meters fetched")
        sys.exit(1)
    
    # Step 5: Build index for fast lookup
    print("\nStep 5: Building master file index...")
    master_index = build_master_index(all_entries)
    print(f"✓ Indexed {len(master_index)} unique street names")
    
    # Step 6: Map meters to CNN L/R
    print("\nStep 6: Mapping meters to CNN L/R entries...")
    meter_mappings = []
    
    for i, meter in enumerate(parking_meters, 1):
        if i % 1000 == 0:
            print(f"  Processed {i}/{len(parking_meters)} meters...")
        
        mapping = match_meter_to_cnn_lr(meter, master_index)
        meter_mappings.append(mapping)
    
    print(f"\n✓ Mapped {len(meter_mappings):,} meters")
    
    # Step 7: Analyze mapping results
    print("\n" + "="*80)
    print("METER MAPPING ANALYSIS")
    print("="*80)
    
    total_meters = len(meter_mappings)
    address_matched = sum(1 for m in meter_mappings if m['match_method'] == 'address_range')
    cnn_fallback = sum(1 for m in meter_mappings if m['match_method'] == 'cnn_fallback')
    unmatched = sum(1 for m in meter_mappings if not m['match_method'])
    
    print(f"\nTotal meters: {total_meters:,}")
    print(f"Matched by address range: {address_matched:,} ({address_matched/total_meters*100:.1f}%)")
    print(f"Matched by CNN fallback: {cnn_fallback:,} ({cnn_fallback/total_meters*100:.1f}%)")
    print(f"Unmatched: {unmatched:,} ({unmatched/total_meters*100:.1f}%)")
    
    # Show examples of each type
    if address_matched > 0:
        print("\nExample: Address Range Match")
        example = next(m for m in meter_mappings if m['match_method'] == 'address_range')
        print(f"  Post ID: {example['post_id']}")
        print(f"  Parking Space ID: {example['parking_space_id']}")
        print(f"  Address: {example['street_num']} {example['street_name']}")
        print(f"  Matched to: {example['matched_cnn_lr_id']} (CNN {example['matched_cnn']}, Side {example['matched_side']})")
    
    if cnn_fallback > 0:
        print("\nExample: CNN Fallback Match")
        example = next(m for m in meter_mappings if m['match_method'] == 'cnn_fallback')
        print(f"  Post ID: {example['post_id']}")
        print(f"  Parking Space ID: {example['parking_space_id']}")
        print(f"  CNN: {example['matched_cnn']}")
        print(f"  Side: {example['matched_side']} (cannot determine without address)")
    
    if unmatched > 0:
        print("\nExample: Unmatched Meter")
        example = next(m for m in meter_mappings if not m['match_method'])
        print(f"  Post ID: {example['post_id']}")
        print(f"  Parking Space ID: {example['parking_space_id']}")
        print(f"  Street: {example['street_num']} {example['street_name']}")
        print(f"  CNN: {example['street_seg_ctrln_id']}")
    
    # Step 8: Save meter mappings
    print(f"\nStep 7: Saving meter mappings to {OUTPUT_METER_MAPPING}...")
    with open(OUTPUT_METER_MAPPING, 'w') as f:
        json.dump(meter_mappings, f, indent=2)
    print(f"✓ Saved {len(meter_mappings):,} meter mappings")
    
    # Save CSV
    print(f"\nSaving meter mappings to {OUTPUT_METER_CSV}...")
    df_meters = pd.DataFrame(meter_mappings)
    df_meters.to_csv(OUTPUT_METER_CSV, index=False)
    print(f"✓ Saved CSV")
    
    # Final summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"\nCNN Master File:")
    print(f"  Total entries: {len(all_entries):,}")
    print(f"  Unique CNNs: {len(active_streets):,}")
    print(f"  L entries: {sum(1 for e in all_entries if e['side'] == 'L'):,}")
    print(f"  R entries: {sum(1 for e in all_entries if e['side'] == 'R'):,}")
    print(f"\nMeter Mapping:")
    print(f"  Total meters: {total_meters:,}")
    print(f"  Successfully matched to L/R: {address_matched:,} ({address_matched/total_meters*100:.1f}%)")
    print(f"  CNN only (side unknown): {cnn_fallback:,} ({cnn_fallback/total_meters*100:.1f}%)")
    print(f"  Unmatched: {unmatched:,} ({unmatched/total_meters*100:.1f}%)")
    print(f"\nOutput files:")
    print(f"  {OUTPUT_MASTER_FILE}")
    print(f"  {OUTPUT_MASTER_CSV}")
    print(f"  {OUTPUT_METER_MAPPING}")
    print(f"  {OUTPUT_METER_CSV}")
    print("\n" + "="*80)

if __name__ == '__main__':
    generate_master_file_and_map_meters()