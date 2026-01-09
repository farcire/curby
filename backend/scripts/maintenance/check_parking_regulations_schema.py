#!/usr/bin/env python3
"""
Check the schema of parking_regulations collection to understand how to query skipped regulations
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
    print("PARKING REGULATIONS COLLECTION SCHEMA")
    print("=" * 80)
    
    db = connect_to_mongodb()
    
    # Get total count
    total = db.parking_regulations.count_documents({})
    print(f"\nTotal parking regulations: {total}")
    
    # Get a sample document
    sample = db.parking_regulations.find_one({})
    
    if sample:
        print("\n" + "=" * 80)
        print("SAMPLE DOCUMENT STRUCTURE")
        print("=" * 80)
        print(json.dumps(sample, indent=2, default=str))
        
        print("\n" + "=" * 80)
        print("AVAILABLE FIELDS")
        print("=" * 80)
        fields = list(sample.keys())
        for field in sorted(fields):
            value = sample.get(field)
            value_type = type(value).__name__
            value_preview = str(value)[:50] if value else "None"
            print(f"  {field}: {value_type} = {value_preview}")
        
        # Check if OBJECTID field exists
        print("\n" + "=" * 80)
        print("CHECKING FOR OBJECTID FIELD")
        print("=" * 80)
        
        objectid_fields = [f for f in fields if 'object' in f.lower()]
        if objectid_fields:
            print(f"Found fields with 'object': {objectid_fields}")
            for field in objectid_fields:
                print(f"\n  {field} sample values:")
                cursor = db.parking_regulations.find({field: {"$exists": True}}, {field: 1}).limit(5)
                for doc in cursor:
                    print(f"    {doc.get(field)}")
        else:
            print("No fields containing 'object' found")
        
        # Try to find regulation with OBJECTID 1551
        print("\n" + "=" * 80)
        print("SEARCHING FOR OBJECTID 1551")
        print("=" * 80)
        
        # Try different field names
        search_fields = ['objectid', 'OBJECTID', 'object_id', 'sfmta_objectid']
        for field in search_fields:
            result = db.parking_regulations.find_one({field: 1551})
            if result:
                print(f"✓ Found using field '{field}'")
                print(f"  Document: {json.dumps(result, indent=2, default=str)[:500]}")
                break
            else:
                result = db.parking_regulations.find_one({field: "1551"})
                if result:
                    print(f"✓ Found using field '{field}' (as string)")
                    print(f"  Document: {json.dumps(result, indent=2, default=str)[:500]}")
                    break
        else:
            print("✗ Could not find regulation with OBJECTID 1551 using any field")

if __name__ == "__main__":
    main()