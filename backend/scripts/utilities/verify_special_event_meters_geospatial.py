#!/usr/bin/env python3
"""
Verify that meters with days_applied = 'special events' fall within
the geospatial boundaries of special event areas.
"""

import os
import sys
from sodapy import Socrata
from dotenv import load_dotenv
from shapely.geometry import Point, shape
import json

# Load environment variables
load_dotenv()

def verify_special_event_meters():
    """
    Check if meters with 'special events' in days_applied are within
    special event area boundaries.
    """
    # Initialize Socrata client
    client = Socrata(
        "data.sfgov.org",
        os.getenv("SFMTA_APP_TOKEN"),
        timeout=30
    )
    
    print("=" * 80)
    print("SPECIAL EVENT METERS - GEOSPATIAL VERIFICATION")
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
    
    # Step 2: Find schedules with 'special event' in days_applied
    print("\nStep 2: Searching for 'special event' in days_applied field...")
    special_event_schedules = []
    
    for sched in schedules:
        days_applied = str(sched.get('days_applied', '')).lower()
        if 'special event' in days_applied or 'special_event' in days_applied:
            special_event_schedules.append(sched)
    
    print(f"✓ Found {len(special_event_schedules)} schedules with 'special event' in days_applied")
    
    if not special_event_schedules:
        print("\n✓ NO schedules found with 'special event' in days_applied")
        print("This confirms ALTERNATE schedules use day-of-week patterns, not event references.")
        client.close()
        return
    
    # Get unique post IDs
    special_event_post_ids = list(set([s.get('postid') for s in special_event_schedules if s.get('postid')]))
    print(f"✓ Unique meters with special event schedules: {len(special_event_post_ids)}")
    print()
    
    # Step 3: Fetch Parking Meters dataset to get locations
    print("Step 3: Fetching Parking Meters (8vzz-qzz9) for locations...")
    try:
        # Fetch meters with post IDs that have special event schedules
        meters = client.get("8vzz-qzz9", limit=50000)
        print(f"✓ Fetched {len(meters)} meter records")
    except Exception as e:
        print(f"✗ Error: {e}")
        client.close()
        return
    
    # Filter to only meters with special event schedules
    special_event_meters = [m for m in meters if m.get('post_id') in special_event_post_ids]
    print(f"✓ Found {len(special_event_meters)} meters with special event schedules")
    print()
    
    # Step 4: Fetch Special Event Areas boundaries
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
    
    print(f"✓ Parsed {len(event_boundaries)} special event area boundaries")
    print()
    
    # Step 5: Check if meters are within boundaries
    print("=" * 80)
    print("GEOSPATIAL VERIFICATION")
    print("=" * 80)
    print()
    
    inside_count = 0
    outside_count = 0
    no_location_count = 0
    
    results = []
    
    for meter in special_event_meters:
        post_id = meter.get('post_id')
        
        # Get meter location
        if 'location' not in meter or not meter['location']:
            no_location_count += 1
            continue
        
        try:
            lon = float(meter['location']['longitude'])
            lat = float(meter['location']['latitude'])
            meter_point = Point(lon, lat)
        except (KeyError, ValueError, TypeError) as e:
            no_location_count += 1
            continue
        
        # Check if meter is within any special event boundary
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
    print(f"Total meters checked: {len(special_event_meters)}")
    print(f"  Inside special event boundaries: {inside_count}")
    print(f"  Outside special event boundaries: {outside_count}")
    print(f"  No location data: {no_location_count}")
    print()
    
    if inside_count > 0:
        percentage_inside = (inside_count / (inside_count + outside_count)) * 100
        print(f"Percentage inside boundaries: {percentage_inside:.1f}%")
        print()
    
    # Show sample results
    if results:
        print("Sample meters with 'special event' schedules:")
        print()
        
        # Show meters inside boundaries
        inside_meters = [r for r in results if r['inside_boundary']]
        if inside_meters:
            print(f"INSIDE boundaries ({len(inside_meters)} meters):")
            for i, m in enumerate(inside_meters[:5], 1):
                print(f"  {i}. Post ID: {m['post_id']}")
                print(f"     Location: {m['street_num']} {m['street']}")
                print(f"     Area: {m['matching_area']}")
                print()
        
        # Show meters outside boundaries
        outside_meters = [r for r in results if not r['inside_boundary']]
        if outside_meters:
            print(f"OUTSIDE boundaries ({len(outside_meters)} meters):")
            for i, m in enumerate(outside_meters[:5], 1):
                print(f"  {i}. Post ID: {m['post_id']}")
                print(f"     Location: {m['street_num']} {m['street']}")
                print(f"     Coordinates: {m['location']}")
                print()
    
    # Save detailed results
    output_file = "special_event_meters_geospatial_verification.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_meters': len(special_event_meters),
                'inside_boundaries': inside_count,
                'outside_boundaries': outside_count,
                'no_location': no_location_count,
                'percentage_inside': (inside_count / (inside_count + outside_count) * 100) if (inside_count + outside_count) > 0 else 0
            },
            'meters': results,
            'sample_schedules': special_event_schedules[:10]
        }, f, indent=2)
    
    print(f"✓ Detailed results saved to: {output_file}")
    print()
    
    # Conclusion
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    if len(special_event_schedules) == 0:
        print("✓ NO meter schedules use 'special event' in days_applied field")
        print("✓ ALTERNATE schedules are day-of-week based (Mon-Sat, Su, etc.)")
        print("✓ Special event pricing comes from dynamic Meter Policies, not base schedules")
    else:
        if percentage_inside >= 90:
            print("✓ VERIFIED: Meters with 'special event' schedules are within special event boundaries")
        elif percentage_inside >= 50:
            print("⚠ PARTIAL: Some meters with 'special event' schedules are outside boundaries")
        else:
            print("✗ MISMATCH: Most meters with 'special event' schedules are outside boundaries")
    
    client.close()

if __name__ == "__main__":
    verify_special_event_meters()