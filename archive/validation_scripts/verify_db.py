import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

async def verify_data():
    """Connects to the database and verifies the street cleaning data."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    collection = db["street_cleaning_schedules"]
    count = await collection.count_documents({})

    if count > 0:
        print(f"Success: Found {count} documents in the 'street_cleaning_schedules' collection.")
    else:
        print("Error: 'street_cleaning_schedules' collection is empty or does not exist.")

    client.close()

if __name__ == "__main__":
    asyncio.run(verify_data())