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
    
    blockfaces = await db.blockfaces.find({
        "streetName": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    print(f"\n20th Street Blockfaces: {len(blockfaces)}\n")
    for bf in blockfaces:
        rules = bf.get('rules', [])
        regs = [r for r in rules if r.get('type') == 'parking-regulation']
        sweeps = [r for r in rules if r.get('type') == 'street-sweeping']
        print(f"{bf.get('streetName')} (CNN: {bf.get('cnn')}) Side {bf.get('side')}")
        print(f"  Total rules: {len(rules)}")
        print(f"  Parking regulations: {len(regs)}")
        print(f"  Street sweeping: {len(sweeps)}")
        if regs:
            print("  ✅ HAS PARKING REGULATIONS!")
            for reg in regs[:2]:  # Show first 2
                print(f"    - {reg.get('description', 'No description')[:100]}")
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test())