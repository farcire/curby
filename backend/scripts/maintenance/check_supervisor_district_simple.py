#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['curby']

# Direct count
total = db.street_segments.count_documents({})
print(f"Total segments: {total}")

# Count with field
with_field = db.street_segments.count_documents({'supervisor_district': {'$exists': True}})
print(f"With supervisor_district field: {with_field}")

# Get one example
example = db.street_segments.find_one({'supervisor_district': {'$exists': True}})
if example:
    print(f"\nExample found:")
    print(f"  CNN: {example.get('cnn')}")
    print(f"  Side: {example.get('side')}")
    print(f"  District: {example.get('supervisor_district')}")
else:
    print("\nNo example found with supervisor_district field")
    
# Check first document
first = db.street_segments.find_one({})
print(f"\nFirst document has supervisor_district: {'supervisor_district' in first}")
if 'supervisor_district' in first:
    print(f"  Value: {first['supervisor_district']}")