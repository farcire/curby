#!/usr/bin/env python3
"""
Check how many segments in MongoDB don't have a streetName field.
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

async def main():
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    print("Checking segments in MongoDB...")
    
    # Count total segments
    total = await db.street_segments.count_documents({})
    print(f"Total segments: {total}")
    
    # Count segments without streetName
    no_streetname = await db.street_segments.count_documents({"streetName": None})
    print(f"Segments with streetName = None: {no_streetname}")
    
    # Count segments where streetName doesn't exist
    no_field = await db.street_segments.count_documents({"streetName": {"$exists": False}})
    print(f"Segments without streetName field: {no_field}")
    
    # Count segments with empty string
    empty_string = await db.street_segments.count_documents({"streetName": ""})
    print(f"Segments with streetName = '': {empty_string}")
    
    # Get detailed list of all segments without streetName
    print("\n" + "="*70)
    print("DETAILED LIST OF SEGMENTS WITHOUT STREETNAME")
    print("="*70)
    
    cursor = db.street_segments.find({"streetName": None})
    segments_without_name = []
    async for seg in cursor:
        segments_without_name.append(seg)
    
    if segments_without_name:
        print(f"\nFound {len(segments_without_name)} segments without streetName:\n")
        for i, seg in enumerate(segments_without_name, 1):
            print(f"{i}. CNN: {seg.get('cnn')}")
            print(f"   Side: {seg.get('side')}")
            print(f"   From Address: {seg.get('fromAddress')}")
            print(f"   To Address: {seg.get('toAddress')}")
            print(f"   Supervisor District: {seg.get('supervisor_district')}")
            print(f"   Zip Code: {seg.get('zip_code')}")
            print(f"   Has Rules: {len(seg.get('rules', []))}")
            print(f"   Has Meters: {len(seg.get('meters', []))}")
            print()
    else:
        print("\n✓ All segments have streetName!")
    
    # Save to file for investigation
    if segments_without_name:
        import json
        output_file = "segments_without_streetname.json"
        with open(output_file, 'w') as f:
            # Convert ObjectId to string for JSON serialization
            for seg in segments_without_name:
                if '_id' in seg:
                    seg['_id'] = str(seg['_id'])
            json.dump(segments_without_name, f, indent=2, default=str)
        print(f"✓ Saved detailed data to {output_file}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())