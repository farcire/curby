import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import pprint
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

async def check_york():
    print("Script started.", flush=True)
    uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(uri)
    db = client.curby
    
    print("Checking York St (CNN 13766000)...", flush=True)
    
    # Check raw schedule in DB
    print("\n--- Raw Schedule in DB ---", flush=True)
    schedule = await db.street_cleaning_schedules.find_one({"cnn": "13766000", "cnnrightleft": "L"})
    if schedule:
        print(f"Blockside in DB: '{schedule.get('blockside')}'", flush=True)
        # pprint.pprint(schedule)
    else:
        print("No schedule found in DB for CNN 13766000 L", flush=True)

    # Check segment 13766000 (Left side)
    doc = await db.street_segments.find_one({"cnn": "13766000", "side": "L"})
    
    if doc:
        print("\n--- Segment Found (L) ---", flush=True)
        print(f"Cardinal Direction: {doc.get('cardinalDirection')}")
        
        rules = doc.get('rules', [])
        for rule in rules:
            if rule.get('type') == 'street-sweeping':
                print(f"  - Sweeping Rule: blockside='{rule.get('blockside')}'")
    else:
        print("Segment 13766000 (L) not found.", flush=True)
        
    client.close()

if __name__ == "__main__":
    asyncio.run(check_york())