import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from sodapy import Socrata

async def debug():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    # 1. Inspect Raw Data from Socrata
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print("\n--- Raw Street Cleaning Data (Source: yhqp-riqs) ---")
    # Dataset: Street Cleaning Schedules (yhqp-riqs)
    # querying for CNN 1046000
    try:
        results = client.get("yhqp-riqs", where="cnn='1046000'")
        print(f"Found {len(results)} records in Socrata for CNN 1046000:")
        for r in results:
            print(f"  - Side: {r.get('cnnrightleft')}, Day: {r.get('weekday')}, Time: {r.get('fromhour')}-{r.get('tohour')}")
    except Exception as e:
        print(f"Error fetching from Socrata: {e}")

    # 2. Connect to MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI not found")
        return

    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = mongo_client.get_default_database()
    except Exception:
        db = mongo_client["curby"]
    
    target_cnn = "1046000"
    print(f"\n--- Database Inspection CNN {target_cnn} ---")
    
    # Check street_cleaning_schedules collection
    raw_docs = await db.street_cleaning_schedules.find({"cnn": target_cnn}).to_list(length=100)
    print(f"Found {len(raw_docs)} docs in 'street_cleaning_schedules' collection:")
    for doc in raw_docs:
        print(f"  - Side: {doc.get('cnnrightleft')}, Day: {doc.get('weekday')}, Time: {doc.get('fromhour')}-{doc.get('tohour')}")

    # Check segments again briefly
    segments = await db.street_segments.find({"cnn": target_cnn}).to_list(length=100)
    print(f"\n--- Segments for CNN {target_cnn} ---")
    for seg in segments:
        print(f"Segment Side: {seg.get('side')}")
        rules = seg.get('rules', [])
        sweeping_rules = [r for r in rules if r.get('type') == 'street-sweeping']
        if sweeping_rules:
            for rule in sweeping_rules:
                print(f"  - Rule: {rule.get('description')}")
        else:
            print("  - No street sweeping rules found.")

    mongo_client.close()

if __name__ == "__main__":
    asyncio.run(debug())