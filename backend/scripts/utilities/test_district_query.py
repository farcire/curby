#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['curby']

print("Testing district query...")

# Test the exact query from investigation script
pipeline = [
    {
        "$match": {
            "supervisor_district": {"$exists": True}
        }
    },
    {
        "$project": {
            "cnn": 1,
            "side": 1,
            "streetName": 1,
            "supervisor_district": 1,
            "centerlineGeometry": 1,
            "blockfaceGeometry": 1
        }
    }
]

result = list(db.street_segments.aggregate(pipeline))
print(f"Query returned: {len(result)} segments")

if result:
    print(f"\nFirst result:")
    first = result[0]
    print(f"  CNN: {first.get('cnn')}")
    print(f"  Side: {first.get('side')}")
    print(f"  District: {first.get('supervisor_district')}")