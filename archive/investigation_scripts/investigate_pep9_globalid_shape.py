import requests
import json
from collections import defaultdict

# Fetch sample records from pep9-66vw dataset
base_url = "https://data.sfgov.org/resource/pep9-66vw.json"

print("=" * 80)
print("PEP9-66VW Dataset: GlobalID and Shape Analysis")
print("=" * 80)

# Fetch records with both globalid and shape fields
params = {
    "$limit": 100,
    "$where": "globalid IS NOT NULL AND shape IS NOT NULL"
}

try:
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    records = response.json()
    
    print(f"\nFetched {len(records)} records with both globalid and shape\n")
    
    # Collect GlobalIDs to check uniqueness
    globalids = []
    globalid_counts = defaultdict(int)
    
    # Analyze shape geometries
    shape_types = defaultdict(int)
    coordinate_samples = []
    
    # Track records with/without cnn_id
    with_cnn = []
    without_cnn = []
    
    for record in records:
        globalid = record.get('globalid')
        shape = record.get('shape')
        cnn_id = record.get('cnn_id')
        
        if globalid:
            globalids.append(globalid)
            globalid_counts[globalid] += 1
        
        if shape:
            shape_types[shape.get('type')] += 1
            
            # Store sample coordinates
            if len(coordinate_samples) < 5:
                coordinate_samples.append({
                    'globalid': globalid,
                    'cnn_id': cnn_id,
                    'shape': shape,
                    'street_name': record.get('street_name'),
                    'from_st': record.get('from_st'),
                    'to_st': record.get('to_st')
                })
        
        # Categorize by cnn_id presence
        if cnn_id:
            with_cnn.append(record)
        else:
            without_cnn.append(record)
    
    # Analysis Results
    print("\n" + "=" * 80)
    print("1. GLOBALID UNIQUENESS ANALYSIS")
    print("=" * 80)
    print(f"Total GlobalIDs collected: {len(globalids)}")
    print(f"Unique GlobalIDs: {len(set(globalids))}")
    
    duplicates = {gid: count for gid, count in globalid_counts.items() if count > 1}
    if duplicates:
        print(f"\nDuplicate GlobalIDs found: {len(duplicates)}")
        for gid, count in list(duplicates.items())[:5]:
            print(f"  {gid}: appears {count} times")
    else:
        print("\n✓ All GlobalIDs are unique - can be used as primary key")
    
    print("\n" + "=" * 80)
    print("2. SHAPE GEOMETRY ANALYSIS")
    print("=" * 80)
    print("Shape types found:")
    for shape_type, count in shape_types.items():
        print(f"  {shape_type}: {count} records")
    
    print("\n" + "=" * 80)
    print("3. SAMPLE SHAPE GEOMETRIES")
    print("=" * 80)
    
    for i, sample in enumerate(coordinate_samples, 1):
        print(f"\nSample {i}:")
        print(f"  GlobalID: {sample['globalid']}")
        print(f"  CNN_ID: {sample['cnn_id']}")
        print(f"  Street: {sample['street_name']}")
        print(f"  From: {sample['from_st']} To: {sample['to_st']}")
        
        shape = sample['shape']
        print(f"  Shape Type: {shape.get('type')}")
        
        if shape.get('type') == 'LineString':
            coords = shape.get('coordinates', [])
            print(f"  Number of coordinate points: {len(coords)}")
            if coords:
                print(f"  First point: {coords[0]}")
                print(f"  Last point: {coords[-1]}")
                
                # Calculate approximate length
                if len(coords) >= 2:
                    # Simple distance calculation (not accurate for lat/lng but gives idea)
                    total_dist = 0
                    for j in range(len(coords) - 1):
                        dx = coords[j+1][0] - coords[j][0]
                        dy = coords[j+1][1] - coords[j][1]
                        total_dist += (dx**2 + dy**2)**0.5
                    print(f"  Approximate length (coordinate units): {total_dist:.6f}")
    
    print("\n" + "=" * 80)
    print("4. CNN_ID RELATIONSHIP ANALYSIS")
    print("=" * 80)
    print(f"Records WITH cnn_id: {len(with_cnn)}")
    print(f"Records WITHOUT cnn_id: {len(without_cnn)}")
    
    # Compare shape quality
    if with_cnn:
        print("\nSample records WITH cnn_id:")
        for i, rec in enumerate(with_cnn[:3], 1):
            shape = rec.get('shape', {})
            coords = shape.get('coordinates', [])
            print(f"\n  {i}. CNN: {rec.get('cnn_id')}, Street: {rec.get('street_name')}")
            print(f"     Shape points: {len(coords)}, Type: {shape.get('type')}")
    
    if without_cnn:
        print("\nSample records WITHOUT cnn_id:")
        for i, rec in enumerate(without_cnn[:3], 1):
            shape = rec.get('shape', {})
            coords = shape.get('coordinates', [])
            print(f"\n  {i}. Street: {rec.get('street_name')}")
            print(f"     Shape points: {len(coords)}, Type: {shape.get('type')}")
    
    print("\n" + "=" * 80)
    print("5. WHAT DO THESE GEOMETRIES REPRESENT?")
    print("=" * 80)
    
    # Analyze a few specific examples in detail
    print("\nDetailed examination of specific blockfaces:")
    
    for i, rec in enumerate(records[:5], 1):
        print(f"\n{'='*60}")
        print(f"Example {i}:")
        print(f"{'='*60}")
        print(f"GlobalID: {rec.get('globalid')}")
        print(f"CNN_ID: {rec.get('cnn_id')}")
        print(f"Street: {rec.get('street_name')}")
        print(f"From: {rec.get('from_st')} To: {rec.get('to_st')}")
        print(f"Side: {rec.get('lf_fadd')} to {rec.get('lf_toadd')} (left), {rec.get('rt_fadd')} to {rec.get('rt_toadd')} (right)")
        
        shape = rec.get('shape', {})
        coords = shape.get('coordinates', [])
        
        print(f"\nGeometry Details:")
        print(f"  Type: {shape.get('type')}")
        print(f"  Number of points: {len(coords)}")
        
        if coords and len(coords) >= 2:
            print(f"  Start: [{coords[0][0]:.6f}, {coords[0][1]:.6f}]")
            print(f"  End: [{coords[-1][0]:.6f}, {coords[-1][1]:.6f}]")
            
            # Show a few intermediate points if available
            if len(coords) > 2:
                print(f"  Intermediate points: {len(coords) - 2}")
                if len(coords) > 4:
                    mid = len(coords) // 2
                    print(f"  Mid-point: [{coords[mid][0]:.6f}, {coords[mid][1]:.6f}]")
        
        # Check for other relevant fields
        print(f"\nAdditional Fields:")
        print(f"  Jurisdiction: {rec.get('jurisdiction')}")
        print(f"  Street Type: {rec.get('st_type')}")
        print(f"  Layer: {rec.get('layer')}")
        print(f"  Class Code: {rec.get('classcode')}")
    
    print("\n" + "=" * 80)
    print("6. COORDINATE SYSTEM ANALYSIS")
    print("=" * 80)
    
    # Check coordinate ranges to determine coordinate system
    all_lngs = []
    all_lats = []
    
    for rec in records:
        shape = rec.get('shape', {})
        coords = shape.get('coordinates', [])
        for coord in coords:
            if len(coord) >= 2:
                all_lngs.append(coord[0])
                all_lats.append(coord[1])
    
    if all_lngs and all_lats:
        print(f"Longitude range: {min(all_lngs):.6f} to {max(all_lngs):.6f}")
        print(f"Latitude range: {min(all_lats):.6f} to {max(all_lats):.6f}")
        
        # SF is approximately -122.5 to -122.35 longitude, 37.7 to 37.8 latitude
        if -123 < min(all_lngs) < -122 and 37 < min(all_lats) < 38:
            print("\n✓ Coordinates appear to be in WGS84 (standard lat/lng)")
            print("  These represent actual street centerline geometries in San Francisco")
        else:
            print("\n⚠ Coordinates may be in a different coordinate system")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
Based on the analysis:

1. GlobalID: Appears to be a unique identifier for each blockface segment
   - Can be used as a primary key if all values are unique

2. Shape (LineString): Represents the street centerline geometry
   - Contains multiple coordinate points defining the path of the street
   - Coordinates are in WGS84 (longitude, latitude)
   - Each LineString represents one blockface segment

3. Relationship to CNN_ID:
   - Some records have CNN_ID, some don't
   - Need to check if shape quality differs between these groups

4. What these represent:
   - These are street centerline geometries for blockface segments
   - Each segment runs from one intersection to another
   - The geometry shows the actual path of the street
   - This is different from curb lines - it's the center of the street
    """)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()