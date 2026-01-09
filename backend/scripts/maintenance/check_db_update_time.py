"""
Check when the street_segments collection was last updated
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from datetime import datetime

async def check_update_time():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in .env file")
        return
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    # Check collection stats
    stats = await db.command("collStats", "street_segments")
    
    print(f"\n=== Street Segments Collection Stats ===")
    print(f"Total documents: {stats.get('count', 'N/A')}")
    print(f"Size: {stats.get('size', 'N/A')} bytes")
    
    # Get a sample document to check if it has updated fields
    sample = await db.street_segments.find_one({}, sort=[("_id", -1)])
    
    if sample:
        print(f"\n=== Sample Document (most recent) ===")
        print(f"CNN: {sample.get('cnn')}")
        print(f"Side: {sample.get('side')}")
        print(f"Street: {sample.get('streetName')}")
        print(f"Has blockfaceGeometry: {bool(sample.get('blockfaceGeometry'))}")
        print(f"Cardinal Direction: {sample.get('cardinalDirection')}")
        print(f"Display Name: {sample.get('displayName')}")
    
    # Count segments with blockface geometry
    with_blockface = await db.street_segments.count_documents({"blockfaceGeometry": {"$ne": None}})
    print(f"\n=== Geometry Stats ===")
    print(f"Segments with blockface geometry: {with_blockface}")
    
    client.close()
    print("\n✓ Database check complete")

if __name__ == "__main__":
    asyncio.run(check_update_time())