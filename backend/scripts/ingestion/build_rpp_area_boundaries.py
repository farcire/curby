#!/usr/bin/env python3
"""
Build RPP Area Geographic Boundaries from Existing Regulations

This script analyzes all parking regulations that successfully matched to segments
to reverse-engineer the geographic boundaries of each RPP area (A, B, C, etc.).

Strategy:
1. Query all regulations with geometry that matched to segments
2. Group by RPP area (rpparea1, rpparea2, rpparea3)
3. For each RPP area, collect all associated:
   - CNNs (street segment IDs)
   - Blockface IDs
   - Supervisor districts
   - Neighborhoods
4. Create a mapping: RPP_AREA → {CNNs, blockfaces, districts, neighborhoods}
5. Use this mapping to assign the 9 regulations without geometry to segments

Output: rpp_area_boundaries.json
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from collections import defaultdict
import json

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    print("=" * 70)
    print("BUILDING RPP AREA GEOGRAPHIC BOUNDARIES")
    print("=" * 70)
    print()
    
    # Step 1: Get all parking regulations from raw collection
    print("Step 1: Fetching all parking regulations...")
    regulations = await db.parking_regulations.find({}).to_list(length=10000)
    print(f"✓ Found {len(regulations)} total regulations")
    
    # Step 2: Get all street segments with rules
    print("\nStep 2: Fetching street segments with parking rules...")
    segments = await db.street_segments.find({"rules": {"$exists": True, "$ne": []}}).to_list(length=50000)
    print(f"✓ Found {len(segments)} segments with rules")
    
    # Step 3: Build RPP area mapping
    print("\nStep 3: Building RPP area boundaries...")
    rpp_boundaries = defaultdict(lambda: {
        "cnns": set(),
        "blockfaces": set(),
        "supervisor_districts": set(),
        "neighborhoods": set(),
        "streets": set(),
        "regulation_count": 0
    })
    
    # Analyze regulations that matched to segments
    for segment in segments:
        cnn = segment.get("cnn")
        supervisor_district = segment.get("supervisor_district")
        street_name = segment.get("streetName")
        
        for rule in segment.get("rules", []):
            permit_area = rule.get("permitArea")
            
            if permit_area:
                # Add this segment's info to the RPP area boundary
                rpp_boundaries[permit_area]["cnns"].add(str(cnn))
                rpp_boundaries[permit_area]["regulation_count"] += 1
                
                if supervisor_district:
                    rpp_boundaries[permit_area]["supervisor_districts"].add(str(supervisor_district))
                
                if street_name:
                    rpp_boundaries[permit_area]["streets"].add(street_name)
    
    # Also check raw regulations for additional metadata
    for reg in regulations:
        for area_field in ["rpparea1", "rpparea2", "rpparea3"]:
            area = reg.get(area_field)
            if area and str(area).lower() not in ['nan', 'none', '']:
                neighborhood = reg.get("neighborhood")
                if neighborhood and str(neighborhood).lower() not in ['nan', 'none', '']:
                    rpp_boundaries[area]["neighborhoods"].add(neighborhood)
    
    # Convert sets to lists for JSON serialization
    rpp_output = {}
    for area, data in rpp_boundaries.items():
        rpp_output[area] = {
            "cnns": sorted(list(data["cnns"])),
            "supervisor_districts": sorted(list(data["supervisor_districts"])),
            "neighborhoods": sorted(list(data["neighborhoods"])),
            "streets": sorted(list(data["streets"]))[:50],  # Limit to first 50 streets
            "regulation_count": data["regulation_count"],
            "cnn_count": len(data["cnns"])
        }
    
    # Save to file
    with open('rpp_area_boundaries.json', 'w') as f:
        json.dump(rpp_output, f, indent=2)
    
    print(f"✓ Built boundaries for {len(rpp_output)} RPP areas")
    print()
    
    # Print summary
    print("=" * 70)
    print("RPP AREA SUMMARY")
    print("=" * 70)
    for area in sorted(rpp_output.keys()):
        data = rpp_output[area]
        print(f"\nRPP Area {area}:")
        print(f"  CNNs: {data['cnn_count']}")
        print(f"  Regulations: {data['regulation_count']}")
        print(f"  Districts: {', '.join(data['supervisor_districts']) if data['supervisor_districts'] else 'Unknown'}")
        print(f"  Neighborhoods: {', '.join(data['neighborhoods'][:3]) if data['neighborhoods'] else 'Unknown'}")
        if data['streets']:
            print(f"  Sample streets: {', '.join(data['streets'][:5])}")
    
    print()
    print("=" * 70)
    print("✓ Saved to rpp_area_boundaries.json")
    print("=" * 70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())