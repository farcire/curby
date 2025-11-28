#!/usr/bin/env python3
"""
Simple synchronous test of RPP data
"""
import sys
import os

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

print("="*70, flush=True)
print("SIMPLE RPP TEST", flush=True)
print("="*70, flush=True)

# Test 1: Check environment
print("\n1. Checking environment...", flush=True)
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

mongodb_uri = os.getenv('MONGODB_URI')
app_token = os.getenv('SFMTA_APP_TOKEN')

print(f"   MongoDB URI: {'✅ Set' if mongodb_uri else '❌ Not set'}", flush=True)
print(f"   SFMTA Token: {'✅ Set' if app_token else '❌ Not set'}", flush=True)

# Test 2: Fetch RPP Parcels from API
print("\n2. Fetching RPP Parcels from Socrata API...", flush=True)

try:
    from sodapy import Socrata
    
    client = Socrata("data.sfgov.org", app_token)
    
    # Fetch a small sample
    print("   Requesting 10 parcels...", flush=True)
    parcels = client.get("i886-hxz9", limit=10)
    
    print(f"   ✅ Fetched {len(parcels)} parcels", flush=True)
    
    if len(parcels) > 0:
        print("\n   Sample parcel:", flush=True)
        sample = parcels[0]
        print(f"     Parcel ID: {sample.get('mapblklot')}", flush=True)
        print(f"     RPP Area: {sample.get('rppeligib')}", flush=True)
        print(f"     Has geometry: {'Yes' if 'shape' in sample else 'No'}", flush=True)
        
        # Count by RPP area
        from collections import Counter
        areas = Counter(p.get('rppeligib') for p in parcels if p.get('rppeligib'))
        print(f"\n   RPP areas in sample: {dict(areas)}", flush=True)
    
    client.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}", flush=True)
    import traceback
    traceback.print_exc()

# Test 3: Check MongoDB for Mission RPP data
print("\n3. Checking MongoDB for Mission RPP regulations...", flush=True)

try:
    from pymongo import MongoClient
    
    client = MongoClient(mongodb_uri)
    db = client.curby
    
    # Count regulations with RPP areas
    count = db.parking_regulations.count_documents({
        "analysis_neighborhood": "Mission",
        "$or": [
            {"rpparea1": {"$exists": True, "$ne": None}},
            {"rpparea2": {"$exists": True, "$ne": None}}
        ]
    })
    
    print(f"   ✅ Found {count} regulations with RPP areas in Mission", flush=True)
    
    # Get unique RPP areas
    pipeline = [
        {"$match": {"analysis_neighborhood": "Mission"}},
        {"$group": {"_id": "$rpparea1", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    
    results = list(db.parking_regulations.aggregate(pipeline))
    areas = [r['_id'] for r in results if r['_id']]
    
    print(f"   RPP areas found: {', '.join(sorted(areas))}", flush=True)
    
    client.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("\n" + "="*70, flush=True)
print("TEST COMPLETE", flush=True)
print("="*70, flush=True)