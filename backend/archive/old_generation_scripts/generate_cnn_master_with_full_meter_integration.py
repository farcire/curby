#!/usr/bin/env python3
"""
Generate CNN Master File with Full Meter Integration

This script implements the planned architecture from METER_OPERATING_SCHEDULES_INVESTIGATION_SUMMARY.md:

1. Creates CNN master reference with L/R entries from Active Streets (3psu-pn9h)
2. Fetches Meter Operating Schedules (6cqg-dxku) - baseline schedules
3. Fetches Special Event Areas (itv4-r6g6) - for flagging special event meters
4. Maps parking meters (8vzz-qzz9) to CNN L/R entries with:
   - Address-based matching (PRIMARY)
   - CNN fallback (when address missing)
   - Embedded operating schedules with priority sorting (TOW > ALTERNATE > OP + PRE > FREE)
   - Cap color normalization (YELLOW/RED = Commercial, others = Standard)
   - Special event meter flags
5. Outputs single CNN master file with all meter data embedded

Architecture:
- Static data (CNN Master): Streets + Meters + Base Schedules + Special Event Flags + Cap Colors
- Dynamic data (separate): Meter Policies (qq7v-hds4) - updated via cron

Cap Color Rules (Revised Dec 31, 2024):
- YELLOW = Commercial Vehicles only
- RED = Commercial Vehicles only (same as YELLOW)
- BLACK/GREY/GREEN = Standard parking
- Blockface-level aggregation uses majority rule
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
from shapely.geometry import Point, shape

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regulation_normalizer import (
    normalize_cap_color,
    prioritize_meter_schedules,
    aggregate_blockface_cap_colors,
    aggregate_blockface_tow_schedules
)

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

# Dataset configuration
ACTIVE_STREETS_ID = "3psu-pn9h"
PARKING_METERS_ID = "8vzz-qzz9"
METER_SCHEDULES_ID = "6cqg-dxku"
SPECIAL_EVENT_AREAS_ID = "itv4-r6g6"
OUTPUT_MASTER_FILE = "cnn_master_reference.json"
OUTPUT_MASTER_CSV = "cnn_master_reference.csv"

def fetch_active_streets():
    """Fetch all active streets from SFMTA Socrata API"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("ERROR: SFMTA_APP_TOKEN not found in environment")
        sys.exit(1)
    
    client = Socrata("data.sfgov.org", app_token)
    
    print("="*80)
    print("CNN MASTER FILE GENERATION WITH FULL METER INTEGRATION")
    print("="*80)
    print(f"\nStep 1: Fetching Active Streets ({ACTIVE_STREETS_ID})")
    print(f"Filter: active='True' OR active IS NULL")
    
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

def fetch_meter_schedules():
    """Fetch all meter operating schedules"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print(f"\nStep 2: Fetching Meter Operating Schedules ({METER_SCHEDULES_ID})")
    
    all_records = []
    offset = 0
    batch_size = 50000
    
    while True:
        print(f"  Batch at offset {offset}...")
        batch = client.get(METER_SCHEDULES_ID, limit=batch_size, offset=offset)
        
        if not batch:
            break
        
        all_records.extend(batch)
        print(f"  Retrieved {len(batch)} records (total: {len(all_records)})")
        
        if len(batch) < batch_size:
            break
        
        offset += batch_size
    
    print(f"\n✓ Total meter schedules fetched: {len(all_records)}")
    
    # Group schedules by post_id
    schedules_by_post = {}
    for record in all_records:
        post_id = record.get('post_id')
        if post_id:
            if post_id not in schedules_by_post:
                schedules_by_post[post_id] = []
            
            schedules_by_post[post_id].append({
                'schedule_type': record.get('schedule_type'),
                'days_applied': record.get('days_applied'),
                'from_time': record.get('beg_time_dt'),
                'to_time': record.get('end_time_dt'),
                'time_limit': record.get('time_limit_minutes'),
                'rate': record.get('rate'),
                'cap_color': record.get('cap_color'),
                'vehicle_type': record.get('vehicle_type')
            })
    
    print(f"✓ Grouped schedules for {len(schedules_by_post)} unique postIDs")
    return schedules_by_post

def fetch_special_event_areas():
    """Fetch special event area boundaries"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print(f"\nStep 3: Fetching Special Event Areas ({SPECIAL_EVENT_AREAS_ID})")
    
    geo_data = client.get(SPECIAL_EVENT_AREAS_ID, limit=50000)
    geo_df = pd.DataFrame.from_records(geo_data)
    
    print(f"✓ Fetched {len(geo_df)} geo boundary records")
    
    # Parse geometries
    geo_shapes = []
    for idx, row in geo_df.iterrows():
        if 'shape' in row and row['shape']:
            try:
                if isinstance(row['shape'], str):
                    geom_data = json.loads(row['shape'])
                else:
                    geom_data = row['shape']
                
                geom = shape(geom_data)
                area_type = row.get('areatype', 'Unknown')
                geo_shapes.append({
                    'geometry': geom,
                    'areatype': area_type
                })
            except Exception as e:
                print(f"  ⚠ Error parsing shape: {e}")
    
    print(f"✓ Successfully parsed {len(geo_shapes)} boundary shapes")
    
    if geo_shapes:
        area_types = set(gs['areatype'] for gs in geo_shapes)
        print(f"  Area types: {', '.join(area_types)}")
    
    return geo_shapes

