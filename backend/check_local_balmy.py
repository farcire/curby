from pymongo import MongoClient
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["parking_data"]

print("=" * 80)
print("CHECKING LOCAL DATABASE FOR BALMY STREET")
print("=" * 80)

# Check what collections we have
print("\nAvailable collections:")
collections = db.list_collection_names()
for coll in collections:
    count = db[coll].count_documents({})
    print(f"  - {coll}: {count} documents")

print("\n" + "=" * 80)

# Search in parking_regulations collection
print("\nSearching parking_regulations for CNN 2699000 or 'BALMY'...")
print("-" * 80)

balmy_regs = list(db.parking_regulations.find({
    "$or": [
        {"cnn": 2699000},
        {"cnn": "2699000"},
        {"street_name": {"$regex": "balmy", "$options": "i"}}
    ]
}))

if balmy_regs:
    print(f"\nFound {len(balmy_regs)} regulation(s):\n")
    for reg in balmy_regs:
        print(json.dumps(reg, indent=2, default=str))
        print("\n" + "-" * 80 + "\n")
else:
    print("No regulations found in parking_regulations collection")

# Search in streets collection
print("\nSearching streets collection for CNN 2699000 or 'BALMY'...")
print("-" * 80)

balmy_streets = list(db.streets.find({
    "$or": [
        {"cnn": 2699000},
        {"cnn": "2699000"},
        {"street_name": {"$regex": "balmy", "$options": "i"}}
    ]
}))

if balmy_streets:
    print(f"\nFound {len(balmy_streets)} street(s):\n")
    for street in balmy_streets:
        print(json.dumps(street, indent=2, default=str))
        print("\n" + "-" * 80 + "\n")
else:
    print("No streets found in streets collection")

# Search in street_cleaning_schedules
print("\nSearching street_cleaning_schedules for CNN 2699000...")
print("-" * 80)

cleaning = list(db.street_cleaning_schedules.find({
    "$or": [
        {"cnn": 2699000},
        {"cnn": "2699000"}
    ]
}))

if cleaning:
    print(f"\nFound {len(cleaning)} cleaning schedule(s):\n")
    for sched in cleaning:
        print(json.dumps(sched, indent=2, default=str))
        print("\n" + "-" * 80 + "\n")
else:
    print("No cleaning schedules found")

print("\n" + "=" * 80)
print("LOCAL DATABASE SEARCH COMPLETE")
print("=" * 80)

client.close()