import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def investigate():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("INVESTIGATING 20TH STREET DATA")
    print("=" * 80)
    
    # Get ALL 20th Street data from original collections
    print("\n--- STREET SWEEPING SCHEDULES for 20TH ST ---")
    sweeping = await db.street_cleaning_schedules.find({
        "streetname": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    print(f"Found {len(sweeping)} street sweeping records")
    for i, s in enumerate(sweeping, 1):
        print(f"\nRecord #{i}:")
        print(f"  CNN: {s.get('cnn')}")
        print(f"  Street: {s.get('streetname')}")
        print(f"  Side: {s.get('cnnrightleft')}")
        print(f"  Day: {s.get('weekday')}")
        print(f"  Time: {s.get('fromhour')} - {s.get('tohour')}")
        print(f"  Corridor: {s.get('corridorname')}")
        print(f"  Limits: {s.get('lf_fadd')} to {s.get('lf_toadd')}")
    
    print("\n" + "=" * 80)
    print("PARKING REGULATIONS near 20TH ST")
    print("=" * 80)
    
    # Get parking regulations that might apply to 20th street
    regs = await db.parking_regulations.find({
        "$or": [
            {"streetname": {"$regex": "20TH", "$options": "i"}},
            {"analysis_neighborhood": "Mission"}
        ]
    }).limit(20).to_list(None)
    
    print(f"\nFound {len(regs)} regulations")
    for i, r in enumerate(regs[:10], 1):  # Show first 10
        print(f"\nRegulation #{i}:")
        print(f"  Regulation: {r.get('regulation')}")
        print(f"  Days: {r.get('days')}")
        print(f"  Hours: {r.get('hours')}")
        print(f"  Time Limit: {r.get('hrlimit')}")
        print(f"  Permit Area: {r.get('rpparea1')}")
        details = r.get('regdetails', 'N/A')
        if isinstance(details, str):
            print(f"  Details: {details[:100]}")
        else:
            print(f"  Details: {details}")
        
        # Check geometry
        geom = r.get('shape')
        if geom and isinstance(geom, dict):
            coords = geom.get('coordinates', [])
            if coords:
                print(f"  Coordinates: {len(coords)} points")
                if len(coords) > 0:
                    print(f"    First point: {coords[0]}")
    
    print("\n" + "=" * 80)
    print("20TH STREET BLOCKFACES IN DATABASE")
    print("=" * 80)
    
    blockfaces = await db.blockfaces.find({
        "streetName": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    for bf in blockfaces:
        print(f"\nBlockface CNN: {bf.get('cnn')}")
        print(f"Side: {bf.get('side')}")
        print(f"ID: {bf.get('id')}")
        
        # Get geometry bounds
        geom = bf.get('geometry')
        if geom and isinstance(geom, dict):
            coords = geom.get('coordinates', [])
            if coords and len(coords) > 0:
                print(f"Geometry: {len(coords)} coordinate points")
                print(f"  Start: {coords[0]}")
                print(f"  End: {coords[-1]}")
        
        rules = bf.get('rules', [])
        print(f"Total rules: {len(rules)}")
        for rule in rules:
            rule_type = rule.get('type')
            if rule_type == 'street-sweeping':
                print(f"  {rule_type}: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
            elif rule_type == 'parking-regulation':
                print(f"  {rule_type}: {rule.get('regulation')} - {rule.get('days')} {rule.get('fromTime')}-{rule.get('toTime')}")
    
    # Check what's between Bryant and Florida
    print("\n" + "=" * 80)
    print("CHECKING SPECIFIC LOCATION: 20TH between Bryant and Florida")
    print("=" * 80)
    print("Expected:")
    print("  North side (Left): No parking Thursday 9am-11am (street cleaning)")
    print("  South side (Right): No parking Tuesday 9am-11am + 1hr parking 8am-6pm M-F (non-RPP)")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(investigate())