#!/usr/bin/env python3
"""
Analyze multiple parking regulations at the same location using geometry overlap.
Query Socrata API directly and identify regulations with overlapping geometries.
"""

import requests
import json
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import os

# Get API token from environment
SFMTA_APP_TOKEN = os.getenv('SFMTA_APP_TOKEN', 'ApbiUQbkvnyKHOVCHUw1Dh4ic')

# Mission district coordinates
TEST_LAT = 37.7526
TEST_LNG = -122.4107
SEARCH_RADIUS = 50  # meters

def query_socrata_regulations(lat: float, lng: float, radius: int) -> List[Dict[str, Any]]:
    """Query Socrata API for parking regulations near a location."""
    
    url = "https://data.sfgov.org/resource/hi6h-neyh.json"
    
    # Calculate bounding box
    lat_offset = radius / 111000  # rough conversion to degrees
    lng_offset = radius / (111000 * 0.8)  # adjust for latitude
    
    min_lat = lat - lat_offset
    max_lat = lat + lat_offset
    min_lng = lng - lng_offset
    max_lng = lng + lng_offset
    
    # Query with bounding box
    where_clause = (
        f"latitude > {min_lat} AND latitude < {max_lat} AND "
        f"longitude > {min_lng} AND longitude < {max_lng}"
    )
    
    headers = {}
    if SFMTA_APP_TOKEN:
        headers['X-App-Token'] = SFMTA_APP_TOKEN
    
    try:
        response = requests.get(
            url,
            params={
                "$where": where_clause,
                "$limit": 1000
            },
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying Socrata: {e}")
        return []

def extract_geometry_key(reg: Dict[str, Any]) -> Tuple:
    """Extract a hashable key from geometry for grouping."""
    
    geom = reg.get('the_geom')
    if not geom or not isinstance(geom, dict):
        return None
    
    coords = geom.get('coordinates', [])
    if not coords or not isinstance(coords, list):
        return None
    
    # For LineString, use first and last points
    if len(coords) >= 2:
        first = tuple(coords[0]) if isinstance(coords[0], list) else coords[0]
        last = tuple(coords[-1]) if isinstance(coords[-1], list) else coords[-1]
        
        # Round to 5 decimal places (~1 meter precision)
        if isinstance(first, tuple) and len(first) >= 2:
            first_rounded = (round(first[0], 5), round(first[1], 5))
        else:
            first_rounded = first
            
        if isinstance(last, tuple) and len(last) >= 2:
            last_rounded = (round(last[0], 5), round(last[1], 5))
        else:
            last_rounded = last
        
        return (first_rounded, last_rounded)
    
    return None

def geometries_overlap(geom1: Dict, geom2: Dict, tolerance: float = 0.00001) -> bool:
    """Check if two geometries overlap within tolerance (~1 meter)."""
    
    if not geom1 or not geom2:
        return False
    
    coords1 = geom1.get('coordinates', [])
    coords2 = geom2.get('coordinates', [])
    
    if not coords1 or not coords2:
        return False
    
    # Check if any points are within tolerance
    for c1 in coords1:
        if not isinstance(c1, list) or len(c1) < 2:
            continue
        for c2 in coords2:
            if not isinstance(c2, list) or len(c2) < 2:
                continue
            
            # Calculate distance
            dist = ((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)**0.5
            if dist < tolerance:
                return True
    
    return False

def analyze_overlapping_regulations(regulations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Group regulations by overlapping geometries."""
    
    print(f"\nAnalyzing {len(regulations)} regulations for geometry overlaps...")
    
    # Group by geometry key
    by_geometry = defaultdict(list)
    no_geometry = []
    
    for reg in regulations:
        geom_key = extract_geometry_key(reg)
        if geom_key:
            by_geometry[geom_key].append(reg)
        else:
            no_geometry.append(reg)
    
    print(f"  Unique geometry keys: {len(by_geometry)}")
    print(f"  Regulations without geometry: {len(no_geometry)}")
    
    # Find groups with multiple regulations
    multi_reg_groups = {key: regs for key, regs in by_geometry.items() if len(regs) > 1}
    print(f"  Geometry groups with multiple regulations: {len(multi_reg_groups)}")
    
    if len(by_geometry) > 0:
        percentage = len(multi_reg_groups) / len(by_geometry) * 100
        print(f"  Percentage: {percentage:.1f}%")
    
    # Distribution
    reg_counts = defaultdict(int)
    for regs in by_geometry.values():
        reg_counts[len(regs)] += 1
    
    print(f"\n  Distribution of regulations per geometry:")
    for count in sorted(reg_counts.keys()):
        print(f"    {count} regulation(s): {reg_counts[count]} geometries")
    
    return {
        'total_regulations': len(regulations),
        'unique_geometries': len(by_geometry),
        'multi_reg_geometries': len(multi_reg_groups),
        'no_geometry': len(no_geometry),
        'groups': multi_reg_groups
    }

def analyze_regulation_conflicts(regs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze if regulations are complementary or conflicting."""
    
    # Extract key fields
    types = [r.get('regulationtype', 'Unknown') for r in regs]
    time_limits = [r.get('timelimit') for r in regs]
    days = [r.get('daysofweek') for r in regs]
    start_times = [r.get('starttime') for r in regs]
    end_times = [r.get('endtime') for r in regs]
    
    # Check for temporal overlap
    has_time_restrictions = sum(1 for d, s, e in zip(days, start_times, end_times) if d or s or e)
    
    # Check for conflicting types
    unique_types = set(types)
    conflicting = False
    
    if 'NO PARKING' in types:
        if any('PARKING' in t and 'NO' not in t for t in types):
            conflicting = True
    
    return {
        'types': types,
        'unique_types': list(unique_types),
        'time_limits': time_limits,
        'days': days,
        'has_time_restrictions': has_time_restrictions,
        'conflicting': conflicting,
        'complementary': has_time_restrictions > 1 and not conflicting
    }

def main():
    print("=" * 80)
    print("INVESTIGATING MULTIPLE PARKING REGULATIONS AT SAME LOCATION")
    print("Using Geometry Overlap Analysis")
    print("=" * 80)
    print(f"\nTest Location: Mission District")
    print(f"Coordinates: {TEST_LAT}, {TEST_LNG}")
    print(f"Search Radius: {SEARCH_RADIUS} meters")
    
    # Query Socrata API
    print("\nQuerying Socrata API...")
    regulations = query_socrata_regulations(TEST_LAT, TEST_LNG, SEARCH_RADIUS)
    
    if not regulations:
        print("No regulations found!")
        return
    
    print(f"Retrieved {len(regulations)} regulations")
    
    # Analyze overlaps
    analysis = analyze_overlapping_regulations(regulations)
    
    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES OF OVERLAPPING REGULATIONS")
    print("=" * 80)
    
    groups = analysis['groups']
    if not groups:
        print("\nNo overlapping regulations found in this area.")
        print("This suggests that multiple regulations at the same location are NOT common,")
        print("or they use different geometry representations.")
    else:
        examples = list(groups.items())[:5]
        
        for i, (geom_key, regs) in enumerate(examples, 1):
            print(f"\nExample {i}: {len(regs)} regulations at same geometry")
            print("-" * 80)
            print(f"Geometry: {geom_key[0]} to {geom_key[1]}")
            
            # Show each regulation
            for j, reg in enumerate(regs, 1):
                print(f"\n  Regulation {j}:")
                print(f"    Street: {reg.get('streetname', 'N/A')}")
                print(f"    Side: {reg.get('streetside', 'N/A')}")
                print(f"    Type: {reg.get('regulationtype', 'N/A')}")
                print(f"    Time Limit: {reg.get('timelimit', 'N/A')}")
                print(f"    Days: {reg.get('daysofweek', 'N/A')}")
                print(f"    Hours: {reg.get('starttime', 'N/A')} - {reg.get('endtime', 'N/A')}")
                
                # Show geometry details
                geom = reg.get('the_geom', {})
                if geom:
                    coords = geom.get('coordinates', [])
                    print(f"    Geometry: {geom.get('type', 'Unknown')} with {len(coords)} points")
            
            # Analyze conflicts
            conflict_analysis = analyze_regulation_conflicts(regs)
            print(f"\n  Analysis:")
            print(f"    Regulation types: {', '.join(conflict_analysis['unique_types'])}")
            print(f"    Time-restricted regulations: {conflict_analysis['has_time_restrictions']}")
            
            if conflict_analysis['conflicting']:
                print(f"    ⚠️  CONFLICTING regulations detected!")
            elif conflict_analysis['complementary']:
                print(f"    ✓ Complementary regulations (different time periods)")
            else:
                print(f"    ℹ️  Same regulation type, may be redundant")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY AND RECOMMENDATIONS")
    print("=" * 80)
    
    if analysis['multi_reg_geometries'] > 0:
        percentage = analysis['multi_reg_geometries'] / analysis['unique_geometries'] * 100
        print(f"\n✓ Multiple regulations at same location IS COMMON")
        print(f"  - {percentage:.1f}% of geometries have multiple regulations")
        print(f"  - This appears to be NORMAL/EXPECTED behavior")
        print(f"\nReasons:")
        print(f"  1. Different time periods (e.g., 2hr parking 9am-6pm, no parking 6pm-9am)")
        print(f"  2. Different days (e.g., street cleaning on Tuesdays, regular parking other days)")
        print(f"  3. Layered restrictions (e.g., RPP + time limit + street cleaning)")
    else:
        print(f"\n✗ Multiple regulations at same location are RARE")
        print(f"  - Only {analysis['multi_reg_geometries']} out of {analysis['unique_geometries']} geometries")
        print(f"  - This could indicate:")
        print(f"    1. Regulations are well-separated spatially")
        print(f"    2. Dataset uses different geometry representations for same location")
        print(f"    3. Data quality issue (missing or incorrect geometries)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()