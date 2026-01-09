#!/usr/bin/env python3
"""
Query the 3 unmatched parking regulations to understand their structure
ObjectIDs: 4973, 64, 2191
"""

from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import json

def main():
    load_dotenv()
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['curby']
    
    # The 3 unmatched regulation IDs
    regulation_ids = [4973, 64, 2191]
    
    print("=" * 80)
    print("QUERYING UNMATCHED PARKING REGULATIONS")
    print("=" * 80)
    
    for reg_id in regulation_ids:
        print(f"\n{'='*80}")
        print(f"Regulation ObjectID: {reg_id}")
        print(f"{'='*80}")
        
        # Try to find by _id as integer
        regulation = db.parking_regulations.find_one({"_id": reg_id})
        
        if not regulation:
            # Try as ObjectId
            try:
                regulation = db.parking_regulations.find_one({"_id": ObjectId(str(reg_id))})
            except:
                pass
        
        if not regulation:
            # Try as string in objectid field
            regulation = db.parking_regulations.find_one({"objectid": reg_id})
        
        if not regulation:
            # Try as string
            regulation = db.parking_regulations.find_one({"objectid": str(reg_id)})
        
        if regulation:
            print(f"\n✓ Found regulation")
            print(f"\nKey fields:")
            print(f"  _id: {regulation.get('_id')}")
            print(f"  objectid: {regulation.get('objectid')}")
            print(f"  supervisor_district: {regulation.get('supervisor_district')}")
            print(f"  analysis_neighborhood: {regulation.get('analysis_neighborhood')}")
            print(f"  cnn: {regulation.get('cnn')}")
            print(f"  cnnside: {regulation.get('cnnside')}")
            print(f"  streetname: {regulation.get('streetname')}")
            print(f"  fromstreet: {regulation.get('fromstreet')}")
            print(f"  tostreet: {regulation.get('tostreet')}")
            
            # Check for geometry
            has_geometry = regulation.get('geometry') is not None
            print(f"  has_geometry: {has_geometry}")
            if has_geometry:
                geom = regulation.get('geometry', {})
                print(f"    type: {geom.get('type')}")
                coords = geom.get('coordinates', [])
                if coords:
                    print(f"    coordinates: {len(coords)} points")
            
            # Regulation details
            print(f"\nRegulation details:")
            print(f"  days_applied: {regulation.get('days_applied')}")
            print(f"  begin_time: {regulation.get('begin_time')}")
            print(f"  end_time: {regulation.get('end_time')}")
            print(f"  time_limit: {regulation.get('time_limit')}")
            print(f"  restriction_type: {regulation.get('restriction_type')}")
            
            # Save full regulation
            output_file = f"unmatched_regulation_{reg_id}.json"
            with open(output_file, 'w') as f:
                json.dump(regulation, f, indent=2, default=str)
            print(f"\n  Full regulation saved to: {output_file}")
        else:
            print(f"\n✗ Regulation not found")
            print(f"  Tried: _id={reg_id}, objectid={reg_id}, objectid='{reg_id}'")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print("\nNext steps:")
    print("1. Review the saved JSON files for each regulation")
    print("2. Verify they have supervisor_district and analysis_neighborhood")
    print("3. Create fallback matching script")

if __name__ == "__main__":
    main()