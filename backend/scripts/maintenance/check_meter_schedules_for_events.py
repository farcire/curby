#!/usr/bin/env python3
"""
Query Meter Operating Schedules dataset (6cqg-dxku) to check for
"event" or "evening" keywords in any field.
"""

import os
import sys
from sodapy import Socrata
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def search_meter_schedules_for_keywords():
    """
    Search Meter Operating Schedules for 'event' or 'evening' keywords.
    """
    # Initialize Socrata client
    client = Socrata(
        "data.sfgov.org",
        os.getenv("SFMTA_APP_TOKEN"),
        timeout=30
    )
    
    print("=" * 80)
    print("METER OPERATING SCHEDULES - EVENT/EVENING KEYWORD SEARCH")
    print("=" * 80)
    print()
    
    # Dataset: Meter Operating Schedules (6cqg-dxku)
    dataset_id = "6cqg-dxku"
    
    print(f"Fetching Meter Operating Schedules dataset ({dataset_id})...")
    print()
    
    # Fetch all records (or a large sample)
    try:
        # Get first 10000 records to search
        results = client.get(dataset_id, limit=10000)
        print(f"✓ Fetched {len(results)} schedule records")
        print()
        
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return
    
    # Search for keywords in all fields
    keywords = ['event', 'evening', 'EVENT', 'EVENING', 'Event', 'Evening']
    matches = []
    
    print("Searching for keywords: event, evening (case-insensitive)...")
    print()
    
    for record in results:
        record_matches = []
        
        # Check each field in the record
        for field, value in record.items():
            if value is None:
                continue
                
            value_str = str(value).lower()
            
            # Check for keywords
            if 'event' in value_str or 'evening' in value_str:
                record_matches.append({
                    'field': field,
                    'value': value,
                    'keyword_found': 'event' if 'event' in value_str else 'evening'
                })
        
        if record_matches:
            matches.append({
                'post_id': record.get('postid', 'N/A'),
                'schedule_type': record.get('schedule_type', 'N/A'),
                'days_applied': record.get('days_applied', 'N/A'),
                'from_time': record.get('from_time', 'N/A'),
                'to_time': record.get('to_time', 'N/A'),
                'matches': record_matches,
                'full_record': record
            })
    
    # Display results
    print("=" * 80)
    print("SEARCH RESULTS")
    print("=" * 80)
    print()
    
    if not matches:
        print("✓ NO RECORDS FOUND containing 'event' or 'evening' keywords")
        print()
        print("This confirms that ALTERNATE schedules are day-of-week based,")
        print("NOT event-based or evening-specific.")
    else:
        print(f"✓ FOUND {len(matches)} records containing 'event' or 'evening'")
        print()
        
        for i, match in enumerate(matches[:20], 1):  # Show first 20
            print(f"Match #{i}:")
            print(f"  Post ID: {match['post_id']}")
            print(f"  Schedule Type: {match['schedule_type']}")
            print(f"  Days Applied: {match['days_applied']}")
            print(f"  Time: {match['from_time']} - {match['to_time']}")
            print(f"  Keyword matches:")
            for m in match['matches']:
                print(f"    - Field '{m['field']}': {m['value']}")
                print(f"      (contains: {m['keyword_found']})")
            print()
        
        if len(matches) > 20:
            print(f"... and {len(matches) - 20} more matches")
            print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total records searched: {len(results)}")
    print(f"Records with 'event' or 'evening': {len(matches)}")
    print(f"Percentage: {len(matches) / len(results) * 100:.2f}%")
    print()
    
    # Breakdown by schedule type
    if matches:
        schedule_types = {}
        for match in matches:
            stype = match['schedule_type']
            schedule_types[stype] = schedule_types.get(stype, 0) + 1
        
        print("Breakdown by schedule type:")
        for stype, count in sorted(schedule_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {stype}: {count} records")
        print()
    
    # Save detailed results to file
    if matches:
        output_file = "meter_schedules_event_evening_matches.json"
        with open(output_file, 'w') as f:
            json.dump(matches, f, indent=2)
        print(f"✓ Detailed results saved to: {output_file}")
        print()
    
    # Also check for ALTERNATE schedules specifically
    print("=" * 80)
    print("ALTERNATE SCHEDULE ANALYSIS")
    print("=" * 80)
    print()
    
    alternate_schedules = [r for r in results if r.get('schedule_type') == 'ALTERNATE']
    print(f"Total ALTERNATE schedules: {len(alternate_schedules)}")
    
    alternate_with_keywords = [m for m in matches if m['schedule_type'] == 'ALTERNATE']
    print(f"ALTERNATE schedules with 'event'/'evening': {len(alternate_with_keywords)}")
    print()
    
    if alternate_schedules:
        # Show sample ALTERNATE schedules
        print("Sample ALTERNATE schedules (first 5):")
        for i, sched in enumerate(alternate_schedules[:5], 1):
            print(f"\n  #{i}:")
            print(f"    Post ID: {sched.get('postid', 'N/A')}")
            print(f"    Days Applied: {sched.get('days_applied', 'N/A')}")
            print(f"    Time: {sched.get('from_time', 'N/A')} - {sched.get('to_time', 'N/A')}")
            print(f"    Rate: ${sched.get('rate', 'N/A')}")
            print(f"    Time Limit: {sched.get('time_limit_minutes', 'N/A')} min")
    
    client.close()

if __name__ == "__main__":
    search_meter_schedules_for_keywords()