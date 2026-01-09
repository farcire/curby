"""
Check what meter schedule data was actually ingested into MongoDB
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from pprint import pprint

load_dotenv()

async def check_meters():
    mongodb_uri = os.getenv("MONGODB_URI")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    
    # Check meter schedules collection
    print("=" * 80)
    print("METER SCHEDULES COLLECTION")
    print("=" * 80)
    
    count = await db.meter_schedules.count_documents({})
    print(f"\nTotal meter schedule records: {count}")
    
    if count > 0:
        # Get a sample record
        sample = await db.meter_schedules.find_one({})
        print("\nSample meter schedule record:")
        print("-" * 80)
        pprint(sample)
        
        # Get all unique field names
        print("\n" + "=" * 80)
        print("All fields in meter_schedules collection:")
        print("=" * 80)
        pipeline = [
            {"$limit": 100},
            {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
            {"$unwind": "$arrayofkeyvalue"},
            {"$group": {"_id": None, "allkeys": {"$addToSet": "$arrayofkeyvalue.k"}}}
        ]
        result = await db.meter_schedules.aggregate(pipeline).to_list(1)
        if result:
            fields = sorted(result[0]['allkeys'])
            for field in fields:
                print(f"  - {field}")
        
        # Check for specific post_id with multiple schedules
        print("\n" + "=" * 80)
        print("Checking post_id with multiple schedules:")
        print("=" * 80)
        pipeline = [
            {"$group": {"_id": "$post_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        result = await db.meter_schedules.aggregate(pipeline).to_list(1)
        if result:
            post_id = result[0]['_id']
            count = result[0]['count']
            print(f"\nPost ID {post_id} has {count} schedules:")
            schedules = await db.meter_schedules.find({"post_id": post_id}).to_list(None)
            for i, sched in enumerate(schedules, 1):
                print(f"\n  Schedule {i}:")
                for key in sorted(sched.keys()):
                    if key != '_id':
                        print(f"    {key}: {sched[key]}")
    
    # Check street_segments collection
    print("\n" + "=" * 80)
    print("STREET SEGMENTS WITH METERS")
    print("=" * 80)
    
    segment_count = await db.street_segments.count_documents({"meters": {"$exists": True, "$ne": []}})
    print(f"\nSegments with meters: {segment_count}")
    
    if segment_count > 0:
        # Get a segment with meters
        segment = await db.street_segments.find_one({"meters": {"$exists": True, "$ne": []}})
        print("\nSample segment with meters:")
        print("-" * 80)
        print(f"CNN: {segment.get('cnn')}")
        print(f"Side: {segment.get('side')}")
        print(f"Street: {segment.get('streetName')}")
        print(f"Number of meters: {len(segment.get('meters', []))}")
        
        if segment.get('meters'):
            meter = segment['meters'][0]
            print(f"\nFirst meter:")
            print(f"  post_id: {meter.get('post_id')}")
            print(f"  cap_color: {meter.get('cap_color')}")
            print(f"  Number of schedules: {len(meter.get('schedules', []))}")
            
            if meter.get('schedules'):
                print(f"\n  Schedules:")
                for i, sched in enumerate(meter['schedules'], 1):
                    print(f"\n    Schedule {i}:")
                    for key in sorted(sched.keys()):
                        print(f"      {key}: {sched[key]}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_meters())