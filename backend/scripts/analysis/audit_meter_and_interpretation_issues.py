"""
Systematic audit to identify:
1. Segments with schedules array but no actual meter data (null values)
2. Segments with street-sweeping rules that need proper interpretation
3. Segments with "No parking any time" + street sweeping combination

This helps identify where meter data is missing and where interpretations need to be applied.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json
from collections import defaultdict

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def audit_issues():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 100)
    print("SYSTEMATIC AUDIT: METER DATA & INTERPRETATION ISSUES")
    print("=" * 100)
    print()
    
    # Get all segments
    cursor = db.street_segments.find({})
    segments = await cursor.to_list(length=None)
    
    print(f"Total segments in database: {len(segments)}")
    print()
    
    # Issue 1: Segments with schedules array but all null values
    segments_with_null_schedules = []
    segments_with_valid_schedules = []
    segments_without_schedules = []
    
    # Issue 2: Segments with street-sweeping rules needing interpretation
    segments_with_sweeping_rules = []
    
    # Issue 3: Segments with "No parking" + street sweeping combination
    segments_with_no_parking_and_sweeping = []
    
    # Issue 4: Segments with no meters field at all
    segments_without_meters_field = []
    
    for seg in segments:
        cnn = seg.get('cnn')
        side = seg.get('side')
        display_name = seg.get('displayName', f"CNN {cnn} Side {side}")
        
        # Check schedules
        schedules = seg.get('schedules', [])
        if schedules:
            # Check if all schedules have null values
            all_null = all(
                s.get('rate') is None and 
                s.get('beginTime') is None and 
                s.get('endTime') is None 
                for s in schedules
            )
            if all_null:
                segments_with_null_schedules.append({
                    'cnn': cnn,
                    'side': side,
                    'displayName': display_name,
                    'schedules_count': len(schedules)
                })
            else:
                segments_with_valid_schedules.append({
                    'cnn': cnn,
                    'side': side,
                    'displayName': display_name
                })
        else:
            segments_without_schedules.append({
                'cnn': cnn,
                'side': side,
                'displayName': display_name
            })
        
        # Check for meters field
        if 'meters' not in seg:
            segments_without_meters_field.append({
                'cnn': cnn,
                'side': side,
                'displayName': display_name
            })
        
        # Check rules
        rules = seg.get('rules', [])
        
        # Find street-sweeping rules
        sweeping_rules = [r for r in rules if r.get('type') == 'street-sweeping']
        if sweeping_rules:
            segments_with_sweeping_rules.append({
                'cnn': cnn,
                'side': side,
                'displayName': display_name,
                'sweeping_count': len(sweeping_rules),
                'sample_rule': sweeping_rules[0]
            })
        
        # Find "No parking" + street sweeping combination
        has_no_parking = any(
            r.get('type') == 'parking-regulation' and 
            'no parking' in str(r.get('regulation', '')).lower()
            for r in rules
        )
        if has_no_parking and sweeping_rules:
            segments_with_no_parking_and_sweeping.append({
                'cnn': cnn,
                'side': side,
                'displayName': display_name,
                'total_rules': len(rules),
                'sweeping_rules': len(sweeping_rules)
            })
    
    # Report findings
    print("=" * 100)
    print("ISSUE 1: SEGMENTS WITH NULL SCHEDULE VALUES (Missing Meter Data)")
    print("=" * 100)
    print(f"Segments with schedules array but all null values: {len(segments_with_null_schedules)}")
    print(f"Segments with valid schedule data: {len(segments_with_valid_schedules)}")
    print(f"Segments without schedules field: {len(segments_without_schedules)}")
    print()
    
    if segments_with_null_schedules:
        print("Sample segments with null schedules (first 10):")
        for seg in segments_with_null_schedules[:10]:
            print(f"  {seg['displayName']} - {seg['schedules_count']} null schedule entries")
    
    print()
    print("=" * 100)
    print("ISSUE 2: SEGMENTS WITHOUT METERS FIELD")
    print("=" * 100)
    print(f"Total segments without 'meters' field: {len(segments_without_meters_field)}")
    print(f"Percentage: {len(segments_without_meters_field) / len(segments) * 100:.1f}%")
    print()
    
    print("=" * 100)
    print("ISSUE 3: STREET SWEEPING RULES NEEDING INTERPRETATION")
    print("=" * 100)
    print(f"Segments with street-sweeping rules: {len(segments_with_sweeping_rules)}")
    print()
    
    # Analyze sweeping patterns
    sweeping_patterns = defaultdict(list)
    for seg in segments_with_sweeping_rules:
        pattern_key = f"{seg['sweeping_count']} sweeping rules"
        sweeping_patterns[pattern_key].append(seg)
    
    print("Sweeping rule patterns:")
    for pattern, segs in sorted(sweeping_patterns.items()):
        print(f"  {pattern}: {len(segs)} segments")
    
    print()
    print("Sample segments with sweeping rules (first 5):")
    for seg in segments_with_sweeping_rules[:5]:
        print(f"  {seg['displayName']}")
        print(f"    Sweeping rules: {seg['sweeping_count']}")
        print(f"    Sample: {seg['sample_rule'].get('description', 'N/A')}")
    
    print()
    print("=" * 100)
    print("ISSUE 4: NO PARKING + STREET SWEEPING COMBINATION")
    print("=" * 100)
    print(f"Segments with 'No parking any time' + street sweeping: {len(segments_with_no_parking_and_sweeping)}")
    print()
    
    if segments_with_no_parking_and_sweeping:
        print("These segments need special interpretation:")
        print("  Line 1: No parking any time")
        print("  Line 2: Street Cleaning [schedule]")
        print()
        print("Sample segments (first 10):")
        for seg in segments_with_no_parking_and_sweeping[:10]:
            print(f"  {seg['displayName']}")
            print(f"    Total rules: {seg['total_rules']}, Sweeping: {seg['sweeping_rules']}")
    
    # Save detailed reports
    print()
    print("=" * 100)
    print("SAVING DETAILED REPORTS")
    print("=" * 100)
    
    # Save null schedules report
    with open("segments_with_null_schedules.json", "w") as f:
        json.dump(segments_with_null_schedules, f, indent=2, default=str)
    print(f"✓ Saved: segments_with_null_schedules.json ({len(segments_with_null_schedules)} segments)")
    
    # Save no parking + sweeping report
    with open("segments_no_parking_plus_sweeping.json", "w") as f:
        json.dump(segments_with_no_parking_and_sweeping, f, indent=2, default=str)
    print(f"✓ Saved: segments_no_parking_plus_sweeping.json ({len(segments_with_no_parking_and_sweeping)} segments)")
    
    # Save all sweeping segments report
    with open("segments_with_sweeping_rules.json", "w") as f:
        json.dump(segments_with_sweeping_rules, f, indent=2, default=str)
    print(f"✓ Saved: segments_with_sweeping_rules.json ({len(segments_with_sweeping_rules)} segments)")
    
    # Create summary report
    summary = {
        "audit_date": "2025-12-05",
        "total_segments": len(segments),
        "issues": {
            "null_schedules": {
                "count": len(segments_with_null_schedules),
                "percentage": f"{len(segments_with_null_schedules) / len(segments) * 100:.1f}%",
                "description": "Segments with schedules array but all null values (missing meter data)"
            },
            "no_meters_field": {
                "count": len(segments_without_meters_field),
                "percentage": f"{len(segments_without_meters_field) / len(segments) * 100:.1f}%",
                "description": "Segments without 'meters' field at all"
            },
            "sweeping_rules": {
                "count": len(segments_with_sweeping_rules),
                "percentage": f"{len(segments_with_sweeping_rules) / len(segments) * 100:.1f}%",
                "description": "Segments with street-sweeping rules"
            },
            "no_parking_plus_sweeping": {
                "count": len(segments_with_no_parking_and_sweeping),
                "percentage": f"{len(segments_with_no_parking_and_sweeping) / len(segments) * 100:.1f}%",
                "description": "Segments with 'No parking any time' + street sweeping (need special interpretation)"
            }
        },
        "recommendations": [
            "Ingest meter data from SFMTA parking meters dataset",
            "Apply proper interpretation to street sweeping rules",
            "Handle 'No parking + sweeping' combination with two-line display",
            "Consider removing null schedule entries or populating with actual data"
        ]
    }
    
    with open("METER_AND_INTERPRETATION_AUDIT.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved: METER_AND_INTERPRETATION_AUDIT.json")
    
    print()
    print("=" * 100)
    print("AUDIT COMPLETE")
    print("=" * 100)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(audit_issues())