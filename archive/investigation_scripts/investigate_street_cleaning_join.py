import requests
import json
from collections import defaultdict

# Street Cleaning dataset
STREET_CLEANING_ID = "yhqp-riqs"
base_url = f"https://data.sfgov.org/resource/{STREET_CLEANING_ID}.json"

print("=" * 80)
print("STREET CLEANING DATASET (yhqp-riqs) - COMPREHENSIVE JOIN ANALYSIS")
print("=" * 80)

# Fetch sample records with all fields
params = {
    "$limit": 100,
    "$select": "*"
}

try:
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    records = response.json()
    
    print(f"\nFetched {len(records)} street cleaning records\n")
    
    # Analyze fields
    print("=" * 80)
    print("1. AVAILABLE FIELDS")
    print("=" * 80)
    
    if records:
        sample = records[0]
        print("\nFields in dataset:")
        for key in sorted(sample.keys()):
            value = sample[key]
            value_str = str(value)[:50] if value else "None"
            print(f"  {key}: {value_str}")
    
    # Check for CNN, side, BlockSweep, and geometry fields
    print("\n" + "=" * 80)
    print("2. KEY FIELD ANALYSIS")
    print("=" * 80)
    
    cnn_fields = []
    side_fields = []
    blocksweep_fields = []
    geometry_fields = []
    blockside_fields = []
    
    for key in sample.keys():
        key_lower = key.lower()
        if 'cnn' in key_lower:
            cnn_fields.append(key)
        if 'side' in key_lower or 'left' in key_lower or 'right' in key_lower:
            side_fields.append(key)
        if 'blocksweep' in key_lower or 'block_sweep' in key_lower:
            blocksweep_fields.append(key)
        if 'geometry' in key_lower or 'shape' in key_lower or 'line' in key_lower:
            geometry_fields.append(key)
        if 'blockside' in key_lower or 'block_side' in key_lower:
            blockside_fields.append(key)
    
    print(f"\nCNN-related fields: {cnn_fields}")
    print(f"Side-related fields (L/R): {side_fields}")
    print(f"BlockSweep ID fields: {blocksweep_fields}")
    print(f"Geometry/LineString fields: {geometry_fields}")
    print(f"Blockside (cardinal direction) fields: {blockside_fields}")
    
    # Analyze CNN coverage
    print("\n" + "=" * 80)
    print("3. CNN COVERAGE ANALYSIS")
    print("=" * 80)
    
    cnn_counts = defaultdict(int)
    side_counts = defaultdict(int)
    cnn_side_combinations = defaultdict(int)
    
    records_with_cnn = 0
    records_with_side = 0
    
    for rec in records:
        # Check various CNN field names
        cnn = rec.get('cnn') or rec.get('cnn_id') or rec.get('streetcnn')
        side = rec.get('cnnrightleft') or rec.get('side')
        
        if cnn:
            records_with_cnn += 1
            cnn_counts[cnn] += 1
            
        if side:
            records_with_side += 1
            side_counts[side] += 1
            
        if cnn and side:
            cnn_side_combinations[f"{cnn}_{side}"] += 1
    
    print(f"\nRecords with CNN: {records_with_cnn}/{len(records)} ({records_with_cnn/len(records)*100:.1f}%)")
    print(f"Records with Side: {records_with_side}/{len(records)} ({records_with_side/len(records)*100:.1f}%)")
    
    print(f"\nSide value distribution:")
    for side, count in sorted(side_counts.items()):
        print(f"  {side}: {count} records")
    
    # Check for duplicate CNN+Side combinations
    print("\n" + "=" * 80)
    print("4. CNN + SIDE UNIQUENESS")
    print("=" * 80)
    
    duplicates = {combo: count for combo, count in cnn_side_combinations.items() if count > 1}
    
    if duplicates:
        print(f"\nFound {len(duplicates)} CNN+Side combinations with multiple records:")
        for combo, count in list(duplicates.items())[:5]:
            cnn, side = combo.split('_')
            print(f"  CNN {cnn} Side {side}: {count} records")
    else:
        print("\n✓ All CNN+Side combinations are unique")
    
    # Sample records with all join keys
    print("\n" + "=" * 80)
    print("5. SAMPLE RECORDS WITH JOIN KEYS")
    print("=" * 80)
    
    for i, rec in enumerate(records[:5], 1):
        print(f"\nRecord {i}:")
        print(f"  CNN: {rec.get('cnn') or rec.get('cnn_id') or rec.get('streetcnn')}")
        print(f"  Side (L/R): {rec.get('cnnrightleft') or rec.get('side')}")
        print(f"  BlockSweep ID: {rec.get('blocksweep_id') or rec.get('blocksweepid')}")
        print(f"  Blockside (Cardinal): {rec.get('blockside')}")
        
        # Check for geometry
        geom = rec.get('the_geom') or rec.get('geometry') or rec.get('shape')
        if geom:
            geom_type = geom.get('type') if isinstance(geom, dict) else 'Unknown'
            print(f"  Geometry Type: {geom_type}")
            if isinstance(geom, dict) and 'coordinates' in geom:
                coords = geom['coordinates']
                print(f"  Geometry Points: {len(coords) if isinstance(coords, list) else 'N/A'}")
        
        print(f"  Week: {rec.get('weekofmonth') or rec.get('week_of_month')}")
        print(f"  Day: {rec.get('weekday') or rec.get('day_of_week')}")
        print(f"  From Hour: {rec.get('fromhour') or rec.get('from_hour')}")
        print(f"  To Hour: {rec.get('tohour') or rec.get('to_hour')}")
        print(f"  Holidays: {rec.get('holidays')}")
    
    # Check total dataset size
    print("\n" + "=" * 80)
    print("6. DATASET SIZE")
    print("=" * 80)
    
    count_params = {"$select": "count(*) as total"}
    count_response = requests.get(base_url, params=count_params)
    if count_response.status_code == 200:
        total = count_response.json()[0]['total']
        print(f"\nTotal records in dataset: {total}")
    
    # Analyze BlockSweep ID and Blockside coverage
    print("\n" + "=" * 80)
    print("7. BLOCKSWEEP ID AND CARDINAL DIRECTION ANALYSIS")
    print("=" * 80)
    
    blocksweep_count = 0
    blockside_count = 0
    blockside_values = defaultdict(int)
    
    for rec in records:
        if rec.get('blocksweep_id') or rec.get('blocksweepid'):
            blocksweep_count += 1
        
        blockside = rec.get('blockside')
        if blockside:
            blockside_count += 1
            blockside_values[blockside] += 1
    
    print(f"\nRecords with BlockSweep ID: {blocksweep_count}/{len(records)} ({blocksweep_count/len(records)*100:.1f}%)")
    print(f"Records with Blockside (cardinal direction): {blockside_count}/{len(records)} ({blockside_count/len(records)*100:.1f}%)")
    
    if blockside_values:
        print(f"\nBlockside (Cardinal Direction) distribution:")
        for direction, count in sorted(blockside_values.items()):
            print(f"  {direction}: {count} records")
    
    # Verify join capability
    print("\n" + "=" * 80)
    print("8. COMPREHENSIVE JOIN CAPABILITY ASSESSMENT")
    print("=" * 80)
    
    print("\n✓ JOIN TO ACTIVE STREETS BY CNN + SIDE:")
    print(f"  - Has CNN field: {'✓' if cnn_fields else '✗'}")
    print(f"  - Has Side field (L/R): {'✓' if side_fields else '✗'}")
    print(f"  - CNN coverage: {records_with_cnn/len(records)*100:.1f}%")
    print(f"  - Side coverage: {records_with_side/len(records)*100:.1f}%")
    
    print("\n✓ ADDITIONAL RELATIONSHIPS TO PRESERVE:")
    print(f"  - BlockSweep ID: {'✓' if blocksweep_fields else '✗'} ({blocksweep_count/len(records)*100:.1f}% coverage)")
    print(f"  - Geometry/LineString: {'✓' if geometry_fields else '✗'}")
    print(f"  - Blockside (Cardinal): {'✓' if blockside_fields else '✗'} ({blockside_count/len(records)*100:.1f}% coverage)")
    
    if records_with_cnn == len(records) and records_with_side == len(records):
        print("\n✓✓✓ CONFIRMED: Can join ALL street cleaning data to Active Streets")
        print("\nJoin Strategy:")
        print("  1. Primary Join: street_cleaning.cnn = segment.cnn AND street_cleaning.side = segment.side")
        print("  2. Store BlockSweep ID: For future reference and joins")
        print("  3. Store Geometry: LineString for spatial operations")
        print("  4. Store Blockside: Cardinal direction (N/S/E/W) for each CNN L/R")
        print("\nData to Preserve in StreetSegment:")
        print("  - sweeping_blocksweep_id: For future joins")
        print("  - sweeping_geometry: LineString geometry")
        print("  - cardinal_direction: From Blockside field (N/S/E/W)")
    elif records_with_cnn > len(records) * 0.9:
        print("\n⚠ MOSTLY JOINABLE: >90% of records have CNN and Side")
    else:
        print("\n✗ INCOMPLETE: Some records missing CNN or Side fields")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()