"""
Repopulate rules arrays in existing street_segments collection.
Uses existing raw datasets (parking_regulations, street_cleaning_schedules, meters)
to attach rules to segments without re-fetching from SFMTA API.
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from typing import List, Dict
from shapely.geometry import shape, LineString
from regulation_normalizer import normalize_regulation, parse_time_to_minutes
from rule_engine import (
    normalize_cap_color,
    aggregate_blockface_cap_colors,
    aggregate_blockface_tow_schedules,
    prioritize_meter_schedules
)

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
        return False

async def main():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    print("=" * 80)
    print("REPOPULATING STREET SEGMENT RULES")
    print("=" * 80)
    
    # Get all segments
    print("\n1. Loading street segments...")
    segments = await db.street_segments.find({}).to_list(None)
    print(f"   Found {len(segments)} segments")
    
    # Clear existing rules
    print("\n2. Clearing existing rules arrays...")
    await db.street_segments.update_many({}, {"$set": {"rules": []}})
    print("   ✓ Cleared")
    
    # Load raw datasets
    print("\n3. Loading raw datasets...")
    parking_regs = await db.parking_regulations.find({}).to_list(None)
    street_cleaning = await db.street_cleaning_schedules.find({}).to_list(None)
    print(f"   ✓ {len(parking_regs)} parking regulations")
    print(f"   ✓ {len(street_cleaning)} street cleaning schedules")
    
    # Build segment lookup
    segment_lookup = {}
    for seg in segments:
        key = f"{seg['cnn']}_{seg['side']}"
        segment_lookup[key] = seg
    
    # Match parking regulations
    print("\n4. Matching parking regulations...")
    matched_regs = 0
    for idx, reg in enumerate(parking_regs):
        if idx % 500 == 0:
            print(f"   Progress: {idx}/{len(parking_regs)}")
        
        reg_geo = reg.get("shape") or reg.get("geometry")
        if not reg_geo or not isinstance(reg_geo, dict):
            continue
        
        # Find matching segment
        for seg in segments:
            if not seg.get("centerlineGeometry"):
                continue
            
            if match_regulation_to_segment(reg_geo, seg["centerlineGeometry"], seg["side"]):
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
                    "side": seg["side"]
                }
                
                await db.street_segments.update_one(
                    {"_id": seg["_id"]},
                    {"$push": {"rules": rule}}
                )
                matched_regs += 1
                break
    
    print(f"   ✓ Matched {matched_regs} regulations")
    
    # Match street cleaning
    print("\n5. Matching street cleaning schedules...")
    matched_cleaning = 0
    for cleaning in street_cleaning:
        cnn = cleaning.get("cnn")
        side = cleaning.get("cnnrightleft")
        
        if not cnn or not side:
            continue
        
        key = f"{cnn}_{side}"
        if key in segment_lookup:
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
                "side": side,
                "limits": cleaning.get("limits")
            }
            
            await db.street_segments.update_one(
                {"cnn": cnn, "side": side},
                {"$push": {"rules": rule}}
            )
            matched_cleaning += 1
    
    print(f"   ✓ Matched {matched_cleaning} street cleaning schedules")
    
    # Verify
    print("\n6. Verifying...")
    with_rules = await db.street_segments.count_documents({"rules": {"$ne": []}})
    with_sweeping = await db.street_segments.count_documents({"rules.type": "street-sweeping"})
    
    print(f"   ✓ Segments with rules: {with_rules}")
    print(f"   ✓ Segments with street sweeping: {with_sweeping}")
    
    client.close()
    print("\n" + "=" * 80)
    print("✓ REPOPULATION COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())