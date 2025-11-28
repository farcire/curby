#!/usr/bin/env python3
"""
Query 20th Street parking regulations between Bryant and Florida
"""
import asyncio
import motor.motor_asyncio
import os
import sys
from dotenv import load_dotenv

async def main():
    # Load environment variables
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI not set")
        sys.exit(1)
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    print("="*70)
    print("20TH STREET PARKING REGULATIONS")
    print("Between Bryant and York Streets")
    print("="*70)
    
    # First, let's find all 20th Street segments and look at their coordinates
    # Bryant is around -122.409770, York is around -122.406947
    all_20th = await db.street_segments.find({
        "streetName": {"$regex": "20TH", "$options": "i"}
    }).to_list(length=100)
    
    print(f"\nFound {len(all_20th)} total 20th Street segments")
    
    # Filter for segments between Bryant (CNN 3309000) and York
    # Based on coordinates: Bryant ~-122.4098, York ~-122.4069
    # We want segments with longitude between these values
    segments = []
    for seg in all_20th:
        cnn = seg.get('cnn')
        geom = seg.get('centerlineGeometry')
        if geom and geom.get('coordinates'):
            coords = geom['coordinates']
            if len(coords) >= 2:
                # Check if segment is in the Bryant-York range
                lng_start = coords[0][0]
                lng_end = coords[-1][0]
                # Bryant to York: approximately -122.4098 to -122.4069
                if (-122.4098 <= lng_start <= -122.4069) or (-122.4098 <= lng_end <= -122.4069):
                    segments.append(seg)
                    print(f"  Including CNN {cnn}: {lng_start:.6f} to {lng_end:.6f}")
    
    if not segments:
        print("\n❌ No segments found")
    else:
        print(f"\n✅ Found {len(segments)} segments\n")
        
        # Group by side
        left_side = [s for s in segments if s.get('side') == 'L']
        right_side = [s for s in segments if s.get('side') == 'R']
        
        for side_name, side_segments in [("LEFT SIDE", left_side), ("RIGHT SIDE", right_side)]:
            print(f"\n{'='*70}")
            print(f"{side_name}")
            print('='*70)
            
            if not side_segments:
                print("  No data for this side")
                continue
            
            for seg in side_segments:
                print(f"\nCNN: {seg.get('cnn')}")
                print(f"From: {seg.get('fromStreet')} → To: {seg.get('toStreet')}")
                
                # Show all rules
                rules = seg.get('rules', [])
                if rules:
                    print(f"\nRegulations ({len(rules)} total):")
                    for i, rule in enumerate(rules, 1):
                        rule_type = rule.get('type', 'unknown')
                        print(f"\n  {i}. {rule_type.upper()}")
                        
                        if rule_type == 'street-sweeping':
                            print(f"     Day: {rule.get('day')}")
                            print(f"     Time: {rule.get('startTime')} - {rule.get('endTime')}")
                        
                        elif rule_type == 'parking-regulation':
                            print(f"     Regulation: {rule.get('regulation')}")
                            if rule.get('permitArea'):
                                print(f"     🅿️  RPP AREA: {rule.get('permitArea')}")
                            if rule.get('timeLimit'):
                                print(f"     Time Limit: {rule.get('timeLimit')} hours")
                            if rule.get('days'):
                                print(f"     Days: {rule.get('days')}")
                            if rule.get('hours'):
                                print(f"     Hours: {rule.get('hours')}")
                else:
                    print("\n  ⚠️  No regulations found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())