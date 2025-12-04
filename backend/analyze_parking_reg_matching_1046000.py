import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
from sodapy import Socrata
from shapely.geometry import shape, Point
import json

async def main():
    load_dotenv()
    
    # MongoDB connection
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("="*80)
    print("ANALYZING PARKING REGULATION MATCHING FOR CNN 1046000")
    print("20th Street South 2801-2899")
    print("="*80)
    
    # Get the street segment data
    print("\n1. STREET SEGMENT DATA (CNN 1046000)")
    print("-" * 80)
    segments = await db.street_segments.find({"cnn": "1046000"}).to_list(None)
    
    for seg in segments:
        side = seg.get('side')
        print(f"\nCNN 1046000 Side {side}:")
        print(f"  Address Range: {seg.get('fromAddress')} - {seg.get('toAddress')}")
        print(f"  Cardinal Direction: {seg.get('cardinalDirection')}")
        print(f"  Display Name: {seg.get('displayName')}")
        
        # Show centerline geometry
        centerline = seg.get('centerlineGeometry')
        if centerline:
            coords = centerline.get('coordinates', [])
            print(f"  Centerline: {len(coords)} points")
            if coords:
                print(f"    Start: {coords[0]}")
                print(f"    End: {coords[-1]}")
        
        # Show blockface geometry
        blockface = seg.get('blockfaceGeometry')
        if blockface:
            coords = blockface.get('coordinates', [])
            print(f"  Blockface: {len(coords)} points")
            if coords:
                print(f"    Start: {coords[0]}")
                print(f"    End: {coords[-1]}")
        
        # Show all rules
        rules = seg.get('rules', [])
        print(f"\n  Rules ({len(rules)} total):")
        for i, rule in enumerate(rules, 1):
            rule_type = rule.get('type')
            if rule_type == 'street-sweeping':
                print(f"    {i}. SWEEPING: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                print(f"       Blockside: {rule.get('blockside')}")
            elif rule_type == 'parking-regulation':
                print(f"    {i}. PARKING: {rule.get('regulation')}")
                print(f"       Days: {rule.get('days')}, Hours: {rule.get('fromTime')}-{rule.get('toTime')}")
                print(f"       Time Limit: {rule.get('timeLimit')} hrs")
                print(f"       Permit Area: {rule.get('permitArea')}")
                print(f"       Match Confidence: {rule.get('matchConfidence', 'N/A')}")
            else:
                print(f"    {i}. {rule_type}: {rule.get('regulation', 'N/A')}")
    
    # Get parking regulations from raw collection
    print("\n\n2. RAW PARKING REGULATIONS NEAR CNN 1046000")
    print("-" * 80)
    
    # Get centerline geometry for spatial query
    centerline_geo = None
    for seg in segments:
        if seg.get('centerlineGeometry'):
            centerline_geo = seg.get('centerlineGeometry')
            break
    
    if centerline_geo:
        # Get center point of the line
        line_shape = shape(centerline_geo)
        center_point = line_shape.interpolate(0.5, normalized=True)
        
        print(f"\nSearching for regulations near: {center_point.coords[0]}")
        
        # Query parking regulations within ~100 meters
        nearby_regs = await db.parking_regulations.find({
            "shape": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": list(center_point.coords[0])
                    },
                    "$maxDistance": 100  # meters
                }
            }
        }).limit(20).to_list(None)
        
        print(f"\nFound {len(nearby_regs)} parking regulations within 100m")
        
        for i, reg in enumerate(nearby_regs, 1):
            print(f"\n  Regulation #{i}:")
            print(f"    Regulation: {reg.get('regulation')}")
            print(f"    Days: {reg.get('days')}")
            print(f"    Hours: {reg.get('hours')}")
            print(f"    Time Limit: {reg.get('hrlimit')} hrs")
            print(f"    Permit Area: {reg.get('rpparea1') or reg.get('rpparea2')}")
            
            # Show geometry
            reg_geo = reg.get('shape')
            if reg_geo and isinstance(reg_geo, dict):
                coords = reg_geo.get('coordinates', [])
                if coords:
                    print(f"    Geometry: {len(coords)} points")
                    if len(coords) > 0:
                        print(f"      Start: {coords[0]}")
                        print(f"      End: {coords[-1]}")
                    
                    # Calculate distance from centerline
                    try:
                        reg_line = shape(reg_geo)
                        distance = reg_line.distance(line_shape)
                        print(f"    Distance from centerline: {distance:.6f} degrees (~{distance * 111000:.1f} meters)")
                    except:
                        pass
    
    # Check Socrata data directly
    print("\n\n3. CHECKING SOCRATA PARKING REGULATIONS DATASET")
    print("-" * 80)
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    socrata = Socrata("data.sfgov.org", app_token)
    
    # Query by street name
    print("\nQuerying for '20TH ST' regulations...")
    regs_data = socrata.get("hi6h-neyh",
                            streetname="20TH ST",
                            limit=100)
    
    print(f"Found {len(regs_data)} regulations for 20TH ST")
    
    # Filter for our address range
    print("\nFiltering for regulations near 2800-2899 block...")
    relevant_regs = []
    
    for reg in regs_data:
        # Check if geometry is near our centerline
        reg_geo = reg.get('shape')
        if reg_geo and centerline_geo:
            try:
                reg_line = shape(reg_geo)
                line_shape = shape(centerline_geo)
                distance = reg_line.distance(line_shape)
                
                # If within ~50 meters
                if distance < 0.0005:
                    relevant_regs.append({
                        'regulation': reg.get('regulation'),
                        'days': reg.get('days'),
                        'hours': reg.get('hours'),
                        'hrlimit': reg.get('hrlimit'),
                        'permit': reg.get('rpparea1') or reg.get('rpparea2'),
                        'distance': distance
                    })
            except:
                pass
    
    print(f"\nFound {len(relevant_regs)} regulations within 50m of CNN 1046000:")
    for i, reg in enumerate(relevant_regs, 1):
        print(f"\n  {i}. {reg['regulation']}")
        print(f"     Days: {reg['days']}, Hours: {reg['hours']}")
        print(f"     Time Limit: {reg['hrlimit']} hrs, Permit: {reg['permit']}")
        print(f"     Distance: {reg['distance']:.6f} degrees (~{reg['distance'] * 111000:.1f}m)")
    
    # Summary
    print("\n\n4. MATCHING SUMMARY")
    print("="*80)
    
    for seg in segments:
        side = seg.get('side')
        cardinal = seg.get('cardinalDirection')
        parking_rules = [r for r in seg.get('rules', []) if r.get('type') == 'parking-regulation']
        
        print(f"\nCNN 1046000 Side {side} ({cardinal}):")
        print(f"  Address Range: {seg.get('fromAddress')} - {seg.get('toAddress')}")
        print(f"  Parking Regulations Matched: {len(parking_rules)}")
        
        if parking_rules:
            for rule in parking_rules:
                print(f"    - {rule.get('regulation')}")
                print(f"      Confidence: {rule.get('matchConfidence', 'N/A')}")
        else:
            print(f"    ⚠️  No parking regulations matched!")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())