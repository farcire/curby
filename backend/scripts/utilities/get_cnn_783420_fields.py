"""
Get meter, regulation and street sweeping fields for CNN 783420 (KING ST)
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def get_cnn_fields():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 100)
    print("CNN 783420 - METER, REGULATION & STREET SWEEPING FIELDS")
    print("=" * 100)
    print()
    
    # Find all sides for this CNN
    cursor = db.street_segments.find({"cnn": "783420"})
    segments = await cursor.to_list(length=None)
    
    if not segments:
        print("ERROR: CNN 783420 not found!")
        client.close()
        return
    
    print(f"Found {len(segments)} segment(s) for CNN 783420")
    print()
    
    # Process each segment (usually L and R sides)
    for idx, doc in enumerate(segments, 1):
        # Convert ObjectId to string for JSON serialization
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        print("=" * 100)
        print(f"SEGMENT {idx}: CNN {doc.get('cnn')}, SIDE {doc.get('side')}")
        print(f"Display Name: {doc.get('displayName')}")
        print(f"Address Range: {doc.get('displayAddressRange')}")
        print(f"Cardinal: {doc.get('displayCardinal', 'N/A')}")
        print(f"From Street: {doc.get('fromStreet', 'N/A')}")
        print(f"To Street: {doc.get('toStreet', 'N/A')}")
        print("=" * 100)
        print()
        
        # Get all field names
        all_fields = list(doc.keys())
        
        # Define field categories
        meter_fields = [k for k in all_fields if 'meter' in k.lower()]
        regulation_fields = [k for k in all_fields if 'regulation' in k.lower() or 'parking' in k.lower() or 'rule' in k.lower()]
        sweeping_fields = [k for k in all_fields if 'sweep' in k.lower() or 'clean' in k.lower() or 'schedule' in k.lower()]
        
        # Print METER fields
        print("METER FIELDS:")
        print("-" * 100)
        if meter_fields:
            for key in sorted(meter_fields):
                value = doc[key]
                value_type = type(value).__name__
                
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        print(f"{key:40} ({value_type:15}): [{len(value)} items]")
                        for i, item in enumerate(value):
                            print(f"{'':40}   Item {i+1}:")
                            print(json.dumps(item, indent=6, default=str))
                    else:
                        print(f"{key:40} ({value_type:15}): {{{len(value)} keys}}")
                        print(json.dumps(value, indent=6, default=str))
                else:
                    print(f"{key:40} ({value_type:15}): {value}")
        else:
            print("  No meter fields found")
        print()
        
        # Print REGULATION/PARKING/RULES fields
        print("REGULATION/PARKING/RULES FIELDS:")
        print("-" * 100)
        if regulation_fields:
            for key in sorted(regulation_fields):
                value = doc[key]
                value_type = type(value).__name__
                
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        print(f"{key:40} ({value_type:15}): [{len(value)} items]")
                        for i, item in enumerate(value):
                            print(f"{'':40}   Item {i+1}:")
                            print(json.dumps(item, indent=6, default=str))
                    else:
                        print(f"{key:40} ({value_type:15}): {{{len(value)} keys}}")
                        print(json.dumps(value, indent=6, default=str))
                else:
                    print(f"{key:40} ({value_type:15}): {value}")
        else:
            print("  No regulation/parking/rules fields found")
        print()
        
        # Print STREET SWEEPING/SCHEDULES fields
        print("STREET SWEEPING/CLEANING/SCHEDULES FIELDS:")
        print("-" * 100)
        if sweeping_fields:
            for key in sorted(sweeping_fields):
                value = doc[key]
                value_type = type(value).__name__
                
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        print(f"{key:40} ({value_type:15}): [{len(value)} items]")
                        for i, item in enumerate(value):
                            print(f"{'':40}   Item {i+1}:")
                            print(json.dumps(item, indent=6, default=str))
                    else:
                        print(f"{key:40} ({value_type:15}): {{{len(value)} keys}}")
                        print(json.dumps(value, indent=6, default=str))
                else:
                    print(f"{key:40} ({value_type:15}): {value}")
        else:
            print("  No street sweeping/cleaning/schedules fields found")
        print()
        
        # Save individual segment to file
        filename = f"backend/cnn_783420_side_{doc.get('side')}_all_fields.json"
        
        # Create filtered document with only relevant fields
        filtered_doc = {
            "cnn": doc.get("cnn"),
            "side": doc.get("side"),
            "streetName": doc.get("streetName"),
            "displayName": doc.get("displayName"),
            "displayAddressRange": doc.get("displayAddressRange"),
            "displayCardinal": doc.get("displayCardinal"),
            "fromStreet": doc.get("fromStreet"),
            "toStreet": doc.get("toStreet"),
            "meter_fields": {k: doc[k] for k in meter_fields} if meter_fields else {},
            "regulation_fields": {k: doc[k] for k in regulation_fields} if regulation_fields else {},
            "sweeping_fields": {k: doc[k] for k in sweeping_fields} if sweeping_fields else {}
        }
        
        with open(filename, "w") as f:
            json.dump(filtered_doc, f, indent=2, default=str)
        
        print(f"✓ Segment data saved to: {filename}")
        print()
    
    print()
    print("=" * 100)
    print(f"✓ Processed {len(segments)} segment(s) for CNN 783420")
    print("=" * 100)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(get_cnn_fields())