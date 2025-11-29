import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

async def verify_ingestion():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI not set")
        return

    client = AsyncIOMotorClient(mongodb_uri)
    db = client.curby

    print("\n--- Database Collection Counts ---")
    collections = [
        "streets", "street_nodes", "intersections", "intersection_permutations",
        "street_cleaning_schedules", "parking_regulations", "blockfaces"
    ]
    
    for col_name in collections:
        count = await db[col_name].count_documents({})
        print(f"{col_name}: {count}")

    print("\n--- Inspecting a Sample Blockface ---")
    # Find a blockface that likely has both rules (sweeping) and schedules (meters)
    # We'll search for one with non-empty rules array
    sample = await db.blockfaces.find_one({"rules": {"$ne": []}})
    
    if sample:
        print(f"Blockface ID (CNN): {sample.get('id')}")
        print(f"Street: {sample.get('streetName')}")
        
        print("\nRules (Street Cleaning):")
        for rule in sample.get('rules', [])[:3]: # Show max 3
            print(f"  - {rule}")
            
        print("\nSchedules (Meters):")
        for sched in sample.get('schedules', [])[:3]: # Show max 3
            print(f"  - {sched}")
            
        print("\nGeometry (First Point):")
        geo = sample.get('geometry')
        if geo and 'coordinates' in geo:
            print(f"  - {geo['coordinates'][0]}")
    else:
        print("No blockfaces found with rules populated.")

    client.close()

if __name__ == "__main__":
    asyncio.run(verify_ingestion())