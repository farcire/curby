"""
Debug script to check if meters are being added to segments during ingestion
but not persisting to the database.
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client['curby']

# Check database state
print("=== Database State ===")
total_segments = db.street_segments.count_documents({})
print(f"Total segments in DB: {total_segments}")

# Check if any segment has meters field
segments_with_meters_field = db.street_segments.count_documents({'meters': {'$exists': True}})
print(f"Segments with 'meters' field: {segments_with_meters_field}")

# Check if any segment has non-empty meters
segments_with_meters_data = db.street_segments.count_documents({'meters': {'$exists': True, '$ne': []}})
print(f"Segments with non-empty 'meters': {segments_with_meters_data}")

# Sample a few segments to see structure
print("\n=== Sample Segment Structure ===")
sample = db.street_segments.find_one({})
if sample:
    print(f"Fields in segment: {list(sample.keys())}")
    print(f"Has 'meters' field: {'meters' in sample}")
    print(f"Has 'schedules' field: {'schedules' in sample}")
    
    # Check if any segment has schedules (old field name?)
    segments_with_schedules = db.street_segments.count_documents({'schedules': {'$exists': True, '$ne': []}})
    print(f"\nSegments with 'schedules' field: {segments_with_schedules}")

# Check if meters were matched during ingestion
print("\n=== Checking Meter Datasets ===")
meters_count = db.parking_meters.count_documents({}) if 'parking_meters' in db.list_collection_names() else 0
print(f"Meters in parking_meters collection: {meters_count}")

print("\n=== Diagnosis ===")
if segments_with_meters_field == 0:
    print("❌ PROBLEM: No segments have 'meters' field at all!")
    print("   This means meters are being matched but not saved to segments.")
    print("   The meter matching code (lines 760-781) adds meters to segments,")
    print("   but they're not persisting to the database.")
elif segments_with_meters_data == 0:
    print("⚠️  PROBLEM: Segments have 'meters' field but all are empty!")
    print("   Meters are being initialized but not populated.")
else:
    print(f"✓ SUCCESS: {segments_with_meters_data} segments have meter data!")

client.close()