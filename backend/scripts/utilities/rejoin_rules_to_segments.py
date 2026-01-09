#!/usr/bin/env python3
"""
Re-join parking regulations and street cleaning to segments with empty rules arrays.
Uses existing data in MongoDB - no need to re-fetch from SFMTA.
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from regulation_normalizer import normalize_regulation
from shapely.geometry import shape, LineString
import pandas as pd

load_dotenv()

def match_regulation_to_segment(regulation_geo: dict, 
                                centerline_geo: dict,
                                segment_side: str,
                                max_distance: float = 0.0005) -> bool:
    """Check if regulation applies to segment side"""
    try:
        reg_line = shape(regulation_geo)
        center_line = shape(centerline_geo)
        
        # Check distance
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
        print(f"Error in match_regulation_to_segment: {e}")
        return False

async def main():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(
        mongodb_uri,
        serverSelectionTimeoutMS=120000,
        connectTimeoutMS=120000,
        socketTimeoutMS=300000
    )
    
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    # Test connection
    try:
        await db.command('ping')
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        client.close()
        return
    
    # Get segments with empty rules
    print("\n=== Finding segments with empty rules ===")
    empty_segments = await db.street_segments.find({'rules': []}).to_list(None)
    print(f"Found {len(empty_segments)} segments with empty rules")
    
    if len(empty_segments) == 0:
        print("✓ All segments already have rules!")
        client.close()
        return
    
    # Build district index for optimization
    print("\n=== Building district index ===")
    segments_by_district = {}
    segments_without_district = []
    
    for segment in empty_segments:
        district = segment.get('supervisor_district')
        if district and pd.notna(district):
            district_str = str(district).strip()
            if district_str not in segments_by_district:
                segments_by_district[district_str] = []
            segments_by_district[district_str].append(segment)
        else:
            segments_without_district.append(segment)
    
    print(f"✓ Indexed {len(segments_by_district)} districts, {len(segments_without_district)} without district")
    
    # Join parking regulations
    print("\n=== Joining parking regulations ===")
    regulations = await db.parking_regulations.find({}).to_list(None)
    print(f"Processing {len(regulations)} parking regulations...")
    
    matched_regs = 0
    for idx, reg in enumerate(regulations):
        if idx > 0 and idx % 500 == 0:
            print(f"  Progress: {idx}/{len(regulations)} ({idx/len(regulations)*100:.1f}%)")
        
        reg_geo = reg.get("shape") or reg.get("geometry")
        if not reg_geo or not isinstance(reg_geo, dict):
            continue
        
        # Get candidate segments by district
        reg_district = reg.get('supervisor_district')
        candidate_segments = []
        
        if reg_district and pd.notna(reg_district):
            district_str = str(reg_district).strip()
            districts = [d.strip() for d in district_str.split(',')]
            for district in districts:
                candidate_segments.extend(segments_by_district.get(district, []))
            candidate_segments.extend(segments_without_district)
        else:
            candidate_segments = empty_segments
        
        # Find best match
        best_match = None
        best_score = 0
        
        for segment in candidate_segments:
            centerline_geo = segment.get("centerlineGeometry")
            if not centerline_geo:
                continue
            
            if match_regulation_to_segment(reg_geo, centerline_geo, segment.get("side")):
                try:
                    reg_line = shape(reg_geo)
                    center_line = shape(centerline_geo)
                    distance = reg_line.distance(center_line)
                    score = 1.0 / (distance + 0.0001)
                    
                    if score > best_score:
                        best_score = score
                        best_match = segment
                except Exception:
                    continue
        
        # Add regulation to segment
        if best_match:
            normalized = normalize_regulation(reg, dataset_type='parking_reg')
            
            # Skip 72hr RPP rules
            if normalized['canonical']['is_rpp_72hr']:
                continue
            
            rule = {
                "type": "parking-regulation",
                "regulation": reg.get("regulation", ""),
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
                "side": best_match.get("side"),
                "matchConfidence": min(best_score, 1.0)
            }
            
            # Update in MongoDB
            await db.street_segments.update_one(
                {"_id": best_match["_id"]},
                {"$push": {"rules": rule}}
            )
            matched_regs += 1
    
    print(f"✓ Matched {matched_regs} parking regulations")
    
    # Join street cleaning
    print("\n=== Joining street cleaning schedules ===")
    sweeping = await db.street_cleaning_schedules.find({}).to_list(None)
    print(f"Processing {len(sweeping)} street cleaning schedules...")
    
    matched_sweeping = 0
    for sweep in sweeping:
        cnn = sweep.get("cnn")
        side = sweep.get("cnnrightleft")
        
        if not cnn or not side:
            continue
        
        # Find matching segment
        segment = await db.street_segments.find_one({"cnn": cnn, "side": side, "rules": []})
        
        if segment:
            normalized = normalize_regulation(sweep, dataset_type='street_cleaning')
            
            rule = {
                "type": "street-sweeping",
                "day": sweep.get("weekday"),
                "startTime": sweep.get("fromhour"),
                "endTime": sweep.get("tohour"),
                "activeDays": normalized['canonical']['days'],
                "startTimeMin": normalized['canonical']['time_start'],
                "endTimeMin": normalized['canonical']['time_end'],
                "description": normalized['display']['summary'],
                "displayDays": normalized['display']['days'],
                "displayTime": normalized['display']['time'],
                "blockside": sweep.get("blockside"),
                "side": side,
                "limits": sweep.get("limits")
            }
            
            # Update in MongoDB
            await db.street_segments.update_one(
                {"_id": segment["_id"]},
                {"$push": {"rules": rule}}
            )
            matched_sweeping += 1
    
    print(f"✓ Matched {matched_sweeping} street cleaning schedules")
    
    # Final stats
    print("\n=== Final Statistics ===")
    total = await db.street_segments.count_documents({})
    with_rules = await db.street_segments.count_documents({'rules': {'$ne': []}})
    empty = await db.street_segments.count_documents({'rules': []})
    
    print(f"Total segments: {total:,}")
    print(f"With rules: {with_rules:,} ({with_rules/total*100:.1f}%)")
    print(f"Still empty: {empty:,} ({empty/total*100:.1f}%)")
    
    client.close()
    print("\n✓ Re-join complete!")

if __name__ == "__main__":
    asyncio.run(main())