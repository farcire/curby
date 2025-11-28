import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

async def check_data():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.curby
    
    # Check if blockfaces collection exists and has data
    count = await db.blockfaces.count_documents({})
    print(f"Total documents in blockfaces collection: {count}")
    
    # Check if geometry index exists
    indexes = await db.blockfaces.index_information()
    print(f"\nIndexes on blockfaces collection:")
    for name, info in indexes.items():
        print(f"  - {name}: {info}")
    
    # Get a sample document
    sample = await db.blockfaces.find_one({})
    if sample:
        print(f"\nSample document fields:")
        for key in sample.keys():
            val = sample[key]
            print(f"  - {key}: {type(val).__name__}")
            if key in ['streetName', 'side', 'fromAddress', 'toAddress', 'cnn']:
                print(f"      Value: {val}")
    
    client.close()

asyncio.run(check_data())