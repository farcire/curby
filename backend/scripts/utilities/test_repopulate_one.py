"""
Test repopulation on a single segment (20th St North, CNN 7834101, Side L)
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from typing import Dict
from shapely.geometry import shape
from regulation_normalizer import normalize_regulation
import json

load_dotenv()

def match_regulation_to_segment(regulation_geo: Dict, 
                                centerline_geo: Dict,
                                segment_side: str,
                                max_distance: float = 0.0005) -> bool:
    """Check if regulation applies to segment side."""
    try:
        reg_line = shape(regulation_geo)
        center_line = shape(centerline_geo)
        
        distance = reg_line.distance(center_line)
        if distance > max_distance:
            return False
        
        # Sample points to determine side
        sample_points = [0.25, 0.5, 0.75]
        side_votes = {"L": 0, "R": 0}
        
        for position in sample_points:
            reg_point = reg_line.interpolate(position, normalized=True)
            projected_dist = center_line.project(reg_point)
            projected_point = center_line.interpolate(projected_dist)
            
            delta = 0.001
            if projected_dist + delta > center_line.length:
                p1 = center_line.interpolate(projected_dist - delta)
                p2 = projected_point
            else:
                p1 = projected_point
                p2 = center_line.interpolate(projected_dist + delta)
            
            tangent = (p2.x - p1.x, p2.y - p1.y)
            to_reg = (reg_point.x - projected_point.x, reg_point.y - projected_point.y)
            cross = tangent[0] * to_reg[1] - tangent[1] * to_reg[0]
            
            if cross > 0:
                side_votes["L"] += 1
            elif cross < 0:
                side_votes["R"] += 1
        
        determined_side = "L" if side_votes["L"] > side_votes["R"] else "R"
        return determined_side == segment_side
        
    except Exception as e:
        print(f"Error in matching: {e}")
        return False

async def main():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    print("=" * 80)
    print("TEST: Repopulate ONE segment (20th St North)")
    print("=" * 80)
    
    # Get the specific segment
    TEST_CNN = "7834101"
    TEST_SIDE = "L"
    
    print(f"\n1. Loading segment CNN={TEST_CNN}, Side={TEST_SIDE}...")
    segment = await db.street_segments.find_one({"cnn": TEST_CNN, "side": TEST_SIDE})
    
    if not segment:
        print("   ✗ Segment not found!")
        client.close()
        return
    
    print(f"   ✓ Found: {segment.get('streetName')}")
    print(f"   Current rules: {len(segment.get('rules', []))}")
    
    # Show current state
    print("\n2. Current rules array:")
    print(json.dumps(segment.get('rules', []), indent=2, default=str)[:500])
    
    # Build new rules array
    new_rules = []
    
    # Match parking regulations
    print("\n3. Matching parking regulations...")
    parking_regs = await db.parking_regulations.find({}).to_list(None)
    print(f"   Checking {len(parking_regs)} regulations...")
    
    matched_regs = 0
    for reg in parking_regs:
        reg_geo = reg.get("shape") or reg.get("geometry")
        if not reg_geo or not isinstance(reg_geo, dict):
            continue
        
        if match_regulation_to_segment(reg_geo, segment["centerlineGeometry"], segment["side"]):
            normalized = normalize_regulation(reg, dataset_type='parking_reg')
            
            # Skip 72hr RPP rules
            if normalized['canonical']['is_rpp_72hr']:
                continue
            
            rule = {
                "type": "time-limit" if "limit" in reg.get("regulation", "").lower() else "parking-regulation",
                "regulation": reg.get("regulation"),
                "timeLimit": reg.get("hrlimit"),
                "permitArea": reg.get("rpparea1") or reg.get("rpparea2"),
                "days": reg.get("days"),
                "hours": reg.get("hours"),
                "fromTime": reg.get("from_time"),
                "toTime": reg.get("to_time"),
                "activeDays": normalized['canonical']['days'],
                "startTimeMin": normalized['canonical']['time_start'],
                "endTimeMin": normalized['canonical']['time_end'],
                "description": normalized['display']['summary'],
                "displayDays": normalized['display']['days'],
                "displayTime": normalized['display']['time'],
                "durationMinutes": normalized['canonical']['duration_minutes'],
                "hasLimit": normalized['canonical']['has_limit'],
                "displayDuration": normalized['display']['duration'],
                "displayDurationLong": normalized['display']['duration_long'],
                "details": reg.get("regdetails"),
                "exceptions": reg.get("exceptions"),
                "side": segment["side"]
            }
            
            new_rules.append(rule)
            matched_regs += 1
    
    print(f"   ✓ Matched {matched_regs} parking regulations")
    
    # Match street cleaning
    print("\n4. Matching street cleaning...")
    cleaning = await db.street_cleaning_schedules.find_one({
        "cnn": TEST_CNN,
        "cnnrightleft": TEST_SIDE
    })
    
    if cleaning:
        normalized = normalize_regulation(cleaning, dataset_type='street_cleaning')
        
        rule = {
            "type": "street-sweeping",
            "day": cleaning.get("weekday"),
            "startTime": cleaning.get("fromhour"),
            "endTime": cleaning.get("tohour"),
            "activeDays": normalized['canonical']['days'],
            "startTimeMin": normalized['canonical']['time_start'],
            "endTimeMin": normalized['canonical']['time_end'],
            "description": normalized['display']['summary'],
            "displayDays": normalized['display']['days'],
            "displayTime": normalized['display']['time'],
            "blockside": cleaning.get("blockside"),
            "side": TEST_SIDE,
            "limits": cleaning.get("limits")
        }
        
        new_rules.append(rule)
        print(f"   ✓ Matched 1 street cleaning schedule")
    else:
        print(f"   ✗ No street cleaning found")
    
    # Show new rules
    print("\n5. NEW RULES ARRAY:")
    print("=" * 80)
    print(json.dumps(new_rules, indent=2, default=str))
    print("=" * 80)
    
    print(f"\n6. Summary:")
    print(f"   Total new rules: {len(new_rules)}")
    for rule in new_rules:
        print(f"   - {rule['type']}: {rule.get('description', 'N/A')}")
    
    # Ask before updating
    print("\n7. Ready to update segment in MongoDB")
    print(f"   This will replace {len(segment.get('rules', []))} rules with {len(new_rules)} rules")
    
    client.close()
    print("\n✓ TEST COMPLETE - No changes made to database")
    print("Review the output above. If correct, run the full repopulation script.")

if __name__ == "__main__":
    asyncio.run(main())