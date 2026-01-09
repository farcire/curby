#!/usr/bin/env python3
"""
Apply meter rates from SFMTA Meter Rate Schedule (fwjv-32uk) to CNN Master dataset.

Matching Logic:
- Match by post_id (required)
- Match by days_applied (when specified in schedule)
- Match by from_time and to_time (when specified in schedule)

Data Quality Check:
- Identify any post_id with same days_applied + time range but different rates
"""

import json
import requests
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Dataset configuration
METER_RATE_SCHEDULE_ID = 'fwjv-32uk'
CNN_MASTER_FILE = 'cnn_master_reference.json'
OUTPUT_FILE = 'cnn_master_with_rates.json'
DUPLICATE_RATES_REPORT = 'duplicate_rate_conflicts.json'

def fetch_meter_rate_schedules() -> List[Dict]:
    """Fetch all meter rate schedule records from Socrata API."""
    url = f'https://data.sfgov.org/resource/{METER_RATE_SCHEDULE_ID}.json'
    
    print("Fetching Meter Rate Schedule data...")
    print(f"Dataset: {METER_RATE_SCHEDULE_ID}")
    print("=" * 80)
    
    all_records = []
    offset = 0
    limit = 50000  # Socrata max
    
    while True:
        params = {
            '$limit': limit,
            '$offset': offset,
            '$order': 'post_id'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        batch = response.json()
        
        if not batch:
            break
            
        all_records.extend(batch)
        print(f"Fetched {len(all_records)} records...")
        
        if len(batch) < limit:
            break
            
        offset += limit
    
    print(f"\nTotal records fetched: {len(all_records)}")
    return all_records


def check_duplicate_rates(rate_schedules: List[Dict]) -> Dict:
    """
    Check for post_ids with same days_applied + time range but different rates.
    
    Returns dict with conflicts found.
    """
    print("\n" + "=" * 80)
    print("CHECKING FOR DUPLICATE RATE CONFLICTS")
    print("=" * 80)
    
    # Group by post_id + days_applied + from_time + to_time
    rate_groups = defaultdict(list)
    
    for record in rate_schedules:
        post_id = record.get('post_id', '')
        days_applied = record.get('days_applied', '')
        from_time = record.get('from_time', '')
        to_time = record.get('to_time', '')
        rate = record.get('rate', '')
        
        # Create composite key
        key = (post_id, days_applied, from_time, to_time)
        rate_groups[key].append({
            'rate': rate,
            'record': record
        })
    
    # Find conflicts (same key, different rates)
    conflicts = []
    for key, rate_list in rate_groups.items():
        unique_rates = set(r['rate'] for r in rate_list)
        
        if len(unique_rates) > 1:
            post_id, days_applied, from_time, to_time = key
            conflicts.append({
                'post_id': post_id,
                'days_applied': days_applied,
                'from_time': from_time,
                'to_time': to_time,
                'conflicting_rates': list(unique_rates),
                'record_count': len(rate_list),
                'sample_records': rate_list[:3]  # First 3 for review
            })
    
    print(f"\nConflicts found: {len(conflicts)}")
    
    if conflicts:
        print("\n⚠️  WARNING: Found post_ids with same schedule but different rates!")
        print("These need manual review:\n")
        for i, conflict in enumerate(conflicts[:10], 1):  # Show first 10
            print(f"{i}. Post ID: {conflict['post_id']}")
            print(f"   Days: {conflict['days_applied']}")
            print(f"   Time: {conflict['from_time']} - {conflict['to_time']}")
            print(f"   Conflicting rates: {conflict['conflicting_rates']}")
            print(f"   Record count: {conflict['record_count']}")
            print()
        
        if len(conflicts) > 10:
            print(f"... and {len(conflicts) - 10} more conflicts")
    else:
        print("✓ No duplicate rate conflicts found")
    
    return {
        'total_conflicts': len(conflicts),
        'conflicts': conflicts
    }


def normalize_days_applied(days_str: str) -> str:
    """Normalize days_applied format for matching."""
    if not days_str:
        return ''
    # Remove spaces, convert to uppercase for consistent matching
    return days_str.replace(' ', '').upper()


def normalize_time(time_str: str) -> str:
    """Normalize time format for matching."""
    if not time_str:
        return ''
    # Remove spaces, convert to uppercase
    return time_str.replace(' ', '').upper()


def build_rate_lookup(rate_schedules: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Build lookup dictionary: post_id -> list of rate schedules.
    
    Each schedule includes days_applied, from_time, to_time, rate.
    """
    print("\n" + "=" * 80)
    print("BUILDING RATE LOOKUP TABLE")
    print("=" * 80)
    
    lookup = defaultdict(list)
    
    for record in rate_schedules:
        post_id = record.get('post_id', '').strip()
        if not post_id:
            continue
        
        schedule = {
            'days_applied': normalize_days_applied(record.get('days_applied', '')),
            'from_time': normalize_time(record.get('from_time', '')),
            'to_time': normalize_time(record.get('to_time', '')),
            'rate': record.get('rate', ''),
            'rate_type': record.get('rate_type', ''),
            'schedule_priority': record.get('schedule_priority', '')
        }
        
        lookup[post_id].append(schedule)
    
    print(f"Built lookup for {len(lookup)} unique post_ids")
    
    # Show statistics
    schedules_per_post = [len(schedules) for schedules in lookup.values()]
    print(f"Average schedules per post_id: {sum(schedules_per_post) / len(schedules_per_post):.1f}")
    print(f"Max schedules for a post_id: {max(schedules_per_post)}")
    
    return dict(lookup)


def match_rate_to_schedule(meter_schedule: Dict, rate_schedules: List[Dict]) -> str:
    """
    Match a meter's base_schedule to a rate from rate_schedules.
    
    Matching logic:
    1. If meter schedule has days_applied, match by days + time
    2. If no days_applied in meter schedule, use base rate (no days/time in rate schedule)
    3. Return rate or None if no match
    """
    meter_days = normalize_days_applied(meter_schedule.get('days_applied', ''))
    meter_from = normalize_time(meter_schedule.get('from_time', ''))
    meter_to = normalize_time(meter_schedule.get('to_time', ''))
    
    # Try exact match first (days + time)
    if meter_days:
        for rate_sched in rate_schedules:
            rate_days = rate_sched['days_applied']
            rate_from = rate_sched['from_time']
            rate_to = rate_sched['to_time']
            
            if (rate_days == meter_days and 
                rate_from == meter_from and 
                rate_to == meter_to):
                return rate_sched['rate']
    
    # Fallback: base rate (no days_applied, no time)
    for rate_sched in rate_schedules:
        if not rate_sched['days_applied'] and not rate_sched['from_time']:
            return rate_sched['rate']
    
    return None


def apply_rates_to_cnn_master(cnn_data: List[Dict], rate_lookup: Dict[str, List[Dict]]) -> Tuple[List[Dict], Dict]:
    """
    Apply rates to CNN master dataset.
    
    Returns: (updated_cnn_data, statistics)
    """
    print("\n" + "=" * 80)
    print("APPLYING RATES TO CNN MASTER")
    print("=" * 80)
    
    stats = {
        'total_segments': len(cnn_data),
        'segments_with_meters': 0,
        'total_meters': 0,
        'meters_with_schedules': 0,
        'schedules_matched': 0,
        'schedules_unmatched': 0,
        'meters_not_in_rate_dataset': 0
    }
    
    for segment in cnn_data:
        meters = segment.get('meters', [])
        
        if not meters:
            continue
        
        stats['segments_with_meters'] += 1
        
        for meter in meters:
            stats['total_meters'] += 1
            post_id = meter.get('post_id', '').strip()
            
            if not post_id:
                continue
            
            # Get rate schedules for this post_id
            rate_schedules = rate_lookup.get(post_id)
            
            if not rate_schedules:
                stats['meters_not_in_rate_dataset'] += 1
                continue
            
            # Apply rates to base_schedules
            base_schedules = meter.get('base_schedules', [])
            
            if not base_schedules:
                continue
            
            stats['meters_with_schedules'] += 1
            
            for schedule in base_schedules:
                # Match and apply rate
                rate = match_rate_to_schedule(schedule, rate_schedules)
                
                if rate:
                    schedule['rate'] = rate
                    stats['schedules_matched'] += 1
                else:
                    stats['schedules_unmatched'] += 1
    
    # Print statistics
    print(f"\nStatistics:")
    print(f"  Total segments: {stats['total_segments']}")
    print(f"  Segments with meters: {stats['segments_with_meters']}")
    print(f"  Total meters: {stats['total_meters']}")
    print(f"  Meters with schedules: {stats['meters_with_schedules']}")
    print(f"  Meters not in rate dataset: {stats['meters_not_in_rate_dataset']}")
    print(f"  Schedules matched: {stats['schedules_matched']}")
    print(f"  Schedules unmatched: {stats['schedules_unmatched']}")
    
    if stats['schedules_unmatched'] > 0:
        match_rate = (stats['schedules_matched'] / 
                     (stats['schedules_matched'] + stats['schedules_unmatched']) * 100)
        print(f"  Match rate: {match_rate:.1f}%")
    
    return cnn_data, stats


def main():
    """Main execution function."""
    print("METER RATE APPLICATION TO CNN MASTER")
    print("=" * 80)
    
    # Step 1: Fetch meter rate schedules
    rate_schedules = fetch_meter_rate_schedules()
    
    # Step 2: Check for duplicate rate conflicts
    conflict_report = check_duplicate_rates(rate_schedules)
    
    # Save conflict report
    with open(DUPLICATE_RATES_REPORT, 'w') as f:
        json.dump(conflict_report, f, indent=2)
    print(f"\nConflict report saved to: {DUPLICATE_RATES_REPORT}")
    
    # Step 3: Build rate lookup
    rate_lookup = build_rate_lookup(rate_schedules)
    
    # Step 4: Load CNN master
    print("\n" + "=" * 80)
    print("LOADING CNN MASTER")
    print("=" * 80)
    
    with open(CNN_MASTER_FILE, 'r') as f:
        cnn_data = json.load(f)
    
    print(f"Loaded {len(cnn_data)} segments from {CNN_MASTER_FILE}")
    
    # Step 5: Apply rates
    updated_cnn_data, stats = apply_rates_to_cnn_master(cnn_data, rate_lookup)
    
    # Step 6: Save updated CNN master
    print("\n" + "=" * 80)
    print("SAVING UPDATED CNN MASTER")
    print("=" * 80)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(updated_cnn_data, f, indent=2)
    
    print(f"Updated CNN master saved to: {OUTPUT_FILE}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if conflict_report['total_conflicts'] > 0:
        print(f"⚠️  {conflict_report['total_conflicts']} rate conflicts need manual review")
        print(f"   See: {DUPLICATE_RATES_REPORT}")
    else:
        print("✓ No rate conflicts found")
    
    print(f"\n✓ Applied rates to {stats['schedules_matched']} schedules")
    
    if stats['schedules_unmatched'] > 0:
        print(f"⚠️  {stats['schedules_unmatched']} schedules could not be matched")
    
    if stats['meters_not_in_rate_dataset'] > 0:
        print(f"⚠️  {stats['meters_not_in_rate_dataset']} meters not found in rate dataset")
    
    print(f"\n✓ Output file: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()