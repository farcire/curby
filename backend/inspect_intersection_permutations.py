#!/usr/bin/env python3
"""
Investigate the Intersection Permutations dataset
API: https://data.sfgov.org/api/v3/views/jfxm-zeee/query.json

This dataset provides ALL permutations of street intersections,
allowing us to handle user input regardless of order:
- "20th & Bryant"
- "Bryant & 20th"
- "20th and Bryant"
- etc.
"""

import requests
import json

# API endpoint
BASE_URL = "https://data.sfgov.org/resource/jfxm-zeee.json"

print("="*80)
print("INTERSECTION PERMUTATIONS DATASET INVESTIGATION")
print("="*80)

# 1. Fetch sample records
print("\n1. Fetching sample records...")
try:
    response = requests.get(BASE_URL, params={"$limit": 5})
    response.raise_for_status()
    samples = response.json()
    
    print(f"   ✓ Retrieved {len(samples)} sample records\n")
    
    if samples:
        print("   Available fields:")
        for key in sorted(samples[0].keys()):
            print(f"     - {key}")
        
        print(f"\n   Sample records:")
        for i, sample in enumerate(samples, 1):
            print(f"\n   Record {i}:")
            for key, value in sorted(sample.items()):
                if isinstance(value, dict):
                    print(f"     {key}: {json.dumps(value)}")
                else:
                    print(f"     {key}: {value}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 2. Search for "20th & Bryant" permutations
print(f"\n{'='*80}")
print("2. Searching for '20TH ST & BRYANT ST' permutations")
print(f"{'='*80}")

try:
    # Try searching for records containing both street names
    params = {
        "$where": "streets LIKE '%20TH%' AND streets LIKE '%BRYANT%'",
        "$limit": 10
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    results = response.json()
    
    print(f"   ✓ Found {len(results)} permutations")
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"\n   Permutation {i}:")
            for key, value in sorted(result.items()):
                print(f"     {key}: {value}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 3. Get dataset statistics
print(f"\n{'='*80}")
print("3. Dataset Statistics")
print(f"{'='*80}")

try:
    # Get total count
    params = {"$select": "COUNT(*) as total"}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    result = response.json()
    
    if result:
        print(f"   ✓ Total permutation records: {result[0].get('total', 'N/A')}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")

print(f"\n{'='*80}")
print("INVESTIGATION COMPLETE")
print(f"{'='*80}\n")

print("\nKEY INSIGHTS:")
print("- This dataset provides ALL permutations of street intersections")
print("- Allows matching user input regardless of street order")
print("- Critical for robust intersection search functionality")
print("- Should be used in conjunction with the main intersections dataset")