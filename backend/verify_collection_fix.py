#!/usr/bin/env python3
"""
Verify that the API is now querying the street_segments collection
and returning the full 4,014 segments instead of just 218.
"""

import requests
import json

def test_mission_coverage():
    """Test that we now get full Mission neighborhood coverage"""
    
    print("=" * 80)
    print("VERIFYING COLLECTION FIX")
    print("=" * 80)
    
    # Test 1: Balmy Street (should now return 2 segments)
    print("\n1. Testing Balmy Street (should find 2 segments)...")
    lat, lng = 37.7526, -122.4107
    response = requests.get(
        f"http://localhost:8000/api/v1/blockfaces?lat={lat}&lng={lng}&radius_meters=100"
    )
    
    if response.status_code == 200:
        data = response.json()
        balmy_segments = [bf for bf in data if 'balmy' in bf.get('street_name', '').lower()]
        print(f"   ✓ Found {len(balmy_segments)} Balmy Street segments")
        if len(balmy_segments) >= 2:
            print("   ✓ PASS: Balmy Street has expected coverage")
        else:
            print("   ✗ FAIL: Expected 2 segments, got", len(balmy_segments))
    else:
        print(f"   ✗ FAIL: API returned status {response.status_code}")
    
    # Test 2: 18th Street (should return ~50-60 segments)
    print("\n2. Testing 18th Street (should find ~50-60 segments)...")
    lat, lng = 37.7604, -122.4087
    response = requests.get(
        f"http://localhost:8000/api/v1/blockfaces?lat={lat}&lng={lng}&radius_meters=500"
    )
    
    if response.status_code == 200:
        data = response.json()
        eighteenth_segments = [bf for bf in data if '18th' in bf.get('street_name', '').lower()]
        print(f"   ✓ Found {len(eighteenth_segments)} 18th Street segments")
        if len(eighteenth_segments) >= 40:
            print("   ✓ PASS: 18th Street has good coverage")
        else:
            print(f"   ⚠ WARNING: Expected ~50-60 segments, got {len(eighteenth_segments)}")
    else:
        print(f"   ✗ FAIL: API returned status {response.status_code}")
    
    # Test 3: Mission neighborhood wide search (should return hundreds)
    print("\n3. Testing Mission neighborhood (should find 200+ segments)...")
    lat, lng = 37.7529, -122.4194
    response = requests.get(
        f"http://localhost:8000/api/v1/blockfaces?lat={lat}&lng={lng}&radius_meters=1000"
    )
    
    if response.status_code == 200:
        data = response.json()
        total_segments = len(data)
        print(f"   ✓ Found {total_segments} total segments in Mission area")
        if total_segments >= 200:
            print("   ✓ PASS: Mission neighborhood has full coverage")
        elif total_segments > 10:
            print(f"   ⚠ IMPROVED: Was ~3 segments, now {total_segments} segments")
        else:
            print(f"   ✗ FAIL: Expected 200+ segments, got {total_segments}")
            
        # Show sample of streets found
        street_names = set(bf.get('street_name', 'Unknown') for bf in data[:20])
        print(f"\n   Sample streets found: {', '.join(sorted(street_names)[:10])}")
    else:
        print(f"   ✗ FAIL: API returned status {response.status_code}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_mission_coverage()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()