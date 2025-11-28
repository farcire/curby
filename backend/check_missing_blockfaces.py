import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def check():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("CHECKING FOR MISSING BLOCKFACE GEOMETRIES")
    print("=" * 80)
    
    # Get all streets in our filtered area
    streets = await db.streets.find({}).to_list(None)
    print(f"\nTotal streets in database: {len(streets)}")
    
    # Get all unique CNNs from blockfaces
    blockface_cnns = set()
    blockfaces = await db.blockfaces.find({}, {"cnn": 1}).to_list(None)
    for bf in blockfaces:
        blockface_cnns.add(bf.get('cnn'))
    
    print(f"CNNs with blockfaces: {len(blockface_cnns)}")
    
    # Find CNNs without blockfaces
    missing_cnns = []
    for street in streets:
        cnn = street.get('cnn')
        if cnn and cnn not in blockface_cnns:
            missing_cnns.append(cnn)
    
    print(f"CNNs WITHOUT blockfaces: {len(missing_cnns)}")
    
    # Focus on 20th Street
    print("\n--- 20TH STREET ANALYSIS ---")
    streets_20th = [s for s in streets if '20TH' in s.get('streetname', '').upper()]
    print(f"Total 20th Street CNN segments: {len(streets_20th)}")
    
    missing_20th = []
    has_blockface_20th = []
    
    for st in streets_20th:
        cnn = st.get('cnn')
        if cnn in blockface_cnns:
            has_blockface_20th.append(cnn)
        else:
            missing_20th.append(cnn)
    
    print(f"  With blockfaces: {len(has_blockface_20th)} - {has_blockface_20th}")
    print(f"  WITHOUT blockfaces: {len(missing_20th)}")
    
    if missing_20th:
        print("\n  Missing CNNs:")
        for cnn in sorted(missing_20th):
            print(f"    {cnn}")
            
            # Check if this CNN has street sweeping data
            sweeping = await db.street_cleaning_schedules.find({"cnn": cnn}).to_list(None)
            if sweeping:
                print(f"      ✓ Has {len(sweeping)} street sweeping schedules")
                for s in sweeping[:2]:  # Show first 2
                    print(f"        - {s.get('weekday')} {s.get('fromhour')}-{s.get('tohour')} Side {s.get('cnnrightleft')}")
    
    # Check CNN 1046000 specifically
    print("\n--- CNN 1046000 SPECIFIC CHECK ---")
    target_cnn = "1046000"
    
    street_1046 = await db.streets.find_one({"cnn": target_cnn})
    if street_1046:
        print(f"✓ CNN {target_cnn} exists in streets collection")
        print(f"  Street: {street_1046.get('streetname')}")
        print(f"  Has centerline geometry: {'Yes' if street_1046.get('line') else 'No'}")
    else:
        print(f"✗ CNN {target_cnn} NOT in streets collection")
        print("  This means it was filtered out during ingestion")
    
    blockface_1046 = await db.blockfaces.find_one({"cnn": target_cnn})
    if blockface_1046:
        print(f"✓ CNN {target_cnn} has blockface")
    else:
        print(f"✗ CNN {target_cnn} has NO blockface geometry")
    
    sweeping_1046 = await db.street_cleaning_schedules.find({"cnn": target_cnn}).to_list(None)
    if sweeping_1046:
        print(f"✓ CNN {target_cnn} has {len(sweeping_1046)} street sweeping schedules:")
        for s in sweeping_1046:
            print(f"    {s.get('weekday')} {s.get('fromhour')}-{s.get('tohour')} Side {s.get('cnnrightleft')}")
            print(f"    Limits: {s.get('limits')}")
    else:
        print(f"✗ CNN {target_cnn} has NO sweeping data")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print(f"\nOut of {len(streets)} street segments in our database:")
    print(f"  {len(blockface_cnns)} have blockface geometries ({len(blockface_cnns)/len(streets)*100:.1f}%)")
    print(f"  {len(missing_cnns)} are MISSING blockface geometries ({len(missing_cnns)/len(streets)*100:.1f}%)")
    
    print("\nFor 20th Street specifically:")
    print(f"  {len(has_blockface_20th)} of {len(streets_20th)} segments have blockfaces")
    print(f"  Missing: {len(missing_20th)} segments")
    
    if target_cnn in missing_cnns:
        print(f"\n✗ CNN {target_cnn} (York-Bryant block) is MISSING blockface geometry")
        print("  This is why we can't show regulations for this specific block")
    
    print("\nNEXT STEP: Generate synthetic blockfaces from centerline geometries")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check())