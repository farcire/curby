import sys
print("Script start", flush=True)
import asyncio
import os
import motor.motor_asyncio
from dotenv import load_dotenv

print("Imports done", flush=True)

load_dotenv()

async def main():
    print("Async main start", flush=True)
    uri = os.getenv("MONGODB_URI")
    print(f"URI found: {bool(uri)}", flush=True)
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    db = client.curby
    print("Connected to DB", flush=True)
    
    count = await db.street_cleaning_schedules.count_documents({})
    print(f"Count: {count}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())