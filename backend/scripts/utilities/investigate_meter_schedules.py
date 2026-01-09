#!/usr/bin/env python3
"""
Investigate meter schedules to see if rates are populated
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
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    return db

def main():
    print("=" * 80)
    print("INVESTIGATING METER SCHEDULES")
    print("=" * 80)
    
    db = connect_to_mongodb()
    
    # Find a metered segment
    segment = db.street_segments.find_one(
        {"meters": {"$exists": True, "$ne": []}},
        {"cnn": 1, "streetName": 1, "side": 1, "meters": 1, "schedules": 1}
    )
    
    if not segment:
        print("No metered segments found")
        return
    
    print(f"\nCNN: {segment.get('cnn')}")
    print(f"Street: {segment.get('streetName')} ({segment.get('side')})")
    
    meters = segment.get('meters', [])
    schedules = segment.get('schedules', [])
    
    print(f"\nNumber of meters: {len(meters)}")
    print(f"Number of schedules: {len(schedules)}")
    
    # Show first meter structure
    if meters:
        print("\n" + "=" * 80)
        print("FIRST METER STRUCTURE")
        print("=" * 80)
        print(json.dumps(meters[0], indent=2, default=str))
    
    # Show first 3 schedules
    if schedules:
        print("\n" + "=" * 80)
        print("FIRST 3 SCHEDULES")
        print("=" * 80)
        for i, schedule in enumerate(schedules[:3], 1):
            print(f"\nSchedule {i}:")
            print(json.dumps(schedule, indent=2, default=str))
    
    # Check if schedules have rate fields
    print("\n" + "=" * 80)
    print("SCHEDULE FIELD ANALYSIS")
    print("=" * 80)
    
    fields_found = set()
    for schedule in schedules:
        fields_found.update(schedule.keys())
    
    print(f"Fields found in schedules: {sorted(fields_found)}")
    
    # Check for rate-related fields
    rate_fields = ['rate', 'rate_per_hour', 'ratePerHour', 'rateQualifier', 'rateUnit']
    print(f"\nRate-related fields present:")
    for field in rate_fields:
        has_field = field in fields_found
        print(f"  {field}: {'✓' if has_field else '✗'}")
    
    # Sample rate values
    if schedules:
        print(f"\nSample rate values from first 5 schedules:")
        for i, schedule in enumerate(schedules[:5], 1):
            rate = schedule.get('rate') or schedule.get('rate_per_hour') or schedule.get('ratePerHour')
            print(f"  Schedule {i}: {rate}")

if __name__ == "__main__":
    main()