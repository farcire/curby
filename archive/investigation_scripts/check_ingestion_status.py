#!/usr/bin/env python3
"""
Quick script to check the status of data ingestion in MongoDB.
Run this while ingestion is in progress to see how much data has been loaded.
"""
import os
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

async def check_status():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in .env file")
        return
    
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    print("=" * 80)
    print("MONGODB INGESTION STATUS")
    print("=" * 80)
    
    collections = [
        "streets",
        "street_segments",
        "street_cleaning_schedules",
        "parking_regulations",
        "street_nodes",
        "intersections",
        "intersection_permutations"
    ]
    
    for collection_name in collections:
        try:
            count = await db[collection_name].count_documents({})
            print(f"{collection_name:30s}: {count:>10,} documents")
        except Exception as e:
            print(f"{collection_name:30s}: Error - {e}")
    
    # Get sample street segment to show structure
    print("\n" + "=" * 80)
    print("SAMPLE STREET SEGMENT")
    print("=" * 80)
    
    sample = await db.street_segments.find_one({})
    if sample:
        print(f"CNN: {sample.get('cnn')}")
        print(f"Street: {sample.get('streetName')}")
        print(f"Side: {sample.get('side')}")
        print(f"Zip: {sample.get('zip_code')}")
        print(f"Rules: {len(sample.get('rules', []))}")
        print(f"Schedules: {len(sample.get('schedules', []))}")
    else:
        print("No segments found yet...")
    
    client.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(check_status())