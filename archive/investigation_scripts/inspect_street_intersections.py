#!/usr/bin/env python3
"""
Inspect the Street Intersections dataset from SF Open Data
Dataset: https://data.sfgov.org/api/v3/views/pu5n-qu5c
API Docs: https://dev.socrata.com/foundry/data.sfgov.org/pu5n-qu5c

KEY FIELDS IN THIS DATASET:
- cnn: The CNN segment identifier
- cnnfrom: The "from" CNN (connecting segment)
- cnnto: The "to" CNN (connecting segment)
- street_name: The intersection street name
- lf_st_num: Left side street number at intersection
- rt_st_num: Right side street number at intersection

This dataset helps us:
1. Handle user queries with street intersections instead of addresses
2. Understand CNN segment connectivity (which CNNs connect at intersections)
3. Get precise address numbers at intersection boundaries
4. Better understand blockface geometry relationships
"""

import requests
import json
from typing import Dict, List, Any

# Socrata API endpoint
BASE_URL = "https://data.sfgov.org/resource/pu5n-qu5c.json"

def fetch_sample_intersections(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch a sample of intersection records"""
    params = {
        "$limit": limit,
        "$order": "cnn DESC"
    }
    
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def fetch_intersections_by_cnn(cnn: str) -> List[Dict[str, Any]]:
    """Fetch all intersections for a given CNN (both as main CNN and as connecting CNN)"""
    params = {
        "$where": f"cnn='{cnn}' OR cnnfrom='{cnn}' OR cnnto='{cnn}'",
        "$limit": 100
    }
    
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def fetch_intersection_by_streets(street1: str, street2: str) -> List[Dict[str, Any]]:
    """Fetch intersection by two street names"""
    # The dataset might store intersections in various formats
    # Try searching for both street names in the street_name field
    params = {
        "$where": f"street_name LIKE '%{street1}%' AND street_name LIKE '%{street2}%'",
        "$limit": 10
    }
    
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def analyze_intersection_structure(intersections: List[Dict[str, Any]]) -> None:
    """Analyze and print the structure of intersection records"""
    if not intersections:
        print("No intersections found")
        return
    
    print(f"\n{'='*80}")
    print(f"INTERSECTION DATASET STRUCTURE")
    print(f"{'='*80}\n")
    
    # Get all unique fields across all records
    all_fields = set()
    for intersection in intersections:
        all_fields.update(intersection.keys())
    
    print(f"Total unique fields: {len(all_fields)}\n")
    print("Fields found:")
    for field in sorted(all_fields):
        # Get sample value
        sample_val = None
        for intersection in intersections:
            if field in intersection:
                sample_val = intersection[field]
                break
        
        val_type = type(sample_val).__name__ if sample_val is not None else "None"
        print(f"  - {field:30s} ({val_type})")
    
    print(f"\n{'='*80}")
    print(f"SAMPLE INTERSECTION RECORDS")
    print(f"{'='*80}\n")
    
    for i, intersection in enumerate(intersections[:5], 1):
        print(f"\nIntersection {i}:")
        print(f"{'-'*80}")
        
        # Key CNN fields
        print(f"CNN (main):        {intersection.get('cnn', 'N/A')}")
        print(f"CNN From:          {intersection.get('cnnfrom', 'N/A')}")
        print(f"CNN To:            {intersection.get('cnnto', 'N/A')}")
        
        # Street information
        print(f"Street Name:       {intersection.get('street_name', 'N/A')}")
        
        # Address numbers at intersection
        print(f"Left Side Number:  {intersection.get('lf_st_num', 'N/A')}")
        print(f"Right Side Number: {intersection.get('rt_st_num', 'N/A')}")
        
        # Geometry
        if 'the_geom' in intersection:
            geom = intersection['the_geom']
            print(f"Geometry Type:     {geom.get('type', 'N/A')}")
            if 'coordinates' in geom:
                coords = geom['coordinates']
                print(f"Coordinates:       [{coords[0]:.6f}, {coords[1]:.6f}]")
        
        # Show all other fields
        print(f"\nOther fields:")
        for key, value in sorted(intersection.items()):
            if key not in ['cnn', 'cnnfrom', 'cnnto', 'street_name', 'lf_st_num', 'rt_st_num', 'the_geom']:
                print(f"  {key}: {value}")

def main():
    print("="*80)
    print("STREET INTERSECTIONS DATASET INVESTIGATION")
    print("="*80)
    
    # 1. Fetch and analyze sample intersections
    print("\n1. Fetching sample intersections...")
    try:
        sample = fetch_sample_intersections(20)
        print(f"   ✓ Fetched {len(sample)} sample records")
        analyze_intersection_structure(sample)
    except Exception as e:
        print(f"   ✗ Error fetching sample: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Search for intersections by CNN (using a known CNN from our system)
    print(f"\n{'='*80}")
    print("2. Searching intersections for CNN: 10048000 (20th St segment)")
    print(f"{'='*80}")
    try:
        results = fetch_intersections_by_cnn("10048000")
        print(f"   ✓ Found {len(results)} intersections involving this CNN")
        
        if results:
            for i, intersection in enumerate(results, 1):
                print(f"\n   Intersection {i}:")
                print(f"   CNN:           {intersection.get('cnn', 'N/A')}")
                print(f"   CNN From:      {intersection.get('cnnfrom', 'N/A')}")
                print(f"   CNN To:        {intersection.get('cnnto', 'N/A')}")
                print(f"   Street:        {intersection.get('street_name', 'N/A')}")
                print(f"   Left #:        {intersection.get('lf_st_num', 'N/A')}")
                print(f"   Right #:       {intersection.get('rt_st_num', 'N/A')}")
                
                if 'the_geom' in intersection:
                    coords = intersection['the_geom'].get('coordinates', [])
                    if coords:
                        print(f"   Location:      [{coords[0]:.6f}, {coords[1]:.6f}]")
        else:
            print("   No intersections found for this CNN")
    except Exception as e:
        print(f"   ✗ Error searching by CNN: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Search for a specific intersection by street names
    print(f"\n{'='*80}")
    print("3. Searching for intersection: 20TH ST & BRYANT ST")
    print(f"{'='*80}")
    try:
        results = fetch_intersection_by_streets("20TH", "BRYANT")
        print(f"   ✓ Found {len(results)} matching intersections")
        
        if results:
            for i, intersection in enumerate(results, 1):
                print(f"\n   Match {i}:")
                print(f"   CNN:           {intersection.get('cnn', 'N/A')}")
                print(f"   CNN From:      {intersection.get('cnnfrom', 'N/A')}")
                print(f"   CNN To:        {intersection.get('cnnto', 'N/A')}")
                print(f"   Street:        {intersection.get('street_name', 'N/A')}")
                print(f"   Left #:        {intersection.get('lf_st_num', 'N/A')}")
                print(f"   Right #:       {intersection.get('rt_st_num', 'N/A')}")
                
                if 'the_geom' in intersection:
                    coords = intersection['the_geom'].get('coordinates', [])
                    if coords:
                        print(f"   Location:      [{coords[0]:.6f}, {coords[1]:.6f}]")
    except Exception as e:
        print(f"   ✗ Error searching intersection: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Analyze dataset statistics
    print(f"\n{'='*80}")
    print("4. Analyzing dataset statistics")
    print(f"{'='*80}")
    try:
        # Get total count
        params = {"$select": "COUNT(*) as total"}
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        result = response.json()
        
        if result:
            print(f"   ✓ Total intersection records: {result[0].get('total', 'N/A')}")
        
        # Get unique CNNs
        params = {"$select": "COUNT(DISTINCT cnn) as unique_cnns"}
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        result = response.json()
        
        if result:
            print(f"   ✓ Unique CNNs: {result[0].get('unique_cnns', 'N/A')}")
            
    except Exception as e:
        print(f"   ✗ Error analyzing statistics: {e}")
    
    print(f"\n{'='*80}")
    print("INVESTIGATION COMPLETE")
    print(f"{'='*80}\n")
    
    print("\nKEY FINDINGS:")
    print("- This dataset provides CNN connectivity information (cnnfrom, cnnto)")
    print("- It includes precise address numbers at intersections (lf_st_num, rt_st_num)")
    print("- It has geospatial coordinates for each intersection point")
    print("- This can help resolve user queries like '20th & Bryant' to specific CNNs")
    print("- The address numbers help us understand blockface boundaries more precisely")

if __name__ == "__main__":
    main()