def fetch_parking_meters():
    """Fetch all active parking meters"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print(f"\nStep 4: Fetching Parking Meters ({PARKING_METERS_ID})")
    print(f"Filter: active_meter_flag='M' OR active_meter_flag='T'")
    
    all_records = []
    offset = 0
    batch_size = 50000
    
    while True:
        print(f"  Batch at offset {offset}...")
        batch = client.get(
            PARKING_METERS_ID,
            limit=batch_size,
            offset=offset,
            where="active_meter_flag='M' OR active_meter_flag='T'"
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

def check_special_event_meter(lon, lat, geo_shapes):
    """Check if meter location falls within special event area"""
    if not lon or not lat or not geo_shapes:
        return False, None
    
    try:
        point = Point(float(lon), float(lat))
        for gs in geo_shapes:
            if gs['geometry'].contains(point):
                return True, gs['areatype']
    except Exception:
        pass
    
    return False, None

def create_master_entries(record):
    """Create both L and R entries for a single CNN"""
    cnn = record.get('cnn')
    timestamp = datetime.utcnow().isoformat()
    
    geometry = record.get('line')
    
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
        'updated_at': timestamp,
        'meters': []  # Will be populated during meter matching
    }
    
    left_entry = {
        'id': f"{cnn}_L",
        'side': 'L',
        'from_addr': record.get('lf_fadd'),
        'to_addr': record.get('lf_toadd'),
        **common_fields
    }
    
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

def match_meter_to_cnn_lr(meter, master_index, schedules_by_post, geo_shapes):
    """
    Match a parking meter to a CNN L or R entry and attach full meter data.
    
    Returns: (matched_entry, meter_data) or (None, None)
    """
    post_id = meter.get('post_id')
    parking_space_id = meter.get('parking_space_id')
    street_num = meter.get('street_num')
    street_name = meter.get('street_name')
    street_seg_ctrln_id = meter.get('street_seg_ctrln_id')
    longitude = meter.get('longitude')
    latitude = meter.get('latitude')
    cap_color = meter.get('cap_color')
    
    # Check if special event meter
    is_special_event, area_type = check_special_event_meter(longitude, latitude, geo_shapes)
    
    # Get operating schedules and prioritize them (TOW > ALTERNATE > OP + PRE > FREE)
    base_schedules = schedules_by_post.get(post_id, [])
    prioritized_schedules = prioritize_meter_schedules(base_schedules)
    
    # Normalize cap color
    cap_normalized = normalize_cap_color(cap_color)
    
    # Build meter data object
    meter_data = {
        'post_id': post_id,
        'parking_space_id': parking_space_id,
        'cap_color': cap_color,  # Raw cap color
        'cap_color_normalized': cap_normalized,  # Normalized cap color data
        'location': {
            'type': 'Point',
            'coordinates': [float(longitude), float(latitude)] if longitude and latitude else None
        },
        'base_schedules': prioritized_schedules,  # Schedules sorted by priority
        'special_event_meter': is_special_event,
        'special_event_area': area_type if is_special_event else None
    }
    
    # Add special event policy if applicable
    if is_special_event:
        meter_data['special_event_policy'] = {
            'operating_hours': {
                'mon_sat': '9am-10pm',
                'special_event_sunday': '12pm-10pm'
            },
            'event_rate': '$12/hour',
            'event_schedule_url': 'https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule'
        }
    
    # PRIMARY METHOD: Address-based matching
    if street_num and street_name:
        try:
            street_num_int = int(street_num)
            normalized_street = normalize_street_name(street_name)
            
            if normalized_street in master_index:
                candidates = master_index[normalized_street]
                
                for entry in candidates:
                    from_addr = entry.get('from_addr')
                    to_addr = entry.get('to_addr')
                    
                    if from_addr and to_addr:
                        try:
                            from_int = int(from_addr)
                            to_int = int(to_addr)
                            
                            if min(from_int, to_int) <= street_num_int <= max(from_int, to_int):
                                return entry, meter_data
                        except (ValueError, TypeError):
                            continue
        except (ValueError, TypeError):
            pass
    
    # FALLBACK METHOD: CNN-based matching (cannot determine side without address)
    # For now, we'll skip these and log them
    return None, meter_data

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

def generate_master_file():
    """Main function to generate CNN master file with full meter integration"""
    
    # Step 1: Fetch Active Streets
    active_streets = fetch_active_streets()
    if not active_streets:
        print("ERROR: No data fetched from Active Streets")
        sys.exit(1)
    
    # Step 2: Fetch Meter Operating Schedules
    schedules_by_post = fetch_meter_schedules()
    
    # Step 3: Fetch Special Event Areas
    geo_shapes = fetch_special_event_areas()
    
    # Step 4: Fetch Parking Meters
    parking_meters = fetch_parking_meters()
    if not parking_meters:
        print("ERROR: No parking meters fetched")
        sys.exit(1)
    
    # Step 5: Generate master file entries
    print("\nStep 5: Generating CNN master file entries...")
    all_entries = []
    
    for i, record in enumerate(active_streets, 1):
        if i % 1000 == 0:
            print(f"  Processed {i}/{len(active_streets)} records...")
        
        entries = create_master_entries(record)
        all_entries.extend(entries)
    
    print(f"\n✓ Generated {len(all_entries):,} entries from {len(active_streets):,} CNNs")
    
    # Step 6: Build index for fast lookup
    print("\nStep 6: Building master file index...")
    master_index = build_master_index(all_entries)
    print(f"✓ Indexed {len(master_index)} unique street names")
    
    # Step 7: Map meters to CNN L/R and embed data
    print("\nStep 7: Mapping meters to CNN L/R entries and embedding data...")
    
    matched_count = 0
    unmatched_count = 0
    special_event_count = 0
    meters_with_schedules = 0
    meters_without_schedules = 0
    
    for i, meter in enumerate(parking_meters, 1):
        if i % 1000 == 0:
            print(f"  Processed {i}/{len(parking_meters)} meters...")
        
        entry, meter_data = match_meter_to_cnn_lr(meter, master_index, schedules_by_post, geo_shapes)
        
        if entry:
            entry['meters'].append(meter_data)
            matched_count += 1
            
            if meter_data['special_event_meter']:
                special_event_count += 1
            
            if meter_data['base_schedules']:
                meters_with_schedules += 1
            else:
                meters_without_schedules += 1
        else:
            unmatched_count += 1
    
    print(f"\n✓ Mapped {matched_count:,} meters to CNN entries")
    print(f"  - With operating schedules: {meters_with_schedules:,}")
    print(f"  - Without schedules: {meters_without_schedules:,}")
    print(f"  - Special event meters: {special_event_count:,}")
    print(f"  - Unmatched: {unmatched_count:,}")
    
    # Step 8: Aggregate blockface-level meter rules
    print("\nStep 8: Aggregating blockface-level meter rules...")
    entries_with_meters = 0
    entries_commercial_only = 0
    entries_with_tow = 0
    
    for entry in all_entries:
        if entry.get('meters'):
            entries_with_meters += 1
            
            # Aggregate TOW schedules
            tow_agg = aggregate_blockface_tow_schedules(entry['meters'])
            entry['towScheduleAggregation'] = tow_agg
            
            if tow_agg['has_tow']:
                entries_with_tow += 1
            
            # Aggregate cap colors
            cap_agg = aggregate_blockface_cap_colors(entry['meters'])
            entry['capColorAggregation'] = cap_agg
            
            if not cap_agg['eligible_for_standard_user']:
                entries_commercial_only += 1
            
            # Set blockface-level flags
            entry['hasHomogeneousTow'] = tow_agg['all_have_tow']
            entry['blockfaceRestriction'] = cap_agg['restriction_type']
            entry['eligibleForStandardUser'] = cap_agg['eligible_for_standard_user']
    
    print(f"✓ Aggregated rules for {entries_with_meters:,} metered entries")
    print(f"  - Commercial vehicles only: {entries_commercial_only:,}")
    print(f"  - With TOW schedules: {entries_with_tow:,}")
    print(f"  - Standard parking available: {entries_with_meters - entries_commercial_only:,}")
    
    # Step 9: Save master file
    print(f"\nStep 9: Saving master file to {OUTPUT_MASTER_FILE}...")
    with open(OUTPUT_MASTER_FILE, 'w') as f:
        json.dump(all_entries, f, indent=2, default=str)
    print(f"✓ Saved {len(all_entries):,} entries")
    
    # Save CSV (without nested meter data)
    print(f"\nSaving summary to {OUTPUT_MASTER_CSV}...")
    df_master = pd.DataFrame([{
        'id': e['id'],
        'cnn': e['cnn'],
        'side': e['side'],
        'streetname_gc': e['streetname_gc'],
        'from_addr': e['from_addr'],
        'to_addr': e['to_addr'],
        'zip_code': e['zip_code'],
        'neighborhood': e['neighborhood'],
        'meter_count': len(e['meters']),
        'has_special_event_meters': any(m['special_event_meter'] for m in e['meters']) if e['meters'] else False,
        'eligible_for_standard_user': e.get('eligibleForStandardUser', True),
        'blockface_restriction': e.get('blockfaceRestriction', 'NONE'),
        'has_tow_schedules': e.get('towScheduleAggregation', {}).get('has_tow', False)
    } for e in all_entries])
    df_master.to_csv(OUTPUT_MASTER_CSV, index=False)
    print(f"✓ Saved CSV summary")
    
    # Final summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"\nCNN Master File:")
    print(f"  Total entries: {len(all_entries):,}")
    print(f"  Unique CNNs: {len(active_streets):,}")
    print(f"  L entries: {sum(1 for e in all_entries if e['side'] == 'L'):,}")
    print(f"  R entries: {sum(1 for e in all_entries if e['side'] == 'R'):,}")
    print(f"\nMeter Integration:")
    print(f"  Total meters matched: {matched_count:,} ({matched_count/len(parking_meters)*100:.1f}%)")
    print(f"  Meters with schedules: {meters_with_schedules:,} ({meters_with_schedules/matched_count*100:.1f}%)")
    print(f"  Meters without schedules: {meters_without_schedules:,} ({meters_without_schedules/matched_count*100:.1f}%)")
    print(f"  Special event meters: {special_event_count:,} ({special_event_count/matched_count*100:.1f}%)")
    print(f"  Unmatched meters: {unmatched_count:,} ({unmatched_count/len(parking_meters)*100:.1f}%)")
    print(f"\nBlockface-Level Aggregation:")
    print(f"  Entries with meters: {entries_with_meters:,}")
    print(f"  Commercial vehicles only: {entries_commercial_only:,} ({entries_commercial_only/entries_with_meters*100:.1f}%)")
    print(f"  Standard parking available: {entries_with_meters - entries_commercial_only:,} ({(entries_with_meters - entries_commercial_only)/entries_with_meters*100:.1f}%)")
    print(f"  With TOW schedules: {entries_with_tow:,} ({entries_with_tow/entries_with_meters*100:.1f}%)")
    print(f"\nOutput files:")
    print(f"  {OUTPUT_MASTER_FILE}")
    print(f"  {OUTPUT_MASTER_CSV}")
    print("\n" + "="*80)

if __name__ == '__main__':
    generate_master_file()