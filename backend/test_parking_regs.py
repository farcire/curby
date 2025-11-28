import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def test():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    # Find all blockfaces with parking regulations
    blockfaces = await db.blockfaces.find({
        "rules.type": "parking-regulation"
    }).to_list(None)
    
    print(f"\n=== BLOCKFACES WITH PARKING REGULATIONS ===")
    print(f"Total: {len(blockfaces)} blockfaces have parking regulations\n")
    
    # Group by street
    streets = {}
    for bf in blockfaces:
        street = bf.get('streetName', 'Unknown')
        if street not in streets:
            streets[street] = []
        streets[street].append(bf)
    
    print(f"Streets with parking regulations: {len(streets)}\n")
    
    for street_name in sorted(streets.keys()):
        bfs = streets[street_name]
        print(f"\n{street_name}: {len(bfs)} blockfaces")
        for bf in bfs[:3]:  # Show first 3 blockfaces per street
            rules = bf.get('rules', [])
            regs = [r for r in rules if r.get('type') == 'parking-regulation']
            print(f"  Side {bf.get('side')}: {len(regs)} parking regulations")
            for reg in regs[:1]:  # Show first regulation
                desc = reg.get('description', 'No description')
                if desc and len(desc) > 80:
                    desc = desc[:80] + "..."
                print(f"    - {desc}")
    
    # Check for 20th street specifically
    print("\n\n=== 20TH STREET CHECK ===")
    street_20th = await db.blockfaces.find({
        "streetName": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    if street_20th:
        print(f"Found {len(street_20th)} blockfaces on 20th Street:")
        for bf in street_20th:
            rules = bf.get('rules', [])
            regs = [r for r in rules if r.get('type') == 'parking-regulation']
            print(f"  CNN {bf.get('cnn')}, Side {bf.get('side')}: {len(regs)} parking regs, {len(rules)} total rules")
    else:
        print("No 20th Street blockfaces found in database")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test())