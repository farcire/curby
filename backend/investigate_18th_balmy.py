#!/usr/bin/env python3
"""
Investigate why Balmy Street and 18th Street aren't showing expected results
"""

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

async def check_data():
    # Use hardcoded URI for now
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.curby
    
    print("=" * 80)
    print("DATABASE INVESTIGATION - 18th Street & Balmy Street")
    print("=" * 80)
    print("Connected successfully!")
    
    # Check collection counts
    print("\nCounting documents in collections...")
    blockfaces_count = await db.blockfaces.count_documents({})
    print(f"  blockfaces counted: {blockfaces_count}")
    street_segments_count = await db.street_segments.count_documents({})
    print(f"  street_segments counted: {street_segments_count}")
    
    print(f"\nCollection counts:")
    print(f"  blockfaces: {blockfaces_count}")
    print(f"  street_segments: {street_segments_count}")
    
    # Check for Balmy Street in both collections
    print(f"\n--- Balmy Street Search ---")
    balmy_blockfaces = await db.blockfaces.count_documents({"streetName": {"$regex": "BALMY", "$options": "i"}})
    balmy_segments = await db.street_segments.count_documents({"streetName": {"$regex": "BALMY", "$options": "i"}})
    
    print(f"  In blockfaces: {balmy_blockfaces}")
    print(f"  In street_segments: {balmy_segments}")
    
    if balmy_segments > 0:
        print(f"\n  Sample Balmy Street records:")
        cursor = db.street_segments.find({"streetName": {"$regex": "BALMY", "$options": "i"}}).limit(5)
        async for doc in cursor:
            print(f"    CNN: {doc.get('cnn')}, Side: {doc.get('side')}")
            geom = doc.get('centerlineGeometry')
            if geom and 'coordinates' in geom:
                coords = geom['coordinates']
                if coords:
                    print(f"      First coord: {coords[0]}")
    
    # Check for 18th Street
    print(f"\n--- 18th Street Search ---")
    eighteenth_blockfaces = await db.blockfaces.count_documents({"streetName": {"$regex": "18TH", "$options": "i"}})
    eighteenth_segments = await db.street_segments.count_documents({"streetName": {"$regex": "18TH", "$options": "i"}})
    
    print(f"  In blockfaces: {eighteenth_blockfaces}")
    print(f"  In street_segments: {eighteenth_segments}")
    
    # Sample a few 18th Street records
    print(f"\n  Sample 18th Street records from street_segments:")
    cursor = db.street_segments.find({"streetName": {"$regex": "18TH", "$options": "i"}}).limit(5)
    async for doc in cursor:
        print(f"    CNN: {doc.get('cnn')}, Side: {doc.get('side')}, From: {doc.get('fromStreet')}, To: {doc.get('toStreet')}")
        # Check if it has geometry
        has_centerline = "centerlineGeometry" in doc
        has_blockface = "blockfaceGeometry" in doc
        print(f"      Has centerlineGeometry: {has_centerline}, Has blockfaceGeometry: {has_blockface}")
        
        # Check geometry structure
        if has_centerline:
            geom = doc.get('centerlineGeometry')
            if geom:
                print(f"      Geometry type: {geom.get('type')}")
                if 'coordinates' in geom and geom['coordinates']:
                    print(f"      First coord: {geom['coordinates'][0]}")
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    client.close()

if __name__ == "__main__":
    print("Starting investigation script...")
    asyncio.run(check_data())
    print("Script finished.")