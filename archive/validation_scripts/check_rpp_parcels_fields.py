#!/usr/bin/env python3
"""
Check if RPP Parcels dataset has street/address fields
"""
from sodapy import Socrata
import os
import json

# Load env manually
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

app_token = os.getenv("SFMTA_APP_TOKEN")

print("=== Fetching RPP Parcels Dataset ===\n")

try:
    client = Socrata("data.sfgov.org", app_token)
    
    # Fetch sample records
    results = client.get("i886-hxz9", limit=5)
    
    if len(results) > 0:
        print("Available fields in RPP Parcels dataset:")
        all_fields = list(results[0].keys())
        for field in sorted(all_fields):
            print(f"  - {field}")
        
        print("\n" + "="*70)
        print("\nSample records with key fields:\n")
        
        for i, record in enumerate(results[:3], 1):
            print(f"--- Record {i} ---")
            print(f"Parcel ID (mapblklot): {record.get('mapblklot', 'N/A')}")
            print(f"RPP Area (rppeligib): {record.get('rppeligib', 'N/A')}")
            
            # Check for street/address fields
            if 'street' in record:
                print(f"Street: {record.get('street')}")
            if 'from_st' in record:
                print(f"From Street #: {record.get('from_st')}")
            if 'to_st' in record:
                print(f"To Street #: {record.get('to_st')}")
            if 'odd_even' in record:
                print(f"Odd/Even: {record.get('odd_even')}")
            
            print()
        
        # Summary
        print("="*70)
        print("\n📊 FIELD AVAILABILITY:")
        print(f"  ✓ mapblklot (Parcel ID): YES")
        print(f"  ✓ rppeligib (RPP Area): YES")
        print(f"  ✓ shape (Geometry): YES")
        print(f"  ? street: {'YES' if 'street' in results[0] else 'NO'}")
        print(f"  ? from_st: {'YES' if 'from_st' in results[0] else 'NO'}")
        print(f"  ? to_st: {'YES' if 'to_st' in results[0] else 'NO'}")
        print(f"  ? odd_even: {'YES' if 'odd_even' in results[0] else 'NO'}")
        
        print("\n" + "="*70)
        print("\n🔍 CONCLUSION:")
        
        if 'street' not in results[0]:
            print("❌ This dataset does NOT contain street/address fields")
            print("   It only has parcel-level data (building footprints)")
            print("\n💡 RECOMMENDATION:")
            print("   Use SPATIAL JOIN between:")
            print("   - RPP Parcel geometries (building footprints)")
            print("   - Active Streets centerline geometries")
            print("   - Determine L/R side using geometric calculation")
            print("   - Match RPP area to street segments")
        else:
            print("✅ This dataset DOES contain street/address information!")
            print("   Can be used to match RPP areas to street segments")
    
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()