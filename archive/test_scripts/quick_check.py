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
    
    with open('test_results.txt', 'w') as f:
        f.write("=== DATABASE CHECK ===\n\n")
        
        # Count blockfaces
        total = await db.blockfaces.count_documents({})
        f.write(f"Total blockfaces: {total}\n\n")
        
        # Check for Mariposa
        mariposa_count = await db.blockfaces.count_documents({"streetName": {"$regex": "MARIPOSA", "$options": "i"}})
        f.write(f"Mariposa Street blockfaces: {mariposa_count}\n\n")
        
        if mariposa_count > 0:
            blockfaces = await db.blockfaces.find({"streetName": {"$regex": "MARIPOSA", "$options": "i"}}).to_list(None)
            f.write(f"Found {len(blockfaces)} Mariposa blockfaces:\n\n")
            
            for i, bf in enumerate(blockfaces, 1):
                f.write(f"--- Blockface {i} ---\n")
                f.write(f"ID: {bf.get('id')}\n")
                f.write(f"Street: {bf.get('streetName')}\n")
                f.write(f"CNN: {bf.get('cnn')}\n")
                f.write(f"Side: {bf.get('side')}\n")
                rules = bf.get('rules', [])
                f.write(f"Rules: {len(rules)} total\n")
                for rule in rules:
                    f.write(f"  - {rule.get('type')}\n")
                f.write("\n")
        else:
            f.write("No Mariposa Street found.\n\n")
            
            # Sample a few streets
            f.write("Sample streets in database:\n")
            sample = await db.blockfaces.find({}, {"streetName": 1}).limit(10).to_list(None)
            for s in sample:
                f.write(f"  - {s.get('streetName')}\n")
        
        # Check rule types
        f.write("\n=== RULE TYPES ===\n")
        pipeline = [
            {"$unwind": "$rules"},
            {"$group": {"_id": "$rules.type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        rules = await db.blockfaces.aggregate(pipeline).to_list(None)
        for r in rules:
            f.write(f"{r['_id']}: {r['count']}\n")
        
        if not any(r['_id'] == 'parking-regulation' for r in rules):
            f.write("\n❌ NO PARKING REGULATIONS FOUND!\n")
    
    client.close()
    print("Results written to test_results.txt")

asyncio.run(check())