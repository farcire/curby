#!/usr/bin/env python3
"""
Re-run parking regulation matching ONLY.
Skips Steps 1-2.5 (street segments, blockfaces) since they're already in MongoDB.
Only runs Step 3 (parking regulations) with the new supervisor_district optimization.

Use this when you only need to update parking regulation matching without
recreating the entire dataset.
"""
import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict
from shapely.geometry import shape
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from regulation_normalizer import normalize_regulation

# Constants
SFMTA_DOMAIN = "data.sfgov.org"
PARKING_REGULATIONS_ID = "hi6h-neyh"

def map_regulation_type(reg_desc: str) -> str:
    """Maps raw regulation description to internal type."""
    if not reg_desc or not isinstance(reg_desc, str):
        return 'unknown'
    
    reg_desc = reg_desc.lower()
    if 'sweeping' in reg_desc or 'cleaning' in reg_desc:
        return 'street-sweeping'
    if 'tow' in reg_desc:
        return 'tow-away'
    if 'no parking' in reg_desc:
        return 'no-parking'
    if 'time' in reg_desc or 'limit' in reg_desc:
        return 'time-limit'
    if 'permit' in reg_desc or 'residential' in reg_desc:
        return 'rpp-zone'
    return 'parking-regulation'

def match_regulation_to_segment(regulation_geo: Dict, centerline_geo: Dict, segment_side: str, max_distance: float = 0.0005) -> bool:
    """Determines if a parking regulation applies to a specific street segment side."""
    try:
        reg_line = shape(regulation_geo)
        center_line = shape(centerline_geo)
        
        distance = reg_line.distance(center_line)
        if distance > max_distance:
            return False
        
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
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(
        mongodb_uri,
        serverSelectionTimeoutMS=60000,
        connectTimeoutMS=60000,
        socketTimeoutMS=60000
    )
    
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    try:
        await db.command('ping')
        print("✓ Successfully connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        client.close()
        return

    print("\n=== Loading Existing Street Segments from MongoDB ===")
    segments_cursor = db.street_segments.find({})
    all_segments = await segments_cursor.to_list(length=None)
    print(f"✓ Loaded {len(all_segments)} street segments from database")
    
    # Clear existing parking regulation rules from segments
    print("\n=== Clearing Old Parking Regulation Rules ===")
    for segment in all_segments:
        # Keep only non-parking-regulation rules (meters, street cleaning, etc.)
        segment["rules"] = [r for r in segment.get("rules", []) 
                           if r.get("type") not in ['parking-regulation', 'time-limit', 'rpp-zone', 'no-parking', 'tow-away']]
    
    print(f"✓ Cleared parking regulation rules from {len(all_segments)} segments")
    
    print("\n=== Fetching Parking Regulations ===")
    socrata_client = Socrata(SFMTA_DOMAIN, app_token)
    regs = socrata_client.get(PARKING_REGULATIONS_ID, limit=10000)
    regulations_df = pd.DataFrame.from_records(regs)
    print(f"✓ Fetched {len(regulations_df)} parking regulations")
    
    print("\n=== Matching Parking Regulations (OPTIMIZED) ===")
    
    # Build supervisor_district index
    print("  Building supervisor_district index...")
    segments_by_district = {}
    segments_without_district = []
    
    for segment in all_segments:
        district = segment.get('supervisor_district')
        if district and pd.notna(district):
            district_str = str(district).strip()
            if district_str not in segments_by_district:
                segments_by_district[district_str] = []
            segments_by_district[district_str].append(segment)
        else:
            segments_without_district.append(segment)
    
    print(f"  ✓ Indexed {len(segments_by_district)} districts, {len(segments_without_district)} segments without district")
    
    matched_count = 0
    skipped_no_geometry = 0
    skipped_no_match = 0
    total_regs = len(regulations_df)
    
    print(f"  Processing {total_regs} parking regulations...")
    
    for idx, reg_row in regulations_df.iterrows():
        if idx > 0 and idx % 500 == 0:
            print(f"    Progress: {idx}/{total_regs} ({idx/total_regs*100:.1f}%)")
        
        reg_geo = reg_row.get("shape") or reg_row.get("geometry")
        
        if not reg_geo or not isinstance(reg_geo, dict):
            skipped_no_geometry += 1
            continue
        
        # Filter by supervisor_district
        reg_district = reg_row.get('supervisor_district')
        candidate_segments = []
        
        if reg_district and pd.notna(reg_district):
            district_str = str(reg_district).strip()
            districts = [d.strip() for d in district_str.split(',')]
            
            for district in districts:
                candidate_segments.extend(segments_by_district.get(district, []))
            candidate_segments.extend(segments_without_district)
        else:
            candidate_segments = all_segments
        
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
        
        if best_match:
            raw_reg = reg_row.get("regulation", "")
            reg_type = map_regulation_type(raw_reg)
            normalized = normalize_regulation(reg_row.to_dict(), dataset_type='parking_reg')
            
            if normalized['canonical']['is_rpp_72hr']:
                continue

            best_match["rules"].append({
                "type": reg_type,
                "regulation": raw_reg,
                "timeLimit": reg_row.get("hrlimit"),
                "permitArea": reg_row.get("rpparea1") or reg_row.get("rpparea2"),
                "days": reg_row.get("days"),
                "hours": reg_row.get("hours"),
                "fromTime": reg_row.get("from_time"),
                "toTime": reg_row.get("to_time"),
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
                "details": reg_row.get("regdetails"),
                "exceptions": reg_row.get("exceptions"),
                "side": best_match.get("side"),
                "matchConfidence": min(best_score, 1.0)
            })
            matched_count += 1
        else:
            skipped_no_match += 1
    
    print(f"\n✓ Matched {matched_count} parking regulations")
    print(f"  Skipped {skipped_no_geometry} without geometry")
    print(f"  Skipped {skipped_no_match} with no match")
    
    print("\n=== Updating MongoDB ===")
    # Update segments in batches
    chunk_size = 1000
    total = len(all_segments)
    
    for i in range(0, total, chunk_size):
        chunk = all_segments[i:i + chunk_size]
        
        # Update each segment
        for segment in chunk:
            await db.street_segments.update_one(
                {"cnn": segment["cnn"], "side": segment["side"]},
                {"$set": {"rules": segment["rules"]}}
            )
        
        print(f"  Updated segments {i} to {min(i+chunk_size, total)}")
    
    print(f"\n✓ Updated {total} street segments in database")
    
    client.close()
    print("\n✓ Parking Regulation Matching Complete!")

if __name__ == "__main__":
    asyncio.run(main())