import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from models import Blockface

load_dotenv()

async def main():
    uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(uri)
    db = client.curby
    
    print("Creating index...")
    await db.blockfaces.create_index([("geometry", "2dsphere")])
    print("Index created.")

    print("Checking indexes...")
    indexes = await db.blockfaces.index_information()
    print(indexes)
    
    print("\nFetching one document...")
    doc = await db.blockfaces.find_one()
    if doc:
        print("Raw document keys:", doc.keys())
        if "_id" in doc:
            del doc["_id"]
        
        try:
            bf = Blockface(**doc)
            print("Successfully validated with Pydantic model.")
            print(bf)
        except Exception as e:
            print(f"Pydantic Validation Error: {e}")
            print("Doc content:", doc)
    else:
        print("No documents found in 'blockfaces'.")

    # Test the query
    print("\nTesting geospatial query ($geoWithin)...")
    try:
        # Radius in radians = radius_meters / earth_radius_meters
        radius_radians = 500 / 6378100
        
        query = {
            "geometry": {
                "$geoWithin": {
                    "$centerSphere": [[-122.41, 37.76], radius_radians]
                }
            }
        }
        count = await db.blockfaces.count_documents(query)
        print(f"Found {count} documents within 500m of -122.41, 37.76")
        
        print("\nFetching sample documents...")
        async for doc in db.blockfaces.find(query).limit(2):
            if "_id" in doc: del doc["_id"]
            print(f"Found blockface: {doc.get('streetName', 'Unknown')}")
            
    except Exception as e:
        print(f"Query Error: {e}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())