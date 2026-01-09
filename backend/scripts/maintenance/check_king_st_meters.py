"""
Check for parking meters on KING ST CNNs 7834201 and 7834101
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def check_meters():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    # Get all collections
    collections = await db.list_collection_names()
    meter_collections = [c for c in collections if 'meter' in c.lower() or 'parking' in c.lower()]
    
    print("Collections with meter/parking in name:")
    for coll in meter_collections:
        count = await db[coll].count_documents({})
        print(f"  {coll}: {count} documents")
    
    print()
    
    # Check for meters on these CNNs
    cnns = ['7834201', '7834101']
    
    for cnn in cnns:
        print(f"=" * 80)
        print(f"Checking meters for CNN {cnn}")
        print("=" * 80)
        
        # Check parking_regulations collection
        if 'parking_regulations' in collections:
            cursor = db.parking_regulations.find({'cnn': cnn})
            regs = await cursor.to_list(length=None)
            if regs:
                print(f"\nFound {len(regs)} in parking_regulations:")
                for reg in regs:
                    print(json.dumps(reg, indent=2, default=str))
        
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_meters())