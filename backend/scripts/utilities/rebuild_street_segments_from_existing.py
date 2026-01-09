#!/usr/bin/env python3
"""
Rebuild street_segments collection using existing raw datasets in MongoDB.
No SFMTA API calls - uses only data already ingested.

This script:
1. Reads from existing MongoDB collections (streets, parking_regulations, etc.)
2. Performs proper joins per CNN Master Dataset Architecture
3. Rebuilds street_segments with correct structure
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import math
from shapely.geometry import shape, LineString
import re

def infer_cardinal_direction(centerline_geo: Dict, side: str) -> Optional[str]:
    """
    Infer cardinal direction from centerline geometry orientation.
    
    Args:
        centerline_geo: GeoJSON LineString
        side: "L" or "R"
    
    Returns:
        Cardinal direction: "N", "S", "E", "W", "NE", "NW", "SE", "SW"
    """
    try:
        line = shape(centerline_geo)
        
        # Get start and end points
        start = line.coords[0]
        end = line.coords[-1]
        
        # Calculate bearing (angle from north)
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # Convert to degrees (0 = North, 90 = East, 180 = South, 270 = West)
        bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360
        
        # Determine cardinal direction based on bearing
        # For LEFT side, add 90 degrees (perpendicular left)
        # For RIGHT side, subtract 90 degrees (perpendicular right)
        if side == "L":
            perpendicular = (bearing + 90) % 360
        else:  # side == "R"
            perpendicular = (bearing - 90) % 360
        
        # Map to cardinal directions
        if 337.5 <= perpendicular or perpendicular < 22.5:
            return "N"
        elif 22.5 <= perpendicular < 67.5:
            return "NE"
        elif 67.5 <= perpendicular < 112.5:
            return "E"
        elif 112.5 <= perpendicular < 157.5:
            return "SE"
        elif 157.5 <= perpendicular < 202.5:
            return "S"
        elif 202.5 <= perpendicular < 247.5:
            return "SW"
        elif 247.5 <= perpendicular < 292.5:
            return "W"
        else:  # 292.5 <= perpendicular < 337.5
            return "NW"
    except Exception as e:
        print(f"Error inferring cardinal direction: {e}")
        return None

def aggregate_street_cleaning(rules: List[Dict]) -> Optional[Dict]:
    """
    Aggregate street cleaning schedules at blockface level.
    Group by time window, aggregate days within each window.
    """
    cleaning_rules = [r for r in rules if r.get("type") == "street-sweeping"]
    
    if not cleaning_rules:
        return None
    
    # Group by time window
    time_windows = {}
    for rule in cleaning_rules:
        start = rule.get("startTime", "")
        end = rule.get("endTime", "")
        time_key = f"{start}-{end}"
        
        if time_key not in time_windows:
            time_windows[time_key] = {
                "rules": [],
                "days": set(),
                "start_time": start,
                "end_time": end
            }
        
        time_windows[time_key]["rules"].append(rule)
        if rule.get("activeDays"):
            time_windows[time_key]["days"].update(rule["activeDays"])
    
    # Build aggregated schedules
    schedules = []
    for time_key, window in time_windows.items():
        schedules.append({
            "days": sorted(list(window["days"])),
            "from_time": window["start_time"],
            "to_time": window["end_time"],
            "display_text": window["rules"][0].get("description", "")
        })
    
    return {
        "has_cleaning": True,
        "schedules": schedules,
        "display_format": "aggregated" if len(schedules) == 1 else "multiple",
        "schedule_count": len(schedules)
    }

def aggregate_non_metered_regulations(rules: List[Dict]) -> Optional[Dict]:
    """
    Aggregate multiple non-metered regulations at blockface level.
    
    Priority Order (Most to Least Restrictive):
    1. No Parking (absolute prohibition)
    2. Government Permit only
    3. Time-limited with RPP exception
    4. Time-limited without RPP
    5. No oversized vehicles (informational)
    """
    reg_types = ["parking-regulation", "time-limit", "rpp-zone", "no-parking"]
    regulations = [r for r in rules if r.get("type") in reg_types]
    
    if not regulations:
        return None
    
    # Sort by priority
    priority_map = {
        "no-parking": 1,
        "government-permit": 2,
        "time-limit": 3,
        "rpp-zone": 4,
        "parking-regulation": 5
    }
    
    regulations.sort(key=lambda r: priority_map.get(r.get("type"), 99))
    
    # Check for RPP
    has_rpp = any(r.get("permitArea") for r in regulations)
    
    return {
        "has_regulations": True,
        "regulations": regulations[:3],  # Max 3 lines
        "primary_regulation": regulations[0].get("description") if regulations else None,
        "regulation_count": len(regulations),
        "has_rpp": has_rpp,
        "rpp_areas": [r.get("permitArea") for r in regulations if r.get("permitArea")]
    }

async def main():
    """Rebuild street_segments from existing MongoDB collections."""
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")
    
    client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=30000)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    # Test connection
    try:
        await db.command('ping')
        print("✓ Successfully connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        client.close()
        return
    
    print("\n=== Rebuilding street_segments from existing data ===\n")
    
    # Step 1: Load existing street_segments to preserve structure
    print("Step 1: Loading existing street_segments...")
    existing_segments = await db.street_segments.find({}).to_list(length=None)
    print(f"✓ Loaded {len(existing_segments)} existing segments")
    
    # Create lookup by (cnn, side)
    segments_by_key = {}
    for seg in existing_segments:
        key = (seg.get("cnn"), seg.get("side"))
        segments_by_key[key] = seg
    
    # Step 2: Load streets collection for additional metadata
    print("\nStep 2: Loading streets metadata...")
    streets_cursor = db.streets.find({})
    streets_by_cnn = {}
    async for street in streets_cursor:
        cnn = street.get("cnn")
        if cnn:
            streets_by_cnn[cnn] = street
    print(f"✓ Loaded {len(streets_by_cnn)} streets")
    
    # Step 3: Enrich segments with missing Active Streets fields
    print("\nStep 3: Enriching with Active Streets metadata...")
    enriched_count = 0
    for key, segment in segments_by_key.items():
        cnn = segment.get("cnn")
        if cnn in streets_by_cnn:
            street = streets_by_cnn[cnn]
            
            # Add missing fields
            if not segment.get("analysis_neighborhood"):
                segment["analysis_neighborhood"] = street.get("analysis_neighborhood")
            
            if not segment.get("street"):
                segment["street"] = street.get("street")
            
            if not segment.get("street_type"):
                segment["street_type"] = street.get("street_type")
            
            # Add f_st/t_st for fromStreet/toStreet fallback
            if not segment.get("fromStreet"):
                segment["fromStreet"] = street.get("f_st")
            
            if not segment.get("toStreet"):
                segment["toStreet"] = street.get("t_st")
            
            enriched_count += 1
    
    print(f"✓ Enriched {enriched_count} segments with Active Streets metadata")
    
    # Step 4: Enhance fromStreet/toStreet from intersections
    print("\nStep 4: Enhancing fromStreet/toStreet from intersections...")
    intersections_cursor = db.intersections.find({})
    intersections_by_cnn = {}
    async for intersection in intersections_cursor:
        cnn = intersection.get("cnn")
        if cnn:
            intersections_by_cnn[cnn] = intersection
    
    enhanced_from = 0
    enhanced_to = 0
    for key, segment in segments_by_key.items():
        cnn = segment.get("cnn")
        if cnn in intersections_by_cnn:
            intersection = intersections_by_cnn[cnn]
            
            # Priority: Use intersection from_st
            from_st = intersection.get("from_st")
            if from_st and not segment.get("fromStreet"):
                segment["fromStreet"] = from_st
                enhanced_from += 1
            
            # Parse limits for toStreet
            limits = intersection.get("limits")
            if limits and not segment.get("toStreet"):
                if "-" in str(limits):
                    parts = str(limits).split("-")
                    if len(parts) == 2:
                        segment["toStreet"] = parts[1].strip()
                        enhanced_to += 1
    
    print(f"✓ Enhanced fromStreet: {enhanced_from} segments")
    print(f"✓ Enhanced toStreet: {enhanced_to} segments")
    
    # Step 5: Infer cardinal direction where missing
    print("\nStep 5: Inferring cardinal directions...")
    inferred_count = 0
    for key, segment in segments_by_key.items():
        if not segment.get("cardinalDirection"):
            centerline = segment.get("centerlineGeometry")
            side = segment.get("side")
            
            if centerline and side:
                cardinal = infer_cardinal_direction(centerline, side)
                if cardinal:
                    segment["cardinalDirection"] = cardinal
                    inferred_count += 1
    
    print(f"✓ Inferred cardinal direction for {inferred_count} segments")
    
    # Step 6: Aggregate street cleaning schedules
    print("\nStep 6: Aggregating street cleaning schedules...")
    cleaning_agg_count = 0
    for key, segment in segments_by_key.items():
        rules = segment.get("rules", [])
        if rules:
            cleaning_agg = aggregate_street_cleaning(rules)
            if cleaning_agg:
                segment["streetCleaningAggregation"] = cleaning_agg
                cleaning_agg_count += 1
    
    print(f"✓ Aggregated street cleaning for {cleaning_agg_count} segments")
    
    # Step 7: Aggregate non-metered regulations
    print("\nStep 7: Aggregating non-metered regulations...")
    reg_agg_count = 0
    for key, segment in segments_by_key.items():
        rules = segment.get("rules", [])
        if rules:
            reg_agg = aggregate_non_metered_regulations(rules)
            if reg_agg:
                segment["nonMeteredRegulationAggregation"] = reg_agg
                reg_agg_count += 1
    
    print(f"✓ Aggregated non-metered regulations for {reg_agg_count} segments")
    
    # Step 8: Populate schedules array from meters
    print("\nStep 8: Populating schedules array...")
    schedules_count = 0
    for key, segment in segments_by_key.items():
        meters = segment.get("meters", [])
        if meters:
            all_schedules = []
            for meter in meters:
                for schedule in meter.get("schedules", []):
                    all_schedules.append({
                        **schedule,
                        "post_id": meter.get("post_id"),
                        "cap_color": meter.get("cap_color")
                    })
            
            if all_schedules:
                segment["schedules"] = all_schedules
                schedules_count += 1
    
    print(f"✓ Populated schedules for {schedules_count} metered segments")
    
    # Step 9: Save updated segments back to MongoDB
    print("\nStep 9: Saving updated segments to MongoDB...")
    
    # Clear existing collection
    await db.street_segments.delete_many({})
    print("✓ Cleared existing street_segments collection")
    
    # Batch insert updated segments
    segments_list = list(segments_by_key.values())
    chunk_size = 100
    total = len(segments_list)
    
    for i in range(0, total, chunk_size):
        chunk = segments_list[i:i + chunk_size]
        await db.street_segments.insert_many(chunk)
        print(f"  Inserted segments {i} to {min(i+chunk_size, total)}")
    
    # Recreate indexes
    print("\nRecreating indexes...")
    await db.street_segments.create_index([("cnn", 1), ("side", 1)], unique=True)
    await db.street_segments.create_index([("centerlineGeometry", "2dsphere")])
    print("✓ Indexes created")
    
    # Step 10: Validation
    print("\n=== Validation ===")
    
    total_segments = len(segments_list)
    
    checks = {
        "fromStreet": sum(1 for s in segments_list if s.get("fromStreet")),
        "toStreet": sum(1 for s in segments_list if s.get("toStreet")),
        "cardinalDirection": sum(1 for s in segments_list if s.get("cardinalDirection")),
        "analysis_neighborhood": sum(1 for s in segments_list if s.get("analysis_neighborhood")),
        "streetCleaningAggregation": sum(1 for s in segments_list if s.get("streetCleaningAggregation")),
        "nonMeteredRegulationAggregation": sum(1 for s in segments_list if s.get("nonMeteredRegulationAggregation")),
        "schedules_populated": sum(1 for s in segments_list if s.get("schedules"))
    }
    
    print(f"\nTotal segments: {total_segments}")
    for field, count in checks.items():
        pct = (count / total_segments * 100) if total_segments > 0 else 0
        print(f"  {field}: {count} ({pct:.1f}%)")
    
    client.close()
    print("\n✓ Rebuild complete!")

if __name__ == "__main__":
    asyncio.run(main())