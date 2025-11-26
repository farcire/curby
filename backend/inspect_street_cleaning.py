import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def inspect_street_cleaning():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI not set")
        return

    client = AsyncIOMotorClient(mongodb_uri)
    db = client.curby

    # 1. Get a sample Blockface
    print("\n--- Sample Blockface ---")
    blockface = await db.blockfaces.find_one({}, {"id": 1, "streetName": 1, "geometry": 1})
    if blockface:
        print(blockface)
    else:
        print("No blockfaces found.")

    # 2. Get a sample Street Cleaning Schedule
    print("\n--- Sample Street Cleaning Schedule ---")
    schedule = await db.street_cleaning_schedules.find_one({})
    if schedule:
        print(schedule)
    else:
        print("No street cleaning schedules found.")

    # 3. Check for common fields (e.g., CNN)
    if blockface and schedule:
        print("\n--- Field Comparison ---")
        print(f"Blockface Keys: {list(blockface.keys())}")
        print(f"Schedule Keys: {list(schedule.keys())}")

    client.close()

if __name__ == "__main__":
    asyncio.run(inspect_street_cleaning())