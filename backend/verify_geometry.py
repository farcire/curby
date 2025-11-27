import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def verify_geometry():
    """Connects to the database and verifies the blockface geometry."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    collection = db["blockfaces"]
    
    # Check total count
    count = await collection.count_documents({})
    print(f"Total blockfaces: {count}")

    if count == 0:
        print("Error: 'blockfaces' collection is empty.")
        client.close()
        return

    # Check for LineString geometry
    sample = await collection.find_one({"geometry.type": "LineString"})
    
    if sample:
        print("\nSuccess: Found blockface with LineString geometry.")
        print("Sample geometry:")
        print(json.dumps(sample.get('geometry'), indent=2))
        
        # Check coordinate structure
        coords = sample.get('geometry', {}).get('coordinates', [])
        if len(coords) > 2:
            print(f"\nVerified: Geometry has {len(coords)} points, indicating detailed curvature (not just start/end).")
        else:
            print(f"\nWarning: Sample geometry has only {len(coords)} points. This might be a straight line.")
            
    else:
        print("\nError: No blockfaces found with LineString geometry.")

    client.close()

if __name__ == "__main__":
    asyncio.run(verify_geometry())