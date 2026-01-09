import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def main():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("BRYANT STREET INVESTIGATION - Address Range 1900-1999")
    print("=" * 80)
    print()
    
    # Find all Bryant Street segments
    bryant_segments = await db.street_segments.find({
        "streetName": {"$regex": "^BRYANT", "$options": "i"}
    }).to_list(None)
    
    print(f"Total Bryant St segments: {len(bryant_segments)}")
    print()
    
    # Find segments with address ranges near 1900-1999
    target_segments = []
    for seg in bryant_segments:
        from_addr = seg.get("fromAddress")
        to_addr = seg.get("toAddress")
        
        if from_addr and to_addr:
            try:
                from_num = int(from_addr)
                to_num = int(to_addr)
                
                # Check if range overlaps with 1900-1999
                if (from_num <= 1999 and to_num >= 1900):
                    target_segments.append(seg)
            except (ValueError, TypeError):
                pass
    
    print(f"Segments in/near 1900-1999 range: {len(target_segments)}")
    print()
    
    # Analyze each segment in detail
    for i, seg in enumerate(target_segments, 1):
        print(f"SEGMENT {i}:")
        print(f"  CNN: {seg.get('cnn')}")
        print(f"  Side: {seg.get('side')}")
        print(f"  Address Range: {seg.get('fromAddress')} - {seg.get('toAddress')}")
        print(f"  From Street: {seg.get('fromStreet')}")
        print(f"  To Street: {seg.get('toStreet')}")
        print(f"  Cardinal: {seg.get('cardinalDirection')}")
        print(f"  Display Name: {seg.get('displayName')}")
        
        # Check geometries
        has_centerline = seg.get('centerlineGeometry') is not None
        has_blockface = seg.get('blockfaceGeometry') is not None
        print(f"  Centerline Geometry: {'✓' if has_centerline else '✗'}")
        print(f"  Blockface Geometry: {'✓' if has_blockface else '✗'}")
        
        if has_centerline:
            coords = seg['centerlineGeometry'].get('coordinates', [])
            print(f"    Centerline points: {len(coords)}")
            if coords:
                print(f"      First: {coords[0]}")
                print(f"      Last: {coords[-1]}")
        
        if has_blockface:
            coords = seg['blockfaceGeometry'].get('coordinates', [])
            print(f"    Blockface points: {len(coords)}")
            if coords:
                print(f"      First: {coords[0]}")
                print(f"      Last: {coords[-1]}")
        
        print(f"  Rules: {len(seg.get('rules', []))}")
        print()
    
    # Data quality checks
    print("=" * 80)
    print("DATA QUALITY CHECKS:")
    print("=" * 80)
    print()
    
    # Check 1: Both sides present?
    sides = set(s.get('side') for s in target_segments)
    print(f"1. Sides present: {', '.join(sorted(sides))}")
    if len(sides) < 2:
        print("   ⚠ WARNING: Only one side found (expected both L and R)")
    else:
        print("   ✓ Both sides present")
    print()
    
    # Check 2: Overlapping ranges on same side?
    print("2. Checking for overlapping address ranges on same side:")
    found_overlap = False
    for i, seg1 in enumerate(target_segments):
        for seg2 in target_segments[i+1:]:
            if seg1.get('side') == seg2.get('side'):
                try:
                    from1, to1 = int(seg1.get('fromAddress', 0)), int(seg1.get('toAddress', 0))
                    from2, to2 = int(seg2.get('fromAddress', 0)), int(seg2.get('toAddress', 0))
                    
                    if not (to1 < from2 or to2 < from1):
                        print(f"   ⚠ OVERLAP DETECTED:")
                        print(f"      CNN {seg1.get('cnn')} Side {seg1.get('side')} ({from1}-{to1})")
                        print(f"      CNN {seg2.get('cnn')} Side {seg2.get('side')} ({from2}-{to2})")
                        found_overlap = True
                except (ValueError, TypeError):
                    pass
    
    if not found_overlap:
        print("   ✓ No overlaps detected")
    print()
    
    # Check 3: Missing cardinal directions?
    print("3. Checking cardinal directions:")
    missing_cardinal = [s for s in target_segments if not s.get('cardinalDirection')]
    if missing_cardinal:
        print(f"   ⚠ {len(missing_cardinal)} segments missing cardinal direction:")
        for s in missing_cardinal:
            print(f"      CNN {s.get('cnn')}, Side {s.get('side')}")
    else:
        print("   ✓ All segments have cardinal directions")
    print()
    
    # Check 4: Missing blockface geometry?
    print("4. Checking blockface geometry coverage:")
    missing_blockface = [s for s in target_segments if not s.get('blockfaceGeometry')]
    if missing_blockface:
        print(f"   ⚠ {len(missing_blockface)} segments missing blockfaceGeometry:")
        for s in missing_blockface:
            print(f"      CNN {s.get('cnn')}, Side {s.get('side')}")
        print(f"   Note: These will use centerlineGeometry as fallback")
    else:
        print("   ✓ All segments have blockface geometry")
    print()
    
    # Export data
    export_data = []
    for seg in target_segments:
        export_data.append({
            'cnn': seg.get('cnn'),
            'side': seg.get('side'),
            'fromAddress': seg.get('fromAddress'),
            'toAddress': seg.get('toAddress'),
            'fromStreet': seg.get('fromStreet'),
            'toStreet': seg.get('toStreet'),
            'cardinalDirection': seg.get('cardinalDirection'),
            'has_centerline': seg.get('centerlineGeometry') is not None,
            'has_blockface': seg.get('blockfaceGeometry') is not None,
            'rules_count': len(seg.get('rules', []))
        })
    
    output_file = 'backend/bryant_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Detailed data exported to: {output_file}")
    print()
    print("=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())