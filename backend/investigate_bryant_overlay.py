#!/usr/bin/env python3
"""
Investigate Bryant St East 1901-1999 overlay positioning issue.

This script will:
1. Find all Bryant St segments in the database
2. Check for segments with address range 1901-1999
3. Examine geometry data (centerlineGeometry vs blockfaceGeometry)
4. Verify CNN and side assignments
5. Identify potential data quality issues
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise Exception("MONGODB_URI environment variable not set")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.curby


async def investigate_bryant_street():
    """Investigate Bryant Street segments, focusing on 1901-1999 range."""
    
    print("=" * 80)
    print("INVESTIGATING BRYANT STREET OVERLAY ISSUE")
    print("=" * 80)
    print()
    
    # Find all Bryant Street segments
    print("1. Finding all Bryant Street segments...")
    bryant_segments = []
    async for doc in db.street_segments.find({"streetName": {"$regex": "^BRYANT", "$options": "i"}}):
        bryant_segments.append(doc)
    
    print(f"   Found {len(bryant_segments)} Bryant Street segments")
    print()
    
    # Find segments with address range containing 1901-1999
    print("2. Looking for segments with address range 1901-1999...")
    target_segments = []
    
    for seg in bryant_segments:
        from_addr = seg.get("fromAddress")
        to_addr = seg.get("toAddress")
        
        if from_addr and to_addr:
            try:
                from_num = int(from_addr)
                to_num = int(to_addr)
                
                # Check if range overlaps with 1901-1999
                if (from_num <= 1999 and to_num >= 1901):
                    target_segments.append(seg)
                    print(f"   ✓ Found: CNN={seg.get('cnn')}, Side={seg.get('side')}, Range={from_addr}-{to_addr}")
            except (ValueError, TypeError):
                pass
    
    print(f"   Total segments in/near 1901-1999 range: {len(target_segments)}")
    print()
    
    # Analyze each target segment in detail
    print("3. Detailed analysis of target segments:")
    print()
    
    for i, seg in enumerate(target_segments, 1):
        print(f"   SEGMENT {i}:")
        print(f"   {'=' * 70}")
        print(f"   CNN: {seg.get('cnn')}")
        print(f"   Side: {seg.get('side')}")
        print(f"   Street Name: {seg.get('streetName')}")
        print(f"   Address Range: {seg.get('fromAddress')} - {seg.get('toAddress')}")
        print(f"   From Street: {seg.get('fromStreet')}")
        print(f"   To Street: {seg.get('toStreet')}")
        print(f"   Cardinal Direction: {seg.get('cardinalDirection')}")
        print(f"   Display Name: {seg.get('displayName')}")
        print()
        
        # Check geometry data
        has_centerline = seg.get('centerlineGeometry') is not None
        has_blockface = seg.get('blockfaceGeometry') is not None
        
        print(f"   Geometry Status:")
        print(f"   - centerlineGeometry: {'✓ Present' if has_centerline else '✗ Missing'}")
        print(f"   - blockfaceGeometry: {'✓ Present' if has_blockface else '✗ Missing'}")
        
        if has_centerline:
            centerline = seg.get('centerlineGeometry')
            coords = centerline.get('coordinates', [])
            print(f"   - centerlineGeometry type: {centerline.get('type')}")
            print(f"   - centerlineGeometry points: {len(coords)}")
            if coords:
                print(f"   - First point: {coords[0]}")
                print(f"   - Last point: {coords[-1]}")
        
        if has_blockface:
            blockface = seg.get('blockfaceGeometry')
            coords = blockface.get('coordinates', [])
            print(f"   - blockfaceGeometry type: {blockface.get('type')}")
            print(f"   - blockfaceGeometry points: {len(coords)}")
            if coords:
                print(f"   - First point: {coords[0]}")
                print(f"   - Last point: {coords[-1]}")
        
        print()
        
        # Check rules
        rules = seg.get('rules', [])
        print(f"   Rules: {len(rules)} total")
        for rule in rules[:3]:  # Show first 3 rules
            print(f"   - Type: {rule.get('type')}, Description: {rule.get('description', 'N/A')[:50]}")
        if len(rules) > 3:
            print(f"   ... and {len(rules) - 3} more rules")
        
        print()
        print()
    
    # Check for potential issues
    print("4. Data Quality Analysis:")
    print()
    
    issues = []
    
    # Issue 1: Missing blockfaceGeometry
    missing_blockface = [s for s in target_segments if not s.get('blockfaceGeometry')]
    if missing_blockface:
        issues.append(f"Missing blockfaceGeometry: {len(missing_blockface)} segments")
        print(f"   ⚠ {len(missing_blockface)} segments missing blockfaceGeometry")
        print(f"      (Using centerlineGeometry as fallback)")
    
    # Issue 2: Check if we have both L and R sides
    sides = set(s.get('side') for s in target_segments)
    if len(sides) < 2:
        issues.append(f"Only one side present: {sides}")
        print(f"   ⚠ Only one side of street found: {sides}")
        print(f"      (Expected both 'L' and 'R' for complete coverage)")
    
    # Issue 3: Check for overlapping address ranges
    for i, seg1 in enumerate(target_segments):
        for seg2 in target_segments[i+1:]:
            if seg1.get('side') == seg2.get('side'):
                try:
                    from1, to1 = int(seg1.get('fromAddress', 0)), int(seg1.get('toAddress', 0))
                    from2, to2 = int(seg2.get('fromAddress', 0)), int(seg2.get('toAddress', 0))
                    
                    # Check for overlap
                    if not (to1 < from2 or to2 < from1):
                        issues.append(f"Overlapping ranges on same side: {seg1.get('cnn')} and {seg2.get('cnn')}")
                        print(f"   ⚠ Overlapping address ranges on same side:")
                        print(f"      CNN {seg1.get('cnn')} ({from1}-{to1}) overlaps with")
                        print(f"      CNN {seg2.get('cnn')} ({from2}-{to2})")
                except (ValueError, TypeError):
                    pass
    
    # Issue 4: Check cardinal direction assignment
    for seg in target_segments:
        cardinal = seg.get('cardinalDirection')
        side = seg.get('side')
        if not cardinal:
            issues.append(f"Missing cardinal direction: CNN {seg.get('cnn')}, Side {side}")
            print(f"   ⚠ Missing cardinal direction for CNN {seg.get('cnn')}, Side {side}")
    
    print()
    
    if not issues:
        print("   ✓ No obvious data quality issues detected")
    else:
        print(f"   Found {len(issues)} potential issues")
    
    print()
    
    # Summary
    print("5. Summary:")
    print()
    print(f"   Total Bryant St segments: {len(bryant_segments)}")
    print(f"   Segments in 1901-1999 range: {len(target_segments)}")
    print(f"   Sides represented: {', '.join(sorted(sides))}")
    print(f"   Data quality issues: {len(issues)}")
    print()
    
    # Export detailed data for further analysis
    export_data = []
    for seg in target_segments:
        export_data.append({
            'cnn': seg.get('cnn'),
            'side': seg.get('side'),
            'streetName': seg.get('streetName'),
            'fromAddress': seg.get('fromAddress'),
            'toAddress': seg.get('toAddress'),
            'fromStreet': seg.get('fromStreet'),
            'toStreet': seg.get('toStreet'),
            'cardinalDirection': seg.get('cardinalDirection'),
            'has_centerlineGeometry': seg.get('centerlineGeometry') is not None,
            'has_blockfaceGeometry': seg.get('blockfaceGeometry') is not None,
            'rules_count': len(seg.get('rules', []))
        })
    
    with open('backend/bryant_overlay_analysis.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"   Detailed data exported to: backend/bryant_overlay_analysis.json")
    print()
    
    print("=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)


async def main():
    try:
        await investigate_bryant_street()
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())