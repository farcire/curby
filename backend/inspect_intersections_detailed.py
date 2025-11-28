#!/usr/bin/env python3
"""
Detailed investigation of the Street Intersections dataset
Dataset: https://data.sfgov.org/resource/pu5n-qu5c.json

Based on initial investigation, the actual fields are:
- cnn: CNN segment identifier
- streetname: The street name
- from_st: The intersecting street name
- limits: Description of the intersection
- theorder: Ordering field
"""

import requests
import json
from typing import Dict, List, Any
from collections import defaultdict

BASE_URL = "https://data.sfgov.org/resource/pu5n-qu5c.json"

def fetch_intersections_for_cnn(cnn: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch all intersections for a given CNN"""
    params = {
        "cnn": cnn,
        "$limit": limit
    }
    
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def fetch_intersections_by_streets(street1: str, street2: str) -> List[Dict[str, Any]]:
    """Fetch intersections involving two street names"""
    # Search where one is streetname and other is from_st, or vice versa
    params = {
        "$where": f"(streetname='{street1}' AND from_st='{street2}') OR (streetname='{street2}' AND from_st='{street1}')",
        "$limit": 50
    }
    
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def analyze_cnn_intersections(cnn: str) -> None:
    """Analyze all intersections for a specific CNN"""
    print(f"\n{'='*80}")
    print(f"ANALYZING INTERSECTIONS FOR CNN: {cnn}")
    print(f"{'='*80}\n")
    
    try:
        intersections = fetch_intersections_for_cnn(cnn)
        print(f"Found {len(intersections)} intersection records for CNN {cnn}\n")
        
        if not intersections:
            print("No intersections found")
            return
        
        # Group by from_st to see all connecting streets
        by_from_st = defaultdict(list)
        for intersection in intersections:
            from_st = intersection.get('from_st', 'Unknown')
            by_from_st[from_st].append(intersection)
        
        print(f"This CNN connects to {len(by_from_st)} different streets:\n")
        
        for from_st, records in sorted(by_from_st.items()):
            print(f"  Intersection with: {from_st}")
            for record in records:
                print(f"    - streetname: {record.get('streetname', 'N/A')}")
                print(f"      limits: {record.get('limits', 'N/A')}")
                print(f"      theorder: {record.get('theorder', 'N/A')}")
                print()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def search_intersection_by_name(street1: str, street2: str) -> None:
    """Search for a specific intersection by street names"""
    print(f"\n{'='*80}")
    print(f"SEARCHING FOR INTERSECTION: {street1} & {street2}")
    print(f"{'='*80}\n")
    
    try:
        results = fetch_intersections_by_streets(street1, street2)
        print(f"Found {len(results)} matching records\n")
        
        if results:
            # Group by CNN to see which CNNs are involved
            by_cnn = defaultdict(list)
            for result in results:
                cnn = result.get('cnn', 'Unknown')
                by_cnn[cnn].append(result)
            
            print(f"This intersection involves {len(by_cnn)} CNN segments:\n")
            
            for cnn, records in sorted(by_cnn.items()):
                print(f"CNN: {cnn}")
                for record in records:
                    print(f"  streetname: {record.get('streetname', 'N/A')}")
                    print(f"  from_st: {record.get('from_st', 'N/A')}")
                    print(f"  limits: {record.get('limits', 'N/A')}")
                print()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("="*80)
    print("DETAILED STREET INTERSECTIONS INVESTIGATION")
    print("="*80)
    
    # Test with known CNN from our system
    analyze_cnn_intersections("10048000")  # 20th St segment
    
    # Test with street name search
    search_intersection_by_name("20TH ST", "BRYANT ST")
    search_intersection_by_name("20TH ST", "FLORIDA ST")
    
    # Additional analysis: understand the data model
    print(f"\n{'='*80}")
    print("DATA MODEL ANALYSIS")
    print(f"{'='*80}\n")
    
    print("Based on the investigation, the intersection dataset structure is:")
    print()
    print("Each record represents ONE DIRECTION of an intersection:")
    print("  - cnn: The CNN of the main street segment")
    print("  - streetname: The name of the main street")
    print("  - from_st: The name of the intersecting/cross street")
    print("  - limits: Description (e.g., 'BRYANT ST intersection')")
    print("  - theorder: Some ordering/sequencing field")
    print()
    print("Key insights:")
    print("  1. Each intersection appears multiple times (once per direction)")
    print("  2. To find all streets at an intersection, query by CNN")
    print("  3. To find a specific intersection, query by both street names")
    print("  4. The 'limits' field describes the intersection boundary")
    print()
    print("For user queries like '20th & Bryant':")
    print("  1. Search for records where streetname='20TH ST' AND from_st='BRYANT ST'")
    print("  2. Or vice versa: streetname='BRYANT ST' AND from_st='20TH ST'")
    print("  3. Extract the CNN(s) involved")
    print("  4. Use those CNNs to query our street_segments collection")
    print()

if __name__ == "__main__":
    main()