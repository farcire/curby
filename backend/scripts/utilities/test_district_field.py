#!/usr/bin/env python3
"""Quick test to check supervisor_district field"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
try:
    db = client.get_default_database()
except:
    db = client['curby']

# Get one segment
sample = db.street_segments.find_one({})
print("Sample segment fields with 'district' or 'supervisor':")
for key in sorted(sample.keys()):
    if 'district' in key.lower() or 'supervisor' in key.lower():
        print(f"  {key}: {sample.get(key)}")

print(f"\nHas 'supervisor_district': {'supervisor_district' in sample}")

# Count
total = db.street_segments.count_documents({})
with_field = db.street_segments.count_documents({'supervisor_district': {'$exists': True}})
print(f"\nTotal segments: {total}")
print(f"With supervisor_district: {with_field}")