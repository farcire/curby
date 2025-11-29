import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
from shapely.geometry import shape, Point

async def analyze():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("ANALYZING 20TH STREET: Block between Bryant and Florida")
    print("=" * 80)
    
    # First, let's find Bryant and Florida Street coordinates
    bryant = await db.streets.find_one({"streetname": {"$regex": "^BRYANT", "$options": "i"}})
    florida = await db.streets.find_one({"streetname": {"$regex": "^FLORIDA", "$options": "i"}})
    
    print("\n--- REFERENCE STREETS ---")
    if bryant:
        print(f"Bryant St CNN: {bryant.get('cnn')}")
    if florida:
        print(f"Florida St CNN: {florida.get('cnn')}")
    
    # Get ALL 20th Street records
    print("\n--- ALL 20TH STREET SEGMENTS ---")
    streets_20th = await db.streets.find({"streetname": {"$regex": "^20TH", "$options": "i"}}).to_list(None)
    print(f"Found {len(streets_20th)} segments of 20TH ST")
    
    for st in streets_20th:
        print(f"\nCNN {st.get('cnn')}:")
        print(f"  Street: {st.get('street')}")
        print(f"  From: {st.get('st_name')} to {st.get('st_name_to')}")
        print(f"  Layer: {st.get('layer')}")
        print(f"  Zip: {st.get('zip_code')}")
        
        # Get geometry bounds
        geom = st.get('line')
        if geom:
            try:
                line = shape(geom)
                coords = list(line.coords)
                print(f"  Start point: {coords[0]}")
                print(f"  End point: {coords[-1]}")
            except:
                pass
    
    # Get blockfaces for 20th Street
    print("\n" + "=" * 80)
    print("BLOCKFACES ON 20TH STREET")
    print("=" * 80)
    
    blockfaces = await db.blockfaces.find({"streetName": {"$regex": "^20TH", "$options": "i"}}).to_list(None)
    print(f"Found {len(blockfaces)} blockfaces")
    
    for bf in blockfaces:
        print(f"\n--- Blockface CNN {bf.get('cnn')} Side {bf.get('side')} ---")
        
        # Get the street info for this CNN
        street = await db.streets.find_one({"cnn": bf.get('cnn')})
        if street:
            print(f"Street segment: {street.get('st_name')} to {street.get('st_name_to')}")
        
        # Show geometry
        geom = bf.get('geometry')
        if geom:
            try:
                line = shape(geom)
                coords = list(line.coords)
                print(f"Geometry: {len(coords)} points")
                print(f"  Start: {coords[0]}")
                print(f"  End: {coords[-1]}")
            except Exception as e:
                print(f"  Geometry error: {e}")
        
        # Show all rules
        rules = bf.get('rules', [])
        print(f"Rules ({len(rules)} total):")
        for rule in rules:
            rtype = rule.get('type')
            if rtype == 'street-sweeping':
                print(f"  - SWEEPING: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
            elif rtype == 'parking-regulation':
                reg = rule.get('regulation', 'Unknown')
                days = rule.get('days', 'N/A')
                hours = rule.get('hours', 'N/A')
                limit = rule.get('timeLimit', 'N/A')
                area = rule.get('permitArea', 'N/A')
                print(f"  - REGULATION: {reg}, {limit}hr limit, Area {area}, {days} {hours}")
    
    # Compare with expected data
    print("\n" + "=" * 80)
    print("EXPECTED vs ACTUAL")
    print("=" * 80)
    print("\nEXPECTED for 20th St between Bryant and Florida:")
    print("  North side (Left): No parking Thursday 9am-11am (street cleaning)")
    print("  South side (Right): No parking Tuesday 9am-11am + 1hr parking 8am-6pm M-F (non-RPP)")
    
    print("\nACTUAL in database:")
    for bf in blockfaces:
        side = bf.get('side')
        print(f"\n  Side {side}:")
        rules = bf.get('rules', [])
        sweeps = [r for r in rules if r.get('type') == 'street-sweeping']
        regs = [r for r in rules if r.get('type') == 'parking-regulation']
        
        if sweeps:
            for s in sweeps:
                print(f"    - Sweeping: {s.get('day')} {s.get('startTime')}-{s.get('endTime')}")
        
        if regs:
            for r in regs:
                print(f"    - Parking: {r.get('regulation')}, {r.get('timeLimit')}hr, {r.get('days')} {r.get('hours')}")
    
    print("\n" + "=" * 80)
    print("ISSUE ANALYSIS")
    print("=" * 80)
    print("\nPotential Issues:")
    print("1. Times don't match:")
    print("   - Expected sweeping: 9am-11am")
    print("   - Actual sweeping: 6am-8am")
    print("\n2. Multiple blocks of 20th St may exist")
    print("3. Data might be from wrong street segment")
    print("4. Need to verify we're looking at Bryant-Florida block specifically")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(analyze())