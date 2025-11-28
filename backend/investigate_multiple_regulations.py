#!/usr/bin/env python3
"""
Investigate if multiple parking regulations can apply to the same location.
Query the Parking Regulations dataset (hi6h-neyh) for a specific location
and analyze overlapping regulations.
"""

import requests
import json
from typing import List, Dict, Any
from collections import defaultdict

# Mission district coordinates (Balmy Street area)
TEST_LAT = 37.7526
TEST_LNG = -122.4107
SEARCH_RADIUS = 50  # meters

def query_local_api(lat: float, lng: float, radius: int) -> Dict[str, Any]:
    """Query the local API for blockfaces near a location."""
    try:
        response = requests.get(
            f"http://localhost:8000/api/v1/blockfaces?lat={lat}&lng={lng}&radius_meters={radius}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying local API: {e}")
        return {}

def query_socrata_api(lat: float, lng: float, radius: int) -> List[Dict[str, Any]]:
    """Query the Socrata API directly for parking regulations."""
    # Convert radius from meters to approximate degrees (rough approximation)
    # At SF latitude, 1 degree ≈ 111km, so radius_degrees ≈ radius_meters / 111000
    radius_degrees = radius / 111000
    
    # Build SoQL query with spatial filter
    url = "https://data.sfgov.org/resource/hi6h-neyh.json"
    
    # Use within_circle for spatial query
    query = f"$where=within_circle(the_geom, {lat}, {lng}, {radius})"
    
    try:
        response = requests.get(
            url,
            params={
                "$where": f"within_circle(the_geom, {lat}, {lng}, {radius})",
                "$limit": 1000
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying Socrata API: {e}")
        return []

def analyze_regulation_overlap(regulations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze if regulations overlap spatially and temporally."""
    
    # Group by CNN (street segment)
    by_cnn = defaultdict(list)
    for reg in regulations:
        cnn = reg.get('cnnid') or reg.get('cnn')
        if cnn:
            by_cnn[cnn].append(reg)
    
    # Group by approximate location (rounded coordinates)
    by_location = defaultdict(list)
    for reg in regulations:
        geom = reg.get('the_geom') or reg.get('geometry')
        if geom:
            # Extract coordinates
            if isinstance(geom, dict):
                coords = geom.get('coordinates', [])
                if coords and len(coords) >= 2:
                    # Round to 4 decimal places (~11 meters precision)
                    loc_key = (round(coords[1], 4), round(coords[0], 4))
                    by_location[loc_key].append(reg)
    
    analysis = {
        'total_regulations': len(regulations),
        'unique_cnns': len(by_cnn),
        'cnns_with_multiple_regs': 0,
        'unique_locations': len(by_location),
        'locations_with_multiple_regs': 0,
        'examples': []
    }
    
    # Find CNNs with multiple regulations
    for cnn, regs in by_cnn.items():
        if len(regs) > 1:
            analysis['cnns_with_multiple_regs'] += 1
            
            # Analyze the regulations
            reg_types = [r.get('regulation_type') or r.get('regulationtype') for r in regs]
            time_limits = [r.get('time_limit_minutes') or r.get('timelimit') for r in regs]
            days = [r.get('days_of_week') or r.get('daysofweek') for r in regs]
            hours = [(r.get('start_time') or r.get('starttime'), 
                     r.get('end_time') or r.get('endtime')) for r in regs]
            
            example = {
                'cnn': cnn,
                'num_regulations': len(regs),
                'regulation_types': reg_types,
                'time_limits': time_limits,
                'days_of_week': days,
                'hours': hours,
                'sample_regulation': regs[0]
            }
            
            if len(analysis['examples']) < 5:
                analysis['examples'].append(example)
    
    # Find locations with multiple regulations
    for loc, regs in by_location.items():
        if len(regs) > 1:
            analysis['locations_with_multiple_regs'] += 1
    
    return analysis

def check_regulation_conflicts(regs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Check if regulations are complementary or conflicting."""
    
    conflicts = []
    complementary = []
    
    for i, reg1 in enumerate(regs):
        for reg2 in regs[i+1:]:
            # Extract regulation details
            type1 = reg1.get('regulation_type') or reg1.get('regulationtype')
            type2 = reg2.get('regulation_type') or reg2.get('regulationtype')
            
            days1 = reg1.get('days_of_week') or reg1.get('daysofweek')
            days2 = reg2.get('days_of_week') or reg2.get('daysofweek')
            
            start1 = reg1.get('start_time') or reg1.get('starttime')
            end1 = reg1.get('end_time') or reg1.get('endtime')
            start2 = reg2.get('start_time') or reg2.get('starttime')
            end2 = reg2.get('end_time') or reg2.get('endtime')
            
            # Check for temporal overlap
            temporal_overlap = False
            if days1 and days2:
                # Simple check: if days are the same or overlap
                if days1 == days2:
                    temporal_overlap = True
            
            # Check for conflicting types
            conflicting_types = False
            if type1 and type2:
                # Examples of conflicting types
                if ('NO PARKING' in str(type1).upper() and 'PARKING' in str(type2).upper() and 'NO' not in str(type2).upper()):
                    conflicting_types = True
                elif ('NO STOPPING' in str(type1).upper() and 'PARKING' in str(type2).upper()):
                    conflicting_types = True
            
            comparison = {
                'reg1_type': type1,
                'reg2_type': type2,
                'temporal_overlap': temporal_overlap,
                'conflicting_types': conflicting_types,
                'reg1_days': days1,
                'reg2_days': days2,
                'reg1_hours': f"{start1}-{end1}" if start1 and end1 else None,
                'reg2_hours': f"{start2}-{end2}" if start2 and end2 else None
            }
            
            if conflicting_types and temporal_overlap:
                conflicts.append(comparison)
            elif not conflicting_types and temporal_overlap:
                complementary.append(comparison)
    
    return {
        'conflicts': conflicts,
        'complementary': complementary,
        'num_conflicts': len(conflicts),
        'num_complementary': len(complementary)
    }

def main():
    print("=" * 80)
    print("INVESTIGATING MULTIPLE PARKING REGULATIONS AT SAME LOCATION")
    print("=" * 80)
    print(f"\nTest Location: Mission District")
    print(f"Coordinates: {TEST_LAT}, {TEST_LNG}")
    print(f"Search Radius: {SEARCH_RADIUS} meters")
    print()
    
    # Query local API
    print("1. Querying Local API...")
    print("-" * 80)
    local_data = query_local_api(TEST_LAT, TEST_LNG, SEARCH_RADIUS)
    
    if local_data:
        blockfaces = local_data.get('blockfaces', [])
        print(f"Found {len(blockfaces)} blockface segments")
        
        # Collect all regulations
        all_regs = []
        for bf in blockfaces:
            regs = bf.get('parking_regulations', [])
            for reg in regs:
                reg['_blockface'] = {
                    'street_name': bf.get('street_name'),
                    'side': bf.get('side'),
                    'cnn': bf.get('cnn')
                }
                all_regs.append(reg)
        
        print(f"Total parking regulations: {len(all_regs)}")
        
        # Group by blockface
        by_blockface = defaultdict(list)
        for reg in all_regs:
            bf_key = (reg['_blockface']['street_name'], reg['_blockface']['side'])
            by_blockface[bf_key].append(reg)
        
        print(f"\nBlockfaces with multiple regulations:")
        for bf_key, regs in by_blockface.items():
            if len(regs) > 1:
                print(f"\n  {bf_key[0]} ({bf_key[1]} side): {len(regs)} regulations")
                for i, reg in enumerate(regs, 1):
                    print(f"    {i}. {reg.get('regulation_type')}")
                    if reg.get('time_limit_minutes'):
                        print(f"       Time Limit: {reg.get('time_limit_minutes')} min")
                    if reg.get('days_of_week'):
                        print(f"       Days: {reg.get('days_of_week')}")
                    if reg.get('start_time') and reg.get('end_time'):
                        print(f"       Hours: {reg.get('start_time')} - {reg.get('end_time')}")
                
                # Check for conflicts
                conflict_analysis = check_regulation_conflicts(regs)
                if conflict_analysis['num_conflicts'] > 0:
                    print(f"    ⚠️  CONFLICTS DETECTED: {conflict_analysis['num_conflicts']}")
                elif conflict_analysis['num_complementary'] > 0:
                    print(f"    ✓ Complementary regulations: {conflict_analysis['num_complementary']}")
    
    print("\n" + "=" * 80)
    print("2. Querying Socrata API Directly...")
    print("-" * 80)
    
    socrata_regs = query_socrata_api(TEST_LAT, TEST_LNG, SEARCH_RADIUS)
    print(f"Found {len(socrata_regs)} regulations from Socrata")
    
    if socrata_regs:
        # Analyze overlap
        analysis = analyze_regulation_overlap(socrata_regs)
        
        print(f"\nAnalysis Results:")
        print(f"  Total regulations: {analysis['total_regulations']}")
        print(f"  Unique CNNs: {analysis['unique_cnns']}")
        print(f"  CNNs with multiple regulations: {analysis['cnns_with_multiple_regs']}")
        print(f"  Unique locations: {analysis['unique_locations']}")
        print(f"  Locations with multiple regulations: {analysis['locations_with_multiple_regs']}")
        
        if analysis['examples']:
            print(f"\nExamples of CNNs with Multiple Regulations:")
            for i, example in enumerate(analysis['examples'], 1):
                print(f"\n  Example {i}:")
                print(f"    CNN: {example['cnn']}")
                print(f"    Number of regulations: {example['num_regulations']}")
                print(f"    Regulation types: {example['regulation_types']}")
                print(f"    Time limits: {example['time_limits']}")
                print(f"    Days: {example['days_of_week']}")
                print(f"    Hours: {example['hours']}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()