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

    # Search for Mariposa
    print("\nSearching for 'Mariposa' in blockfaces...")
    try:
        query = {"streetName": {"$regex": "Mariposa", "$options": "i"}}
        count = await db.blockfaces.count_documents(query)
        print(f"Found {count} documents matching 'Mariposa'")
        
        async for doc in db.blockfaces.find(query).limit(5):
            if "_id" in doc: del doc["_id"]
            print("\n----------------")
            print(f"CNN: {doc.get('cnn')}")
            print(f"Street: {doc.get('streetName')}")
            print(f"Side: {doc.get('side')}") # Check if we have side info
            print(f"Geometry Type: {doc.get('geometry', {}).get('type')}")
            
    except Exception as e:
        print(f"Query Error: {e}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())