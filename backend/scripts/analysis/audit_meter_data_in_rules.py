"""
Audit Meter Data in Rules

This script checks if meter data is appearing in the rules window
when there are no actual meters for that blockface/CNN.

It verifies that:
1. Segments with schedules have actual meter data (not null)
2. Segments without meters don't show meter-related rules
3. King Street and other metered streets show correct data
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def audit_meter_data():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    collection = db.street_segments
    
    print("=" * 80)
    print("METER DATA IN RULES AUDIT")
    print("=" * 80)
    print()
    
    # Get all segments
    cursor = collection.find({})
    segments = await cursor.to_list(length=None)
    
    print(f"Total segments: {len(segments)}")
    print()
    
    # Analysis categories
    segments_with_schedules = []
    segments_with_null_schedules = []
    segments_with_valid_schedules = []
    segments_without_schedules = []
    
    # Check King Street specifically
    king_street_segments = []
    
    for seg in segments:
        cnn = seg.get('cnn')
        side = seg.get('side')
        display_name = seg.get('displayName', f"CNN {cnn} Side {side}")
        schedules = seg.get('schedules', [])
        
        # Check if this is King Street
        if 'king' in display_name.lower():
            king_street_segments.append({
                'cnn': cnn,
                'side': side,
                'displayName': display_name,
                'schedules': schedules,
                'schedules_count': len(schedules) if schedules else 0
            })
        
        # Categorize by schedule status
        if schedules:
            segments_with_schedules.append(seg)
            
            # Check if schedules are null/empty
            has_valid_data = False
            for schedule in schedules:
                if schedule is None:
                    continue
                # Check if schedule has actual data
                if (schedule.get('rate') is not None or 
                    schedule.get('beginTime') is not None or
                    schedule.get('endTime') is not None):
                    has_valid_data = True
                    break
            
            if has_valid_data:
                segments_with_valid_schedules.append({
                    'cnn': cnn,
                    'side': side,
                    'displayName': display_name,
                    'schedules_count': len(schedules),
                    'sample_schedule': schedules[0] if schedules else None
                })
            else:
                segments_with_null_schedules.append({
                    'cnn': cnn,
                    'side': side,
                    'displayName': display_name,
                    'schedules_count': len(schedules)
                })
        else:
            segments_without_schedules.append({
                'cnn': cnn,
                'side': side,
                'displayName': display_name
            })
    
    # Report findings
    print("=" * 80)
    print("SCHEDULE STATUS BREAKDOWN")
    print("=" * 80)
    print(f"Segments with schedules array: {len(segments_with_schedules)}")
    print(f"  - With valid meter data: {len(segments_with_valid_schedules)}")
    print(f"  - With null/empty data: {len(segments_with_null_schedules)}")
    print(f"Segments without schedules: {len(segments_without_schedules)}")
    print()
    
    # King Street analysis
    print("=" * 80)
    print("KING STREET ANALYSIS")
    print("=" * 80)
    print(f"Found {len(king_street_segments)} King Street segments")
    print()
    
    for seg in king_street_segments[:5]:  # Show first 5
        print(f"{seg['displayName']}")
        print(f"  CNN: {seg['cnn']}, Side: {seg['side']}")
        print(f"  Schedules count: {seg['schedules_count']}")
        if seg['schedules']:
            print(f"  Sample schedule: {seg['schedules'][0]}")
        print()
    
    # Sample valid meter data
    print("=" * 80)
    print("SAMPLE SEGMENTS WITH VALID METER DATA")
    print("=" * 80)
    for seg in segments_with_valid_schedules[:5]:
        print(f"{seg['displayName']}")
        print(f"  CNN: {seg['cnn']}, Side: {seg['side']}")
        print(f"  Schedules: {seg['schedules_count']}")
        print(f"  Sample: {seg['sample_schedule']}")
        print()
    
    # Sample null schedules
    print("=" * 80)
    print("SAMPLE SEGMENTS WITH NULL/EMPTY SCHEDULES")
    print("=" * 80)
    for seg in segments_with_null_schedules[:5]:
        print(f"{seg['displayName']}")
        print(f"  CNN: {seg['cnn']}, Side: {seg['side']}")
        print(f"  Schedules count: {seg['schedules_count']} (but all null/empty)")
        print()
    
    # Save detailed reports
    print("=" * 80)
    print("SAVING REPORTS")
    print("=" * 80)
    
    with open("backend/king_street_meter_analysis.json", "w") as f:
        json.dump(king_street_segments, f, indent=2, default=str)
    print(f"✓ Saved: king_street_meter_analysis.json ({len(king_street_segments)} segments)")
    
    with open("backend/segments_with_valid_meters.json", "w") as f:
        json.dump(segments_with_valid_schedules, f, indent=2, default=str)
    print(f"✓ Saved: segments_with_valid_meters.json ({len(segments_with_valid_schedules)} segments)")
    
    # Summary
    summary = {
        "total_segments": len(segments),
        "with_schedules": len(segments_with_schedules),
        "with_valid_meter_data": len(segments_with_valid_schedules),
        "with_null_schedules": len(segments_with_null_schedules),
        "without_schedules": len(segments_without_schedules),
        "king_street_segments": len(king_street_segments),
        "percentage_with_valid_meters": f"{len(segments_with_valid_schedules) / len(segments) * 100:.1f}%",
        "percentage_with_null_schedules": f"{len(segments_with_null_schedules) / len(segments) * 100:.1f}%"
    }
    
    with open("backend/METER_DATA_AUDIT_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved: METER_DATA_AUDIT_SUMMARY.json")
    
    print()
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(audit_meter_data())