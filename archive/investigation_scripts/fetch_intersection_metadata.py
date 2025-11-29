#!/usr/bin/env python3
"""
Fetch metadata and sample data from the Street Intersections dataset
to understand the actual schema
"""

import requests
import json

# Get metadata about the dataset
METADATA_URL = "https://data.sfgov.org/api/views/pu5n-qu5c.json"
DATA_URL = "https://data.sfgov.org/resource/pu5n-qu5c.json"

print("="*80)
print("FETCHING INTERSECTION DATASET METADATA")
print("="*80)

try:
    # Get metadata
    print("\n1. Fetching dataset metadata...")
    response = requests.get(METADATA_URL)
    response.raise_for_status()
    metadata = response.json()
    
    print(f"   Dataset Name: {metadata.get('name', 'N/A')}")
    print(f"   Description: {metadata.get('description', 'N/A')[:200]}...")
    print(f"   Rows: {metadata.get('rowsUpdatedAt', 'N/A')}")
    
    # Get column information
    if 'columns' in metadata:
        print(f"\n2. Column Definitions ({len(metadata['columns'])} columns):")
        print(f"   {'Field Name':<30} {'Data Type':<15} {'Description'}")
        print(f"   {'-'*30} {'-'*15} {'-'*50}")
        
        for col in metadata['columns']:
            field_name = col.get('fieldName', col.get('name', 'N/A'))
            data_type = col.get('dataTypeName', 'N/A')
            description = col.get('description', '')[:50]
            print(f"   {field_name:<30} {data_type:<15} {description}")
    
    # Fetch sample data
    print(f"\n3. Fetching sample data...")
    params = {"$limit": 5}
    response = requests.get(DATA_URL, params=params)
    response.raise_for_status()
    samples = response.json()
    
    print(f"   Retrieved {len(samples)} sample records\n")
    
    for i, sample in enumerate(samples, 1):
        print(f"   Sample {i}:")
        for key, value in sorted(sample.items()):
            if isinstance(value, dict):
                print(f"     {key}: {json.dumps(value, indent=8)}")
            else:
                print(f"     {key}: {value}")
        print()
    
    # Try to find a specific intersection
    print(f"\n4. Searching for '20TH ST' intersections...")
    params = {
        "$where": "streetname LIKE '%20TH%'",
        "$limit": 10
    }
    response = requests.get(DATA_URL, params=params)
    response.raise_for_status()
    results = response.json()
    
    print(f"   Found {len(results)} records")
    if results:
        print(f"\n   First few results:")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. CNN: {result.get('cnn', 'N/A')}, "
                  f"Street: {result.get('streetname', 'N/A')}, "
                  f"From: {result.get('from_st', 'N/A')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("METADATA FETCH COMPLETE")
print(f"{'='*80}\n")