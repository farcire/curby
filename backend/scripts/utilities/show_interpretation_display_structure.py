#!/usr/bin/env python3
"""
Show interpretation display structure for:
1. One segment with meters
2. One segment with non-metered parking regulations
"""

from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

def connect_to_mongodb():
    """Connect to MongoDB"""
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file")
    
    client = MongoClient(mongodb_uri)
    # Try to get default database, fallback to 'curby'
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    return db

def main():
    print("=" * 80)
    print("INTERPRETATION DISPLAY STRUCTURE EXAMPLES")
    print("=" * 80)
    
    db = connect_to_mongodb()
    
    # Example 1: Segment with meters
    print("\n\n1. SEGMENT WITH METERS")
    print("=" * 80)
    
    metered_segment = db.street_segments.find_one(
        {
            "meters": {"$exists": True, "$ne": []},
            "interpretation": {"$exists": True}
        },
        {
            "cnn": 1,
            "streetName": 1,
            "side": 1,
            "meters": 1,
            "interpretation": 1,
            "schedules": 1
        }
    )
    
    if metered_segment:
        print(f"\nCNN: {metered_segment.get('cnn')}")
        print(f"Street: {metered_segment.get('streetName')} ({metered_segment.get('side')})")
        print(f"\nNumber of meters: {len(metered_segment.get('meters', []))}")
        print(f"Number of schedules: {len(metered_segment.get('schedules', []))}")
        
        interpretation = metered_segment.get('interpretation', {})
        print(f"\n--- INTERPRETATION STRUCTURE ---")
        print(f"Version: {interpretation.get('version')}")
        print(f"Parking Status: {interpretation.get('parking_status')}")
        print(f"Has Meters: {interpretation.get('has_meters')}")
        print(f"Manual Overrides: {len(interpretation.get('manual_overrides', []))}")
        
        rules_display = interpretation.get('rules_display', [])
        print(f"\nRules Display Count: {len(rules_display)}")
        print(f"Rules Display Type: {type(rules_display[0]).__name__ if rules_display else 'N/A'}")
        
        if rules_display:
            print(f"\n--- RULES DISPLAY CONTENT ---")
            for i, rule in enumerate(rules_display[:5], 1):  # Show first 5
                print(f"{i}. {rule}")
        
        # Show full JSON structure
        print(f"\n--- FULL INTERPRETATION JSON ---")
        print(json.dumps(interpretation, indent=2, default=str))
    else:
        print("No metered segment found")
    
    # Example 2: Segment with non-metered parking regulations
    print("\n\n" + "=" * 80)
    print("2. SEGMENT WITH NON-METERED PARKING REGULATIONS")
    print("=" * 80)
    
    non_metered_segment = db.street_segments.find_one(
        {
            "$or": [
                {"meters": {"$exists": False}},
                {"meters": []}
            ],
            "rules": {
                "$elemMatch": {
                    "ruleType": {"$in": ["parking_regulation", "time_limit"]}
                }
            },
            "interpretation": {"$exists": True}
        },
        {
            "cnn": 1,
            "streetName": 1,
            "side": 1,
            "rules": 1,
            "interpretation": 1
        }
    )
    
    if non_metered_segment:
        print(f"\nCNN: {non_metered_segment.get('cnn')}")
        print(f"Street: {non_metered_segment.get('streetName')} ({non_metered_segment.get('side')})")
        
        rules = non_metered_segment.get('rules', [])
        parking_rules = [r for r in rules if r.get('ruleType') in ['parking_regulation', 'time_limit']]
        print(f"\nNumber of parking regulation rules: {len(parking_rules)}")
        
        interpretation = non_metered_segment.get('interpretation', {})
        print(f"\n--- INTERPRETATION STRUCTURE ---")
        print(f"Version: {interpretation.get('version')}")
        print(f"Parking Status: {interpretation.get('parking_status')}")
        print(f"Has Meters: {interpretation.get('has_meters')}")
        print(f"Manual Overrides: {len(interpretation.get('manual_overrides', []))}")
        
        rules_display = interpretation.get('rules_display', [])
        print(f"\nRules Display Count: {len(rules_display)}")
        print(f"Rules Display Type: {type(rules_display[0]).__name__ if rules_display else 'N/A'}")
        
        if rules_display:
            print(f"\n--- RULES DISPLAY CONTENT ---")
            for i, rule in enumerate(rules_display[:5], 1):  # Show first 5
                print(f"{i}. {rule}")
        
        # Show full JSON structure
        print(f"\n--- FULL INTERPRETATION JSON ---")
        print(json.dumps(interpretation, indent=2, default=str))
    else:
        print("No non-metered segment with parking regulations found")
    
    print("\n\n" + "=" * 80)
    print("DONE")
    print("=" * 80)

if __name__ == "__main__":
    main()