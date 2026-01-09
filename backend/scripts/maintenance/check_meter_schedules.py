"""Check meter schedules to see if TOW/ALTERNATE schedules exist"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    
    # Check a few segments with meters
    segments = await db.street_segments.find({"meters": {"$exists": True, "$ne": []}}).limit(10).to_list(length=10)
    
    print(f"Found {len(segments)} segments with meters\n")
    
    for seg in segments[:3]:
        print(f"CNN: {seg.get('cnn')}, Side: {seg.get('side')}")
        print(f"  Street: {seg.get('streetName')}")
        print(f"  Meters: {len(seg.get('meters', []))}")
        
        for meter in seg.get('meters', [])[:2]:  # Check first 2 meters
            print(f"    Post ID: {meter.get('post_id')}")
            print(f"    Cap Color: {meter.get('cap_color')}")
            schedules = meter.get('schedules', [])
            print(f"    Schedules: {len(schedules)}")
            for sched in schedules:
                print(f"      - Type: {sched.get('schedule_type')}, Rate: {sched.get('rate')}")
        
        # Check aggregations
        tow_agg = seg.get('towScheduleAggregation', {})
        print(f"  TOW Aggregation: has_tow={tow_agg.get('has_tow')}, all_have_tow={tow_agg.get('all_have_tow')}")
        
        cap_agg = seg.get('capColorAggregation', {})
        print(f"  Cap Color Aggregation: eligible={cap_agg.get('eligible_for_curby_user')}")
        print()
    
    # Check raw meter_schedules collection
    print("\n=== Checking raw meter_schedules collection ===")
    
    # Count by schedule_type
    pipeline = [
        {"$group": {"_id": "$schedule_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    # Check if collection exists
    collections = await db.list_collection_names()
    if "meter_schedules" in collections:
        print("meter_schedules collection exists")
        total = await db.meter_schedules.count_documents({})
        print(f"Total meter schedules: {total}")
        
        # Sample a few
        samples = await db.meter_schedules.find().limit(5).to_list(length=5)
        print("\nSample schedules:")
        for s in samples:
            print(f"  Post ID: {s.get('post_id')}, Type: {s.get('schedule_type')}, Rate: {s.get('rate')}")
    else:
        print("meter_schedules collection does NOT exist")
        print(f"Available collections: {collections}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())