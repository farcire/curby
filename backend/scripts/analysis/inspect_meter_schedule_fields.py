#!/usr/bin/env python3
"""
Inspect actual field names in Meter Operating Schedules dataset.
"""

import os
from sodapy import Socrata
from dotenv import load_dotenv
import json

load_dotenv()

def inspect_fields():
    client = Socrata(
        "data.sfgov.org",
        os.getenv("SFMTA_APP_TOKEN"),
        timeout=30
    )
    
    print("=" * 80)
    print("METER OPERATING SCHEDULES - FIELD INSPECTION")
    print("=" * 80)
    print()
    
    # Fetch a few records
    print("Fetching sample records...")
    records = client.get("6cqg-dxku", limit=5)
    
    if records:
        print(f"✓ Fetched {len(records)} sample records")
        print()
        print("Field names in first record:")
        for field in sorted(records[0].keys()):
            print(f"  - {field}")
        print()
        
        print("First record (full):")
        print(json.dumps(records[0], indent=2))
        print()
        
        # Now search for Posted Events with correct field name
        print("=" * 80)
        print("SEARCHING FOR 'POSTED EVENTS'")
        print("=" * 80)
        print()
        
        # Try different search approaches
        print("Approach 1: Filter by days_applied field...")
        try:
            posted = client.get("6cqg-dxku", 
                              where="days_applied = 'Posted Events'",
                              limit=5)
            print(f"✓ Found {len(posted)} records")
            if posted:
                print("\nSample Posted Events record:")
                print(json.dumps(posted[0], indent=2))
        except Exception as e:
            print(f"✗ Error: {e}")
        
        print()
        print("Approach 2: Search all records for 'posted event' pattern...")
        all_records = client.get("6cqg-dxku", limit=100000)
        posted_events = []
        
        for rec in all_records:
            days = rec.get('days_applied', '')
            if 'posted event' in str(days).lower():
                posted_events.append(rec)
        
        print(f"✓ Found {len(posted_events)} records with 'posted event' in days_applied")
        
        if posted_events:
            print("\nFirst Posted Events record:")
            print(json.dumps(posted_events[0], indent=2))
            
            # Check for postid field
            postid_field = None
            for key in posted_events[0].keys():
                if 'post' in key.lower() and 'id' in key.lower():
                    postid_field = key
                    break
            
            print(f"\nPostID field name: {postid_field}")
            print(f"PostID value: {posted_events[0].get(postid_field)}")
    
    client.close()

if __name__ == "__main__":
    inspect_fields()