from pymongo import MongoClient
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["parking_data"]

print("Available collections:")
print(db.list_collection_names())
print("\n" + "="*80 + "\n")

# Search for Balmy in parking_regulations collection
print("Searching for 'Balmy' in parking_regulations collection...")
balmy_regs = list(db.parking_regulations.find(
    {"$or": [
        {"street_name": {"$regex": "balmy", "$options": "i"}},
        {"cnn": 2699000}
    ]}
).limit(10))

print(f"Found {len(balmy_regs)} regulations mentioning Balmy or CNN 2699000")
for reg in balmy_regs:
    print(f"\nCNN: {reg.get('cnn')}")
    print(f"Street: {reg.get('street_name')}")
    print(f"Type: {reg.get('regulation_type')}")
    if reg.get('time_limit_minutes'):
        print(f"Time Limit: {reg.get('time_limit_minutes')} minutes")
    if reg.get('days_of_week'):
        print(f"Days: {reg.get('days_of_week')}")
    if reg.get('start_time') and reg.get('end_time'):
        print(f"Hours: {reg.get('start_time')} - {reg.get('end_time')}")
    print("-" * 40)

print("\n" + "="*80 + "\n")

# Search in streets collection
print("Searching for 'Balmy' in streets collection...")
balmy_streets = list(db.streets.find(
    {"$or": [
        {"street_name": {"$regex": "balmy", "$options": "i"}},
        {"cnn": 2699000}
    ]}
).limit(10))

print(f"Found {len(balmy_streets)} streets mentioning Balmy or CNN 2699000")
for street in balmy_streets:
    print(f"\nCNN: {street.get('cnn')}")
    print(f"Street: {street.get('street_name')}")
    print(f"From: {street.get('from_street')} to {street.get('to_street')}")
    print("-" * 40)

client.close()