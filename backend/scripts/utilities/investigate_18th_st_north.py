"""
Investigation script for 18th St North 2700-2798
Queries all parking regulations, street sweeping, and meter information
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json
from pprint import pprint

load_dotenv()

# Redirect output to both console and file
class TeeOutput:
    def __init__(self, *files):
        self.files = files
    
    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise Exception("MONGODB_URI environment variable not set")

async def investigate_18th_street():
    """
    Investigate all parking information for 18th St North 2700-2798
    """
    # Setup output to both console and file
    output_file = open("backend/18th_st_north_investigation.txt", "w")
    original_stdout = sys.stdout
    sys.stdout = TeeOutput(sys.stdout, output_file)
    
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client.curby
        
        print("=" * 80)
        print("INVESTIGATION: 18th St North 2700-2798")
        print("=" * 80)
        print()
    
    # Search for 18th Street segments
    print("1. Searching for 18th Street segments...")
    print("-" * 80)
    
    # Query for 18th Street (exact match)
    query = {
        "streetName": "18TH ST"
    }
    
    segments = []
    async for doc in db.street_segments.find(query):
        segments.append(doc)
    
    print(f"Found {len(segments)} total segments for 18th Street")
    print()
    
    # Filter for North side and address range 2700-2798
    print("2. Filtering for North side with address range 2700-2798...")
    print("-" * 80)
    
    matching_segments = []
    for seg in segments:
        # Check if it's North side
        cardinal = seg.get("cardinalDirection", "").upper()
        side = seg.get("side", "")
        
        # Get address range
        from_addr = seg.get("fromAddress")
        to_addr = seg.get("toAddress")
        
        # Check if North side
        is_north = cardinal in ["N", "NORTH"] or "NORTH" in seg.get("displayCardinal", "").upper()
        
        # Check if address range overlaps with 2700-2798
        if from_addr and to_addr:
            try:
                from_num = int(from_addr)
                to_num = int(to_addr)
                
                # Check if ranges overlap
                overlaps = (from_num <= 2798 and to_num >= 2700)
                
                if is_north and overlaps:
                    matching_segments.append(seg)
                    print(f"  ✓ CNN: {seg.get('cnn')}, Side: {side}, Cardinal: {cardinal}")
                    print(f"    Address Range: {from_addr}-{to_addr}")
                    print(f"    Display Name: {seg.get('displayName')}")
                    print()
            except (ValueError, TypeError):
                pass
    
    print(f"Found {len(matching_segments)} matching segments")
    print()
    
    # Display detailed information for each matching segment
    for i, seg in enumerate(matching_segments, 1):
        print("=" * 80)
        print(f"SEGMENT {i}: {seg.get('displayName')}")
        print("=" * 80)
        print()
        
        # Basic Information
        print("BASIC INFORMATION:")
        print("-" * 80)
        print(f"  CNN: {seg.get('cnn')}")
        print(f"  Side: {seg.get('side')}")
        print(f"  Street Name: {seg.get('streetName')}")
        print(f"  Cardinal Direction: {seg.get('cardinalDirection')}")
        print(f"  Display Cardinal: {seg.get('displayCardinal')}")
        print(f"  From Street: {seg.get('fromStreet')}")
        print(f"  To Street: {seg.get('toStreet')}")
        print(f"  Address Range: {seg.get('fromAddress')}-{seg.get('toAddress')}")
        print(f"  Zip Code: {seg.get('zip_code')}")
        print()
        
        # Rules (Parking Regulations, Street Sweeping, etc.)
        rules = seg.get("rules", [])
        print(f"RULES ({len(rules)} total):")
        print("-" * 80)
        
        if rules:
            for j, rule in enumerate(rules, 1):
                print(f"\n  Rule {j}:")
                print(f"    Type: {rule.get('type')}")
                
                # Source text
                source_text = rule.get('source_text')
                if source_text:
                    print(f"    Source Text: {source_text}")
                
                # Source fields (raw data)
                source_fields = rule.get('source_fields', {})
                if source_fields:
                    print(f"    Source Fields:")
                    for key, value in source_fields.items():
                        if value:
                            print(f"      {key}: {value}")
                
                # Interpreted data (AI-generated)
                interpreted = rule.get('interpreted')
                if interpreted:
                    print(f"    Interpreted:")
                    print(f"      Action: {interpreted.get('action')}")
                    print(f"      Summary: {interpreted.get('summary')}")
                    print(f"      Severity: {interpreted.get('severity')}")
                    
                    conditions = interpreted.get('conditions', {})
                    if conditions:
                        print(f"      Conditions:")
                        if conditions.get('days'):
                            print(f"        Days: {', '.join(conditions['days'])}")
                        if conditions.get('hours'):
                            print(f"        Hours: {conditions['hours']}")
                        if conditions.get('time_limit_minutes'):
                            print(f"        Time Limit: {conditions['time_limit_minutes']} minutes")
                        if conditions.get('exceptions'):
                            print(f"        Exceptions: {', '.join(conditions['exceptions'])}")
                    
                    if interpreted.get('details'):
                        print(f"      Details: {interpreted['details']}")
                    
                    if interpreted.get('confidence_score'):
                        print(f"      Confidence Score: {interpreted['confidence_score']}")
                    
                    if interpreted.get('judge_verified'):
                        print(f"      Judge Verified: {interpreted['judge_verified']}")
                
                # Legacy fields
                description = rule.get('description')
                if description:
                    print(f"    Description: {description}")
                
                time_ranges = rule.get('timeRanges', [])
                if time_ranges:
                    print(f"    Time Ranges: {time_ranges}")
                
                metadata = rule.get('metadata', {})
                if metadata:
                    print(f"    Metadata: {json.dumps(metadata, indent=6)}")
        else:
            print("  No rules found")
        
        print()
        
        # Schedules (Meter Information)
        schedules = seg.get("schedules", [])
        print(f"METER SCHEDULES ({len(schedules)} total):")
        print("-" * 80)
        
        if schedules:
            for j, schedule in enumerate(schedules, 1):
                print(f"\n  Schedule {j}:")
                print(f"    Begin Time: {schedule.get('beginTime')}")
                print(f"    End Time: {schedule.get('endTime')}")
                print(f"    Rate: {schedule.get('rate')}")
                print(f"    Rate Qualifier: {schedule.get('rateQualifier')}")
                print(f"    Rate Unit: {schedule.get('rateUnit')}")
        else:
            print("  No meter schedules found")
        
        print()
        
        # Geometry Information
        print("GEOMETRY:")
        print("-" * 80)
        centerline = seg.get("centerlineGeometry")
        blockface = seg.get("blockfaceGeometry")
        
        if centerline:
            coords = centerline.get("coordinates", [])
            print(f"  Centerline Geometry: {centerline.get('type')} with {len(coords)} coordinates")
        
        if blockface:
            coords = blockface.get("coordinates", [])
            print(f"  Blockface Geometry: {blockface.get('type')} with {len(coords)} coordinates")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total 18th Street segments: {len(segments)}")
    print(f"Matching segments (North side, 2700-2798): {len(matching_segments)}")
    
    total_rules = sum(len(seg.get("rules", [])) for seg in matching_segments)
    total_schedules = sum(len(seg.get("schedules", [])) for seg in matching_segments)
    
    print(f"Total rules: {total_rules}")
    print(f"Total meter schedules: {total_schedules}")
    print()
    
    # Export to JSON for further analysis
    output_file = "backend/18th_st_north_investigation.json"
    export_data = {
        "query": "18th St North 2700-2798",
        "total_18th_segments": len(segments),
        "matching_segments_count": len(matching_segments),
        "segments": []
    }
    
    for seg in matching_segments:
        # Remove MongoDB _id for JSON serialization
        seg_copy = dict(seg)
        if "_id" in seg_copy:
            seg_copy["_id"] = str(seg_copy["_id"])
        export_data["segments"].append(seg_copy)
    
    with open(output_file, "w") as f:
        json.dump(export_data, f, indent=2, default=str)
    
        print(f"Detailed results exported to: backend/18th_st_north_investigation.json")
        print()
        
        client.close()
    finally:
        sys.stdout = original_stdout
        output_file.close()

if __name__ == "__main__":
    asyncio.run(investigate_18th_street())