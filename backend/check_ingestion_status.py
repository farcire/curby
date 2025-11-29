#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

async def check_db():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    # Check what collections exist and their counts
    collections = await db.list_collection_names()
    print('Current database collections:')
    for coll in collections:
        count = await db[coll].count_documents({})
        print(f'  {coll}: {count:,} documents')
    
    # Check if street_segments exists (the new collection)
    if 'street_segments' in collections:
        count = await db.street_segments.count_documents({})
        print(f'\n✓ NEW street_segments collection found with {count:,} segments')
        
        # Sample a few
        sample = await db.street_segments.find_one({})
        if sample:
            print(f'\nSample segment:')
            print(f'  CNN: {sample.get("cnn")}')
            print(f'  Side: {sample.get("side")}')
            print(f'  Street: {sample.get("streetName")}')
            print(f'  Rules: {len(sample.get("rules", []))}')
            print(f'  Schedules: {len(sample.get("schedules", []))}')
            
        # Count segments with data
        with_sweeping = 0
        with_parking = 0
        with_meters = 0
        async for seg in db.street_segments.find({}):
            if any(r.get("type") == "street-sweeping" for r in seg.get("rules", [])):
                with_sweeping += 1
            if any(r.get("type") == "parking-regulation" for r in seg.get("rules", [])):
                with_parking += 1
            if seg.get("schedules"):
                with_meters += 1
        
        print(f'\nSegment enrichment:')
        print(f'  With street sweeping: {with_sweeping:,}')
        print(f'  With parking regulations: {with_parking:,}')
        print(f'  With meters: {with_meters:,}')
    else:
        print('\n⚠️  street_segments collection not yet created - ingestion still in progress')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_db())