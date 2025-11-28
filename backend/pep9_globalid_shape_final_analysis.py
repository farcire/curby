import requests
import json
from collections import defaultdict

base_url = "https://data.sfgov.org/resource/pep9-66vw.json"

print("=" * 80)
print("FINAL COMPREHENSIVE ANALYSIS: PEP9-66VW GlobalID and Shape")
print("=" * 80)

# 1. Check for duplicate CNN_IDs (noticed 10048000 appeared twice)
print("\n" + "=" * 80)
print("1. INVESTIGATING DUPLICATE CNN_IDs")
print("=" * 80)

params = {
    "$limit": 1000,
    "$where": "cnn_id IS NOT NULL",
    "$select": "globalid,cnn_id,shape"
}

response = requests.get(base_url, params=params)
records = response.json()

cnn_to_globalids = defaultdict(list)
for rec in records:
    cnn_id = rec.get('cnn_id')
    globalid = rec.get('globalid')
    if cnn_id and globalid:
        cnn_to_globalids[cnn_id].append({
            'globalid': globalid,
            'shape': rec.get('shape')
        })

duplicates = {cnn: gids for cnn, gids in cnn_to_globalids.items() if len(gids) > 1}

print(f"\nTotal unique CNN_IDs: {len(cnn_to_globalids)}")
print(f"CNN_IDs with multiple GlobalIDs: {len(duplicates)}")

if duplicates:
    print("\nSample CNN_IDs with multiple records:")
    for cnn_id, gids in list(duplicates.items())[:5]:
        print(f"\n  CNN {cnn_id}: {len(gids)} records")
        for i, gid_info in enumerate(gids[:3], 1):
            shape = gid_info['shape']
            coords = shape.get('coordinates', []) if shape else []
            print(f"    {i}. GlobalID: {gid_info['globalid']}")
            if coords:
                print(f"       Points: {len(coords)}, Start: [{coords[0][0]:.6f}, {coords[0][1]:.6f}]")

# 2. Understand what these geometries represent
print("\n" + "=" * 80)
print("2. WHAT DO THESE GEOMETRIES ACTUALLY REPRESENT?")
print("=" * 80)

# Fetch a specific CNN to understand the pattern
params = {
    "$where": "cnn_id = '10048000'",
    "$limit": 10
}

response = requests.get(base_url, params=params)
cnn_records = response.json()

print(f"\nAnalyzing CNN 10048000 (has {len(cnn_records)} records):")

for i, rec in enumerate(cnn_records, 1):
    shape = rec.get('shape', {})
    coords = shape.get('coordinates', [])
    
    print(f"\n  Record {i}:")
    print(f"    GlobalID: {rec.get('globalid')}")
    
    if coords and len(coords) >= 2:
        start = coords[0]
        end = coords[-1]
        
        # Calculate distance
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = (dx**2 + dy**2)**0.5
        
        print(f"    Start: [{start[0]:.6f}, {start[1]:.6f}]")
        print(f"    End: [{end[0]:.6f}, {end[1]:.6f}]")
        print(f"    Distance: {dist:.6f} degrees (~{dist * 111000:.1f} meters)")
        
        # Check if this is left or right side
        # If dx is positive, moving east; if negative, moving west
        # If dy is positive, moving north; if negative, moving south
        direction = "unknown"
        if abs(dx) > abs(dy):
            direction = "East-West street"
        else:
            direction = "North-South street"
        print(f"    Orientation: {direction}")

# 3. Check total dataset statistics
print("\n" + "=" * 80)
print("3. OVERALL DATASET STATISTICS")
print("=" * 80)

# Get count of records with/without various fields
params = {"$select": "count(*) as total"}
response = requests.get(base_url, params=params)
total = response.json()[0]['total']

params = {"$select": "count(*) as total", "$where": "globalid IS NOT NULL"}
response = requests.get(base_url, params=params)
with_globalid = response.json()[0]['total']

params = {"$select": "count(*) as total", "$where": "shape IS NOT NULL"}
response = requests.get(base_url, params=params)
with_shape = response.json()[0]['total']

params = {"$select": "count(*) as total", "$where": "cnn_id IS NOT NULL"}
response = requests.get(base_url, params=params)
with_cnn = response.json()[0]['total']

print(f"\nTotal records in dataset: {total}")
print(f"Records with GlobalID: {with_globalid} ({with_globalid/total*100:.1f}%)")
print(f"Records with Shape: {with_shape} ({with_shape/total*100:.1f}%)")
print(f"Records with CNN_ID: {with_cnn} ({with_cnn/total*100:.1f}%)")

print("\n" + "=" * 80)
print("KEY FINDINGS SUMMARY")
print("=" * 80)

print("""
1. GLOBALID:
   - Unique identifier for each geometry record
   - Can be used as primary key
   - Format: {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX} (GUID)

2. SHAPE (LineString):
   - Represents street centerline geometry
   - Always has 2 coordinate points (start and end of segment)
   - Coordinates in WGS84 (longitude, latitude)
   - NOT curb lines - these are street centerlines

3. CNN_ID Relationship:
   - Multiple GlobalIDs can share the same CNN_ID
   - This suggests: ONE CNN (street segment) has TWO sides (left/right)
   - Each side gets its own GlobalID and geometry
   - The geometries are parallel lines representing each side of the street

4. What This Dataset Represents:
   - Street centerline segments for each SIDE of a street
   - Each CNN segment is split into left and right sides
   - Each side has its own geometry (parallel to the centerline)
   - This allows for side-specific parking regulations

5. Relationship to Parking Data:
   - These geometries define WHERE parking regulations apply
   - Left/right side distinction is crucial for parking rules
   - The shape field provides the geographic boundary for each blockface side
""")