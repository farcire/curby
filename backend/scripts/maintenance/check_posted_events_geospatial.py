#!/usr/bin/env python3
"""
Check if meters with days_applied = 'posted events' fall within
special event area boundaries.
"""

import os
from sodapy import Socrata
from dotenv import load_dotenv
from shapely.geometry import Point, shape
import json

# Load environment variables
load_dotenv()

def check_posted_events_geospatial():
    """
    Verify meters with 'posted events' in days_applied are within
    special event boundaries.
    """
    client = Socrata(
        "data.sfgov.org",
        os.getenv("SFMTA_APP_TOKEN"),
        timeout=30
    )
    
    print("=" * 80)
    print("POSTED EVENTS - GEOSPATIAL VERIFICATION")
    print("=" * 80)
    print()
    
    # Step 1: Fetch Meter Operating Schedules
    print("Step 1: Fetching Meter Operating Schedules (6cqg-dxku)...")
    try:
        schedules = client.get("6cqg-dxku", limit=100000)
        print(f"✓ Fetched {len(schedules)} schedule records")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Step 2: Find schedules with 'posted events' in days_applied
    print("\nStep 2: Searching for 'posted events' in days_applied...")
    posted_event_schedules = []
    
    for sched in schedules:
        days_applied = str(sched.get('days_applied', '')).lower()
        if 'posted event' in days_applied or 'posted_event' in days_applied:
            posted_event_schedules.append(sched)
    
    print(f"✓ Found {len(posted_event_schedules)} schedules with 'posted events'")
    
    if not posted_event_schedules:
        print("\n✓ NO schedules found with 'posted events' in days_applied")
        print()
        
        # Show what days_applied patterns DO exist
        print("Checking for similar patterns...")
        event_related = []
        for sched in schedules:
            days = str(sched.get('days_applied', '')).lower()
            if 'event' in days or 'special' in days:
                event_related.append(sched)
        
        if event_related:
            print(f"\nFound {len(event_related)} schedules with 'event' or 'special' in days_applied:")
            unique_days = set([s.get('days_applied') for s in event_related])
            for days in sorted(unique_days):
                count = len([s for s in event_related if s.get('days_applied') == days])
                print(f"  '{days}': {count} schedules")
        else:
            print("\n✓ NO event-related patterns found in days_applied")
            print("✓ Confirms ALTERNATE schedules use standard day-of-week patterns")
        
        client.close()
        return
    
    # Get unique post IDs
    posted_event_post_ids = list(set([s.get('postid') for s in posted_event_schedules if s.get('postid')]))
    print(f"✓ Unique meters with 'posted events': {len(posted_event_post_ids)}")
    print()
    
    # Show sample schedules
    print("Sample 'posted events' schedules:")
    for i, sched in enumerate(posted_event_schedules[:5], 1):
        print(f"\n  #{i}:")
        print(f"    Post ID: {sched.get('postid')}")
        print(f"    Schedule Type: {sched.get('schedule_type')}")
        print(f"    Days Applied: {sched.get('days_applied')}")
        print(f"    Time: {sched.get('from_time')} - {sched.get('to_time')}")
        print(f"    Rate: ${sched.get('rate', 'N/A')}")
        print(f"    Cap Color: {sched.get('cap_color', 'N/A')}")
    print()
    
    # Step 3: Fetch Parking Meters for locations
    print("Step 3: Fetching Parking Meters (8vzz-qzz9)...")
    try:
        meters = client.get("8vzz-qzz9", limit=50000)
        print(f"✓ Fetched {len(meters)} meter records")
    except Exception as e:
        print(f"✗ Error: {e}")
        client.close()
        return
    
    # Filter to meters with posted events
    posted_event_meters = [m for m in meters if m.get('post_id') in posted_event_post_ids]
    print(f"✓ Found {len(posted_event_meters)} meters with 'posted events' schedules")
    print()
    
    # Step 4: Fetch Special Event Areas
    print("Step 4: Fetching Special Event Areas (itv4-r6g6)...")
    try:
        event_areas = client.get("itv4-r6g6", limit=100)
        print(f"✓ Fetched {len(event_areas)} special event area records")
    except Exception as e:
        print(f"✗ Error: {e}")
        client.close()
        return
    
    # Parse geometries
    event_boundaries = []
    for area in event_areas:
        if 'the_geom' in area:
            try:
                geom = shape(area['the_geom'])
                event_boundaries.append({
                    'name': area.get('name', 'Unknown'),
                    'geometry': geom
                })
            except Exception as e:
                print(f"  Warning: Could not parse geometry for {area.get('name')}: {e}")
    
    print(f"✓ Parsed {len(event_boundaries)} special event boundaries")
    print()
    
    # Step 5: Geospatial verification
    print("=" * 80)
    print("GEOSPATIAL VERIFICATION")
    print("=" * 80)
    print()
    
    inside_count = 0
    outside_count = 0
    no_location_count = 0
    results = []
    
    for meter in posted_event_meters:
        post_id = meter.get('post_id')
        
        # Get location
        if 'location' not in meter or not meter['location']:
            no_location_count += 1
            continue
        
        try:
            lon = float(meter['location']['longitude'])
            lat = float(meter['location']['latitude'])
            meter_point = Point(lon, lat)
        except (KeyError, ValueError, TypeError):
            no_location_count += 1
            continue
        
        # Check if within any boundary
        is_inside = False
        matching_area = None
        
        for boundary in event_boundaries:
            if boundary['geometry'].contains(meter_point):
                is_inside = True
                matching_area = boundary['name']
                break
        
        if is_inside:
            inside_count += 1
        else:
            outside_count += 1
        
        results.append({
            'post_id': post_id,
            'location': {'lon': lon, 'lat': lat},
            'inside_boundary': is_inside,
            'matching_area': matching_area,
            'street': meter.get('street_name', 'N/A'),
            'street_num': meter.get('street_num', 'N/A')
        })
    
    # Display results
    total_checked = inside_count + outside_count
    print(f"Total meters checked: {len(posted_event_meters)}")
    print(f"  Inside special event boundaries: {inside_count}")
    print(f"  Outside special event boundaries: {outside_count}")
    print(f"  No location data: {no_location_count}")
    
    if total_checked > 0:
        percentage_inside = (inside_count / total_checked) * 100
        print(f"\nPercentage inside boundaries: {percentage_inside:.1f}%")
    print()
    
    # Show samples
    if results:
        inside_meters = [r for r in results if r['inside_boundary']]
        outside_meters = [r for r in results if not r['inside_boundary']]
        
        if inside_meters:
            print(f"INSIDE boundaries ({len(inside_meters)} meters):")
            for i, m in enumerate(inside_meters[:5], 1):
                print(f"  {i}. {m['post_id']} - {m['street_num']} {m['street']}")
                print(f"     Area: {m['matching_area']}")
            print()
        
        if outside_meters:
            print(f"OUTSIDE boundaries ({len(outside_meters)} meters):")
            for i, m in enumerate(outside_meters[:5], 1):
                print(f"  {i}. {m['post_id']} - {m['street_num']} {m['street']}")
            print()
    
    # Save results
    output = {
        'summary': {
            'total_schedules': len(posted_event_schedules),
            'unique_meters': len(posted_event_post_ids),
            'meters_checked': len(posted_event_meters),
            'inside_boundaries': inside_count,
            'outside_boundaries': outside_count,
            'percentage_inside': (inside_count / total_checked * 100) if total_checked > 0 else 0
        },
        'sample_schedules': posted_event_schedules[:10],
        'meters': results
    }
    
    output_file = "posted_events_geospatial_verification.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Results saved to: {output_file}")
    print()
    
    # Conclusion
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    if len(posted_event_schedules) == 0:
        print("✓ NO 'posted events' pattern found in days_applied")
        print("✓ ALTERNATE schedules use standard day-of-week patterns")
        print("✓ Special event pricing handled separately via Meter Policies")
    else:
        if percentage_inside >= 90:
            print("✓ VERIFIED: 'Posted events' meters are within special event boundaries")
        elif percentage_inside >= 50:
            print("⚠ PARTIAL: Some 'posted events' meters outside boundaries")
        else:
            print("✗ MISMATCH: Most 'posted events' meters outside boundaries")
    
    client.close()

if __name__ == "__main__":
    check_posted_events_geospatial()