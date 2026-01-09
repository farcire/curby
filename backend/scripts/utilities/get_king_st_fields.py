"""
Get meter, regulation and street sweeping fields for KING ST segments
- KING ST (NorthWest, 300-398) between 4th St → 5th St
- KING ST (SouthEast, 301-399) between 4th St → 5th St
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json
from pprint import pprint

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def get_king_st_fields():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 100)
    print("KING ST SEGMENTS - METER, REGULATION & STREET SWEEPING FIELDS")
    print("=" * 100)
    print()
    
    # Find all KING ST segments
    cursor = db.street_segments.find({
        "streetName": {"$regex": "KING", "$options": "i"}
    })
    
    segments = await cursor.to_list(length=None)
    
    if not segments:
        print("ERROR: No KING ST segments found!")
        client.close()
        return
    
    print(f"Found {len(segments)} KING ST segments")
    print()
    
    # Filter for segments near 4th/5th St with address ranges 300-399
    target_segments = []
    for seg in segments:
        # Check if address range overlaps with 300-399
        from_addr = seg.get("fromAddress")
        to_addr = seg.get("toAddress")
        
        if from_addr and to_addr:
            if (from_addr >= 300 and from_addr <= 399) or (to_addr >= 300 and to_addr <= 399):
                target_segments.append(seg)
    
    print(f"Found {len(target_segments)} segments in 300-399 range")
    print()
    
    # Process each segment
    for idx, doc in enumerate(target_segments, 1):
        # Convert ObjectId to string for JSON serialization
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        print("=" * 100)
        print(f"SEGMENT {idx}: CNN {doc.get('cnn')}, SIDE {doc.get('side')}")
        print(f"Display Name: {doc.get('displayName')}")
        print(f"Address: {doc.get('fromAddress')}-{doc.get('toAddress')} {doc.get('streetName')} ST")
        print(f"Cardinal: {doc.get('cardinalDirection', 'N/A')}")
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
        if meter_fields:
            print("METER FIELDS:")
            print("-" * 100)
            for key in sorted(meter_fields):
                value = doc[key]
                value_type = type(value).__name__
                
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        preview = f"[{len(value)} items]"
                        print(f"{key:40} ({value_type:15}): {preview}")
                        if value:  # Show first item if exists
                            print(f"{'':40}   First item: {json.dumps(value[0], indent=2, default=str)[:300]}")
                    else:
                        preview = f"{{{len(value)} keys}}"
                        print(f"{key:40} ({value_type:15}): {preview}")
                        print(f"{'':40}   {json.dumps(value, indent=2, default=str)[:300]}")
                else:
                    preview = str(value)[:100]
                    print(f"{key:40} ({value_type:15}): {preview}")
            print()
        else:
            print("METER FIELDS: None found")
            print()
        
        # Print REGULATION/PARKING/RULES fields
        if regulation_fields:
            print("REGULATION/PARKING/RULES FIELDS:")
            print("-" * 100)
            for key in sorted(regulation_fields):
                value = doc[key]
                value_type = type(value).__name__
                
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        preview = f"[{len(value)} items]"
                        print(f"{key:40} ({value_type:15}): {preview}")
                        if value:  # Show all items for rules
                            for i, item in enumerate(value):
                                print(f"{'':40}   Item {i+1}: {json.dumps(item, indent=2, default=str)}")
                    else:
                        preview = f"{{{len(value)} keys}}"
                        print(f"{key:40} ({value_type:15}): {preview}")
                        print(f"{'':40}   {json.dumps(value, indent=2, default=str)}")
                else:
                    preview = str(value)[:100]
                    print(f"{key:40} ({value_type:15}): {preview}")
            print()
        else:
            print("REGULATION/PARKING/RULES FIELDS: None found")
            print()
        
        # Print STREET SWEEPING/SCHEDULES fields
        if sweeping_fields:
            print("STREET SWEEPING/CLEANING/SCHEDULES FIELDS:")
            print("-" * 100)
            for key in sorted(sweeping_fields):
                value = doc[key]
                value_type = type(value).__name__
                
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        preview = f"[{len(value)} items]"
                        print(f"{key:40} ({value_type:15}): {preview}")
                        if value:  # Show all items for sweeping
                            for i, item in enumerate(value):
                                print(f"{'':40}   Item {i+1}: {json.dumps(item, indent=2, default=str)}")
                    else:
                        preview = f"{{{len(value)} keys}}"
                        print(f"{key:40} ({value_type:15}): {preview}")
                        print(f"{'':40}   {json.dumps(value, indent=2, default=str)}")
                else:
                    preview = str(value)[:100]
                    print(f"{key:40} ({value_type:15}): {preview}")
            print()
        else:
            print("STREET SWEEPING/CLEANING/SCHEDULES FIELDS: None found")
            print()
        
        print()
        
        # Save individual segment to file
        filename = f"backend/king_st_cnn_{doc.get('cnn')}_side_{doc.get('side')}_fields.json"
        
        # Create filtered document with only relevant fields
        filtered_doc = {
            "cnn": doc.get("cnn"),
            "side": doc.get("side"),
            "streetName": doc.get("streetName"),
            "displayName": doc.get("displayName"),
            "fromAddress": doc.get("fromAddress"),
            "toAddress": doc.get("toAddress"),
            "cardinalDirection": doc.get("cardinalDirection"),
            "fromStreet": doc.get("fromStreet"),
            "toStreet": doc.get("toStreet"),
            "meter_fields": {k: doc[k] for k in meter_fields} if meter_fields else {},
            "regulation_fields": {k: doc[k] for k in regulation_fields} if regulation_fields else {},
            "sweeping_fields": {k: doc[k] for k in sweeping_fields} if sweeping_fields else {}
        }
        
        with open(filename, "w") as f:
            json.dump(filtered_doc, f, indent=2, default=str)
        
        print(f"Segment data saved to: {filename}")
        print()
    
    print()
    print("=" * 100)
    print(f"Processed {len(target_segments)} KING ST segments")
    print("=" * 100)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(get_king_st_fields())