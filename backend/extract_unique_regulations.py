"""
Extract unique regulation combinations from the parking_regulations collection.

This script:
1. Fetches all parking regulations from MongoDB
2. Groups them by unique field combinations (ALL relevant fields)
3. Exports results with associated ObjectIds for human review
4. Generates statistics on deduplication effectiveness
"""

import asyncio
import os
import json
import hashlib
from collections import defaultdict
from typing import Dict, List, Any
from dotenv import load_dotenv
import motor.motor_asyncio
from datetime import datetime
from bson import ObjectId

# Custom JSON encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def normalize_value(val):
    """Normalize a value for comparison - handle None, NaN, empty strings."""
    if val is None:
        return None
    if isinstance(val, float):
        import math
        if math.isnan(val):
            return None
        return val
    if isinstance(val, str):
        stripped = val.strip()
        return stripped if stripped else None
    return val

def create_unique_key(reg: Dict[str, Any]) -> str:
    """
    Create a unique key for a regulation based on ALL semantic fields.
    
    Fields used for uniqueness (as specified by user):
    - regulation (text)
    - days (schedule)
    - hours (time window)
    - hrs_begin (start time)
    - hrs_end (end time)
    - regdetails (regulation details)
    - rpparea1 (RPP zone)
    - exceptions (exceptions text)
    - from_time (formatted start time)
    - to_time (formatted end time)
    - hrlimit (time limit in hours)
    
    Fields EXCLUDED (location-specific):
    - cnn, geometry, addresses, neighborhoods, objectid
    """
    key_fields = {
        'regulation': normalize_value(reg.get('regulation')),
        'days': normalize_value(reg.get('days')),
        'hours': normalize_value(reg.get('hours')),
        'hrs_begin': normalize_value(reg.get('hrs_begin')),
        'hrs_end': normalize_value(reg.get('hrs_end')),
        'regdetails': normalize_value(reg.get('regdetails')),
        'rpparea1': normalize_value(reg.get('rpparea1')),
        'exceptions': normalize_value(reg.get('exceptions')),
        'from_time': normalize_value(reg.get('from_time')),
        'to_time': normalize_value(reg.get('to_time')),
        'hrlimit': normalize_value(reg.get('hrlimit')),
    }
    
    # Normalize strings to uppercase for comparison
    for k, v in key_fields.items():
        if isinstance(v, str):
            key_fields[k] = v.upper()
    
    # Create a stable string representation
    key_string = json.dumps(key_fields, sort_keys=True)
    
    # Return hash for compact storage
    return hashlib.md5(key_string.encode()).hexdigest()

async def extract_unique_regulations():
    """Extract and group unique regulation combinations."""
    
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("❌ Error: MONGODB_URI not found in environment variables")
        return

    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    print("🔍 Fetching parking regulations from MongoDB...")
    
    # Fetch all regulations with ALL relevant fields
    projection = {
        "regulation": 1,
        "days": 1,
        "hours": 1,
        "hrs_begin": 1,
        "hrs_end": 1,
        "regdetails": 1,
        "rpparea1": 1,
        "exceptions": 1,
        "from_time": 1,
        "to_time": 1,
        "hrlimit": 1
    }
    
    regulations = await db.parking_regulations.find({}, projection).to_list(None)
    total_count = len(regulations)
    
    if total_count == 0:
        print("❌ No regulations found in 'parking_regulations' collection.")
        client.close()
        return

    print(f"✅ Found {total_count:,} total parking regulations")
    print("\n📊 Grouping by unique field combinations...")
    print("   Fields used: regulation, days, hours, hrs_begin, hrs_end,")
    print("                regdetails, rpparea1, exceptions, from_time, to_time, hrlimit")
    
    # Group by unique key
    unique_groups: Dict[str, Dict[str, Any]] = {}
    
    for reg in regulations:
        unique_key = create_unique_key(reg)
        
        if unique_key not in unique_groups:
            # Initialize group with normalized values
            unique_groups[unique_key] = {
                "unique_id": unique_key,
                "fields": {
                    'regulation': normalize_value(reg.get('regulation')),
                    'days': normalize_value(reg.get('days')),
                    'hours': normalize_value(reg.get('hours')),
                    'hrs_begin': normalize_value(reg.get('hrs_begin')),
                    'hrs_end': normalize_value(reg.get('hrs_end')),
                    'regdetails': normalize_value(reg.get('regdetails')),
                    'rpparea1': normalize_value(reg.get('rpparea1')),
                    'exceptions': normalize_value(reg.get('exceptions')),
                    'from_time': normalize_value(reg.get('from_time')),
                    'to_time': normalize_value(reg.get('to_time')),
                    'hrlimit': normalize_value(reg.get('hrlimit')),
                },
                "usage_count": 0,
                "all_object_ids": []
            }
        
        unique_groups[unique_key]["usage_count"] += 1
        unique_groups[unique_key]["all_object_ids"].append(reg["_id"])
    
    unique_count = len(unique_groups)
    dedup_ratio = (1 - (unique_count / total_count)) * 100
    
    print(f"✅ Extracted {unique_count} unique combinations")
    print(f"📉 Deduplication Ratio: {dedup_ratio:.1f}%")
    
    # Prepare output structure
    output_data = {
        "metadata": {
            "total_regulations": total_count,
            "unique_combinations": unique_count,
            "deduplication_ratio": f"{dedup_ratio:.1f}%",
            "extracted_at": datetime.now().isoformat(),
            "fields_used": [
                "regulation", "days", "hours", "hrs_begin", "hrs_end",
                "regdetails", "rpparea1", "exceptions", "from_time", "to_time", "hrlimit"
            ]
        },
        "unique_combinations": []
    }
    
    # Sort by usage count (most common first)
    sorted_groups = sorted(unique_groups.values(), key=lambda x: x["usage_count"], reverse=True)
    
    for group in sorted_groups:
        # Add sample IDs for review (first 5)
        group["sample_object_ids"] = group["all_object_ids"][:5]
        # Keep full list for mapping later
        output_data["unique_combinations"].append(group)
        
    # Write to file
    output_file = "unique_regulations.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, cls=JSONEncoder)
        
    print(f"\n💾 Saved results to {output_file}")
    print(f"\n📋 Top 10 most common regulations:")
    for i, group in enumerate(sorted_groups[:10], 1):
        fields = group["fields"]
        reg_text = fields.get('regulation') or 'N/A'
        days = fields.get('days') or 'N/A'
        hours = fields.get('hours') or 'N/A'
        hrlimit = fields.get('hrlimit') or 'N/A'
        rpp = fields.get('rpparea1') or 'N/A'
        desc = f"{reg_text} | {days} {hours} | Limit:{hrlimit} | RPP:{rpp}"
        print(f"   {i:2d}. [{group['usage_count']:4d} uses] {desc[:80]}")

    client.close()

if __name__ == "__main__":
    asyncio.run(extract_unique_regulations())