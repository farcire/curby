#!/usr/bin/env python3
"""
Query Socrata API directly for parking regulations at a specific location.
"""

import requests
import json
from typing import List, Dict, Any

# Mission district coordinates
TEST_LAT = 37.7526
TEST_LNG = -122.4107
SEARCH_RADIUS = 50  # meters

def query_socrata_regulations():
    """Query the Socrata API for parking regulations."""
    
    print("=" * 80)
    print("QUERYING SOCRATA PARKING REGULATIONS API")
    print("=" * 80)
    print(f"Location: {TEST_LAT}, {TEST_LNG}")
    print(f"Radius: {SEARCH_RADIUS} meters")
    print()
    
    # Socrata API endpoint
    url = "https://data.sfgov.org/resource/hi6h-neyh.json"
    
    # Try different query approaches
    
    # Approach 1: Simple limit query to see what data looks like
    print("1. Fetching sample regulations...")
    try:
        response = requests.get(url, params={"$limit": 10}, timeout=30)
        response.raise_for_status()
        sample_data = response.json()
        
        print(f"   Retrieved {len(sample_data)} sample records")
        if sample_data:
            print("\n   Sample record structure:")
            first_record = sample_data[0]
            for key in sorted(first_record.keys()):
                value = first_record[key]
                if isinstance(value, dict):
                    print(f"     {key}: {type(value).__name__} with keys: {list(value.keys())[:5]}")
                elif isinstance(value, list):
                    print(f"     {key}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"     {key}: {value}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Approach 2: Query by bounding box
    print("\n2. Querying by bounding box...")
    # Create a small bounding box around the point
    lat_offset = SEARCH_RADIUS / 111000  # rough conversion to degrees
    lng_offset = SEARCH_RADIUS / (111000 * 0.8)  # adjust for latitude
    
    min_lat = TEST_LAT - lat_offset
    max_lat = TEST_LAT + lat_offset
    min_lng = TEST_LNG - lng_offset
    max_lng = TEST_LNG + lng_offset
    
    try:
        # Use SoQL WHERE clause for bounding box
        where_clause = (
            f"latitude > {min_lat} AND latitude < {max_lat} AND "
            f"longitude > {min_lng} AND longitude < {max_lng}"
        )
        
        response = requests.get(
            url,
            params={
                "$where": where_clause,
                "$limit": 1000
            },
            timeout=30
        )
        response.raise_for_status()
        bbox_data = response.json()
        
        print(f"   Found {len(bbox_data)} regulations in bounding box")
        
        if bbox_data:
            # Group by CNN
            by_cnn = {}
            for reg in bbox_data:
                cnn = reg.get('cnnid')
                if cnn:
                    if cnn not in by_cnn:
                        by_cnn[cnn] = []
                    by_cnn[cnn].append(reg)
            
            print(f"   Unique CNNs: {len(by_cnn)}")
            
            # Find CNNs with multiple regulations
            multi_reg_cnns = {cnn: regs for cnn, regs in by_cnn.items() if len(regs) > 1}
            print(f"   CNNs with multiple regulations: {len(multi_reg_cnns)}")
            
            if multi_reg_cnns:
                print("\n   Examples of CNNs with multiple regulations:")
                for i, (cnn, regs) in enumerate(list(multi_reg_cnns.items())[:3], 1):
                    print(f"\n   Example {i}: CNN {cnn} ({len(regs)} regulations)")
                    for j, reg in enumerate(regs, 1):
                        print(f"     Regulation {j}:")
                        print(f"       Type: {reg.get('regulationtype', 'N/A')}")
                        print(f"       Time Limit: {reg.get('timelimit', 'N/A')}")
                        print(f"       Days: {reg.get('daysofweek', 'N/A')}")
                        print(f"       Hours: {reg.get('starttime', 'N/A')} - {reg.get('endtime', 'N/A')}")
                        print(f"       Street: {reg.get('streetname', 'N/A')}")
                        
                        # Check geometry
                        if 'the_geom' in reg:
                            geom = reg['the_geom']
                            if isinstance(geom, dict) and 'coordinates' in geom:
                                coords = geom['coordinates']
                                print(f"       Geometry: {geom.get('type', 'Unknown')} with {len(coords) if isinstance(coords, list) else 0} points")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Approach 3: Query specific CNN if we know one
    print("\n3. Querying specific CNN (1046000 - Balmy Street)...")
    try:
        response = requests.get(
            url,
            params={
                "cnnid": "1046000",
                "$limit": 100
            },
            timeout=30
        )
        response.raise_for_status()
        cnn_data = response.json()
        
        print(f"   Found {len(cnn_data)} regulations for CNN 1046000")
        
        if cnn_data:
            print("\n   Regulations for Balmy Street (CNN 1046000):")
            for i, reg in enumerate(cnn_data, 1):
                print(f"\n   Regulation {i}:")
                print(f"     Type: {reg.get('regulationtype', 'N/A')}")
                print(f"     Time Limit: {reg.get('timelimit', 'N/A')}")
                print(f"     Days: {reg.get('daysofweek', 'N/A')}")
                print(f"     Hours: {reg.get('starttime', 'N/A')} - {reg.get('endtime', 'N/A')}")
                print(f"     Street: {reg.get('streetname', 'N/A')}")
                print(f"     Side: {reg.get('streetside', 'N/A')}")
                
                # Check for geometry overlap
                if 'the_geom' in reg:
                    geom = reg['the_geom']
                    if isinstance(geom, dict):
                        print(f"     Geometry Type: {geom.get('type', 'Unknown')}")
                        if 'coordinates' in geom:
                            coords = geom['coordinates']
                            if isinstance(coords, list) and len(coords) > 0:
                                if isinstance(coords[0], list):
                                    print(f"     Coordinates: {len(coords)} line segments")
                                    # Show first and last point
                                    if len(coords) > 0:
                                        first = coords[0]
                                        last = coords[-1]
                                        print(f"     Start: {first}")
                                        print(f"     End: {last}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("QUERY COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    query_socrata_regulations()