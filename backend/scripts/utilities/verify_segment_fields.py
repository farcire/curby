#!/usr/bin/env python3
"""
Quick verification of street_segments field population
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

# Get total count
total = db.street_segments.count_documents({})
print(f"\n{'='*60}")
print(f"STREET SEGMENTS FIELD VERIFICATION")
print(f"{'='*60}")
print(f"\nTotal segments: {total:,}\n")

# Check key fields
fields_to_check = [
    'fromStreet',
    'toStreet',
    'cardinalDirection',
    'analysis_neighborhood',
    'streetCleaningAggregation',
    'nonMeteredRegulationAggregation',
    'schedules',
    'rules',
    'meters'
]

print("Field Population Status:")
print("-" * 60)

for field in fields_to_check:
    # Count non-null, non-empty values
    if field in ['rules', 'schedules', 'meters']:
        # For arrays, check if not empty
        count = db.street_segments.count_documents({field: {"$exists": True, "$ne": []}})
    else:
        # For other fields, check if exists and not null
        count = db.street_segments.count_documents({field: {"$exists": True, "$ne": None}})
    
    percentage = (count / total * 100) if total > 0 else 0
    status = "✓" if percentage > 50 else "⚠" if percentage > 0 else "✗"
    print(f"{status} {field:35s}: {count:6,} / {total:,} ({percentage:5.1f}%)")

# Sample a document to show structure
print(f"\n{'='*60}")
print("Sample Document Structure:")
print(f"{'='*60}\n")

sample = db.street_segments.find_one({})
if sample:
    for key in sorted(sample.keys()):
        value = sample.get(key)
        if isinstance(value, list):
            print(f"  {key:35s}: [{len(value)} items]")
        elif isinstance(value, dict):
            print(f"  {key:35s}: {{dict with {len(value)} keys}}")
        elif value is None:
            print(f"  {key:35s}: None")
        else:
            val_str = str(value)[:50]
            print(f"  {key:35s}: {val_str}")

print(f"\n{'='*60}\n")
client.close()