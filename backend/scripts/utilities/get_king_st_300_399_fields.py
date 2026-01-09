"""
Get meter, regulation and street sweeping fields for KING ST 300-399 block
- CNN 7834201 (Right side 300-398, NorthWest)
- CNN 7834101 (Left side 301-399, SouthEast)
Between 4TH ST and 5TH ST
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def get_king_st_fields():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 100)
    print("KING ST 300-399 BLOCK - METER, REGULATION & STREET SWEEPING FIELDS")
    print("=" * 100)
    print()
    
    # CNNs for the 300-399 block between 4th and 5th
    target_cnns = [
        ("7834201", "R", "NorthWest, 300-398"),
        ("7834101", "L", "SouthEast, 301-399")
    ]
    
    for cnn, side, description in target_cnns:
        print("=" * 100)
        print(f"CNN {cnn}, SIDE {side} ({description})")
        print("=" * 100)
        print()
        
        # Find in street_segments
        doc = await db.street_segments.find_one({"cnn": cnn, "side": side})
        
        if not doc:
            print(f"ERROR: CNN {cnn} Side {side} not found in street_segments!")
            print()
            continue
        
        # Convert ObjectId to string
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        print(f"Display Name: {doc.get('displayName')}")
        print(f"Address Range: {doc.get('displayAddressRange')}")
        print(f"Cardinal: {doc.get('displayCardinal', 'N/A')}")
        print(f"From Street: {doc.get('fromStreet', 'N/A')}")
        print(f"To Street: {doc.get('toStreet', 'N/A')}")
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
        filename = f"king_st_cnn_{cnn}_side_{side}_fields.json"
        
        # Create filtered document with only relevant fields
        filtered_doc = {
            "cnn": doc.get("cnn"),
            "side": doc.get("side"),
            "description": description,
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
    print(f"✓ Processed KING ST 300-399 block segments")
    print("=" * 100)
    
    # Create documentation about querying streets dataset
    doc_content = """# KING ST CNN Investigation Summary

## Problem
Could not find KING ST segments by searching street_segments collection by street name.

## Root Cause
The `streets` collection (from SF Data Active/Retired Streets dataset) contains the master CNN list with street names, but the `street_segments` collection uses different field names:
- streets collection: `street`, `cnn`, `lf_fadd`, `rt_fadd`, etc.
- street_segments collection: `streetName`, `cnn`, `fromAddress`, `toAddress`, etc.

## Solution
1. Query the `streets` collection to find CNNs by street name
2. Use those CNNs to query the `street_segments` collection for detailed parking data

## KING ST CNNs Found (15 total)
From the `streets` collection query:

```python
cursor = db.streets.find({'street': 'KING'})
```

Results:
- CNN 7834201: Right side 300-398, 4TH ST to 5TH ST (NorthWest)
- CNN 7834101: Left side 301-399, 4TH ST to 5TH ST (SouthEast)
- CNN 7833201: Right side 200-298, 3RD ST to 4TH ST
- CNN 7833101: Left side 201-299, 3RD ST to 4TH ST
- CNN 7832201: Right side 100-198, 2ND ST to 3RD ST
- CNN 7832101: Left side 101-199, 2ND ST to 3RD ST
- CNN 7831201: Right side 2-98, EMBARCADERO to 2ND ST
- CNN 7831101: Left side 1-99, EMBARCADERO to 2ND ST
- CNN 7835001: Both sides 400-499, 5TH ST to BERRY ST
- CNN 7837000: Both sides 600-699, 7TH ST to DIVISION ST
- CNN 7834000, 7835000, 7836000, 7836001, 7836002: Various segments with nan addresses

## Key Learnings
1. **Always check the `streets` collection first** when searching by street name
2. The `streets` collection has the authoritative CNN-to-street-name mapping
3. The `street_segments` collection has the detailed parking/meter/regulation data
4. Field names differ between collections (lowercase vs camelCase)
5. CNNs are stored as strings, not integers

## Query Pattern
```python
# Step 1: Find CNN in streets collection
street_doc = await db.streets.find_one({'street': 'KING', 'lf_fadd': '301', 'lf_toadd': '399'})
cnn = street_doc['cnn']

# Step 2: Get detailed data from street_segments
segment_doc = await db.street_segments.find_one({'cnn': cnn, 'side': 'L'})
```
"""
    
    with open("KING_ST_CNN_INVESTIGATION.md", "w") as f:
        f.write(doc_content)
    
    print()
    print("✓ Documentation saved to: KING_ST_CNN_INVESTIGATION.md")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(get_king_st_fields())