"""
Get ALL fields for CNN 868000, Side R (18th St North 2700-2798)
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json
from pprint import pprint

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def get_all_fields():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 100)
    print("ALL FIELDS FOR CNN 868000, SIDE R (18TH STREET NORTH 2700-2798)")
    print("=" * 100)
    print()
    
    # Query for the specific segment
    doc = await db.street_segments.find_one({
        "cnn": "868000",
        "side": "R"
    })
    
    if not doc:
        print("ERROR: Segment not found!")
        client.close()
        return
    
    # Convert ObjectId to string for JSON serialization
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    
    # Print all top-level fields
    print("TOP-LEVEL FIELDS:")
    print("-" * 100)
    for key in sorted(doc.keys()):
        value = doc[key]
        value_type = type(value).__name__
        
        # Show preview of value
        if isinstance(value, (list, dict)):
            if isinstance(value, list):
                preview = f"[{len(value)} items]"
            else:
                preview = f"{{{len(value)} keys}}"
        else:
            preview = str(value)[:100]
        
        print(f"{key:30} ({value_type:15}): {preview}")
    
    print()
    print()
    
    # Print complete document in JSON format
    print("=" * 100)
    print("COMPLETE DOCUMENT (JSON FORMAT)")
    print("=" * 100)
    print()
    print(json.dumps(doc, indent=2, default=str))
    print()
    
    # Save to file
    with open("backend/cnn_868000_all_fields.json", "w") as f:
        json.dump(doc, f, indent=2, default=str)
    
    print()
    print("=" * 100)
    print(f"Complete data saved to: backend/cnn_868000_all_fields.json")
    print("=" * 100)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(get_all_fields())