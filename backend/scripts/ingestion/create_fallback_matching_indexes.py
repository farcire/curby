#!/usr/bin/env python3
"""
Create indexes on street_segments collection for efficient fallback matching
Creates compound index on supervisor_district + analysis_neighborhood
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

def main():
    print("=" * 80)
    print("CREATING INDEXES FOR FALLBACK MATCHING")
    print("=" * 80)
    
    load_dotenv()
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['curby']
    
    print("\n1. Creating compound index on supervisor_district + analysis_neighborhood...")
    # Compound index for efficient queries by both fields
    result = db.street_segments.create_index([
        ("supervisor_district", 1),
        ("analysis_neighborhood", 1)
    ])
    print(f"   ✓ Compound index created: {result}")
    
    print("\n2. Creating individual index on supervisor_district...")
    # Individual index for district-only queries
    result = db.street_segments.create_index("supervisor_district")
    print(f"   ✓ Index created: {result}")
    
    print("\n3. Creating individual index on analysis_neighborhood...")
    # Individual index for neighborhood-only queries
    result = db.street_segments.create_index("analysis_neighborhood")
    print(f"   ✓ Index created: {result}")
    
    # List all indexes on street_segments
    print("\n" + "=" * 80)
    print("ALL INDEXES ON street_segments COLLECTION")
    print("=" * 80)
    for index in db.street_segments.list_indexes():
        keys = index.get('key', {})
        print(f"\n  Index: {index['name']}")
        print(f"    Keys: {dict(keys)}")
    
    print("\n" + "=" * 80)
    print("INDEX CREATION COMPLETE")
    print("=" * 80)
    
    print("\n✅ Benefits:")
    print("  - Fast queries by district + neighborhood (compound index)")
    print("  - Efficient fallback matching for unmatched regulations")
    print("  - Optimized queries for district-only or neighborhood-only searches")
    
    print("\n📋 Usage Examples:")
    print("  # Find segments in District 7, Golden Gate Park neighborhood")
    print("  db.street_segments.find({")
    print("    'supervisor_district': '7',")
    print("    'analysis_neighborhood': 'GOLDEN GATE PARK'")
    print("  })")
    
    print("\n  # Find segments in District 7 (any neighborhood)")
    print("  db.street_segments.find({'supervisor_district': '7'})")

if __name__ == "__main__":
    main()