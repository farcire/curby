"""
Resumable CNN Segment Ingestion Script with Checkpoints

This script saves progress after each major step, allowing resumption from any checkpoint.
Checkpoints are saved to MongoDB in the 'ingestion_checkpoints' collection.

Usage:
    python ingest_data_cnn_segments_resumable.py [--resume-from STEP]
    
    --resume-from: Optional step number to resume from (1-6)
                   If not provided, starts from beginning or last checkpoint
"""

import os
import asyncio
import argparse
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, LineString, Point, mapping
import math
import re
import sys
import json
from datetime import datetime

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from display_utils import generate_display_messages
from regulation_normalizer import (
    normalize_regulation,
    parse_days,
    parse_time_to_minutes,
    normalize_cap_color,
    aggregate_blockface_cap_colors,
    aggregate_blockface_tow_schedules,
    prioritize_meter_schedules,
    format_segment_for_modal
)
from apply_manual_overrides import apply_manual_overrides_to_segments

# Import all helper functions from original script
from ingest_data_cnn_segments import (
    map_regulation_type,
    get_side_of_street,
    match_regulation_to_segment,
    generate_offset_geometry,
    extract_street_limits,
    fetch_data_as_dataframe,
    match_parking_regulations_to_segments,
    SFMTA_DOMAIN,
    STREETS_DATASET_ID,
    STREET_NODES_ID,
    INTERSECTIONS_DATASET_ID,
    INTERSECTION_PERMUTATIONS_ID,
    BLOCKFACE_GEOMETRY_ID,
    STREET_CLEANING_SCHEDULES_ID,
    PARKING_REGULATIONS_ID,
    METERED_BLOCKFACES_ID,
    METERS_DATASET_ID,
    METER_SCHEDULES_DATASET_ID
)

class IngestionCheckpoint:
    """Manages ingestion checkpoints in MongoDB"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.ingestion_checkpoints
    
    async def save_checkpoint(self, step: int, step_name: str, data: Dict[str, Any]):
        """Save checkpoint to MongoDB"""
        checkpoint = {
            "step": step,
            "step_name": step_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        await self.collection.update_one(
            {"step": step},
            {"$set": checkpoint},
            upsert=True
        )
        print(f"✓ Checkpoint saved: Step {step} - {step_name}")
    
    async def load_checkpoint(self, step: int) -> Optional[Dict[str, Any]]:
        """Load checkpoint from MongoDB"""
        checkpoint = await self.collection.find_one({"step": step})
        if checkpoint:
            print(f"✓ Loaded checkpoint: Step {step} - {checkpoint['step_name']}")
            return checkpoint.get("data")
        return None
    
    async def get_last_checkpoint(self) -> Optional[int]:
        """Get the last completed step"""
        checkpoint = await self.collection.find_one(
            {},
            sort=[("step", -1)]
        )
        if checkpoint:
            return checkpoint["step"]
        return None
    
    async def clear_checkpoints(self):
        """Clear all checkpoints (start fresh)"""
        await self.collection.delete_many({})
        print("✓ Cleared all checkpoints")


async def step1_create_segments(db, app_token, checkpoint_mgr):
    """STEP 1: Load Active Streets & Create Segments"""
    print("\n=== STEP 1: Creating CNN-Based Street Segments ===")
    
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token)
    
    if streets_df.empty:
        raise ValueError("Failed to fetch streets data")
    
    # Save raw collection with batching
    await db.streets.delete_many({})
    
    streets_records = streets_df.to_dict('records')
    chunk_size = 1000
    total_streets = len(streets_records)
    
    for i in range(0, total_streets, chunk_size):
        chunk = streets_records[i:i + chunk_size]
        await db.streets.insert_many(chunk)
        print(f"  Inserted streets {i} to {min(i+chunk_size, total_streets)}")
    
    print(f"✓ Saved {total_streets} streets to raw collection.")
    
    # Create segments
    streets_metadata = {}
    all_segments = []
    
    for _, row in streets_df.iterrows():
        cnn = row.get("cnn")
        if not cnn:
            continue
        
        streets_metadata[cnn] = {
            "streetName": row.get("street_name_gc"),
            "centerlineGeometry": row.get("line"),
            "zip_code": row.get("zip_code"),
            "layer": row.get("layer")
        }
        
        # Create LEFT segment
        left_segment = {
            "cnn": cnn,
            "side": "L",
            "streetName": row.get("street_name_gc"),
            "centerlineGeometry": row.get("line"),
            "blockfaceGeometry": None,
            "rules": [],
            "schedules": [],
            "zip_code": row.get("zip_code"),
            "layer": row.get("layer"),
            "supervisor_district": row.get("supervisor_district"),
            "fromStreet": None,
            "toStreet": None,
            "fromAddress": row.get("lf_fadd"),
            "toAddress": row.get("lf_toadd")
        }
        all_segments.append(left_segment)
        
        # Create RIGHT segment
        right_segment = {
            "cnn": cnn,
            "side": "R",
            "streetName": row.get("street_name_gc"),
            "centerlineGeometry": row.get("line"),
            "blockfaceGeometry": None,
            "rules": [],
            "schedules": [],
            "zip_code": row.get("zip_code"),
            "layer": row.get("layer"),
            "supervisor_district": row.get("supervisor_district"),
            "fromStreet": None,
            "toStreet": None,
            "fromAddress": row.get("rt_fadd"),
            "toAddress": row.get("rt_toadd")
        }
        all_segments.append(right_segment)
    
    print(f"✓ Created {len(all_segments)} street segments (2 per CNN)")
    
    # Save checkpoint
    await checkpoint_mgr.save_checkpoint(1, "segments_created", {
        "total_segments": len(all_segments),
        "total_cnns": len(streets_metadata)
    })
    
    return streets_metadata, all_segments


async def step2_add_blockfaces(db, app_token, checkpoint_mgr, streets_metadata, all_segments):
    """STEP 2: Add Blockface Geometries"""
    print("\n=== STEP 2: Adding Blockface Geometries ===")
    
    geo_df = fetch_data_as_dataframe(BLOCKFACE_GEOMETRY_ID, app_token)
    
    blockface_count = 0
    if not geo_df.empty:
        blockfaces_by_cnn = {}
        for _, row in geo_df.iterrows():
            cnn = row.get("cnn_id")
            bf_geo = row.get("shape")
            
            if not cnn or not bf_geo:
                continue
                
            if cnn not in blockfaces_by_cnn:
                blockfaces_by_cnn[cnn] = []
            blockfaces_by_cnn[cnn].append(bf_geo)
        
        for cnn, geometries in blockfaces_by_cnn.items():
            if cnn not in streets_metadata:
                continue
            
            left_segment = None
            right_segment = None
            for segment in all_segments:
                if segment["cnn"] == cnn:
                    if segment["side"] == "L":
                        left_segment = segment
                    elif segment["side"] == "R":
                        right_segment = segment
            
            centerline_geo = streets_metadata[cnn].get("centerlineGeometry")
            if centerline_geo and len(geometries) > 0:
                for bf_geo in geometries:
                    side = get_side_of_street(centerline_geo, bf_geo)
                    
                    if side == "L" and left_segment and not left_segment.get("blockfaceGeometry"):
                        left_segment["blockfaceGeometry"] = bf_geo
                        blockface_count += 1
                    elif side == "R" and right_segment and not right_segment.get("blockfaceGeometry"):
                        right_segment["blockfaceGeometry"] = bf_geo
                        blockface_count += 1
    
    print(f"✓ Added {blockface_count} blockface geometries")
    
    # Generate synthetic blockfaces
    print("\n=== STEP 2.5: Generating Synthetic Blockfaces ===")
    synthetic_count = 0
    for segment in all_segments:
        if not segment["blockfaceGeometry"] and segment["centerlineGeometry"]:
            synthetic_geo = generate_offset_geometry(
                segment["centerlineGeometry"],
                segment["side"]
            )
            if synthetic_geo:
                segment["blockfaceGeometry"] = synthetic_geo
                synthetic_count += 1
    
    print(f"✓ Generated {synthetic_count} synthetic blockfaces")
    
    await checkpoint_mgr.save_checkpoint(2, "blockfaces_added", {
        "real_blockfaces": blockface_count,
        "synthetic_blockfaces": synthetic_count
    })
    
    return all_segments


async def step3_match_regulations(db, app_token, checkpoint_mgr, all_segments):
    """STEP 3: Match Parking Regulations"""
    print("\n=== STEP 3: Matching Parking Regulations ===")
    
    regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, app_token)
    
    matched_regs = 0
    if not regulations_df.empty:
        await db.parking_regulations.delete_many({})
        
        regs_records = regulations_df.to_dict('records')
        chunk_size = 1000
        total_regs = len(regs_records)
        
        for i in range(0, total_regs, chunk_size):
            chunk = regs_records[i:i + chunk_size]
            await db.parking_regulations.insert_many(chunk)
            print(f"  Inserted parking regulations {i} to {min(i+chunk_size, total_regs)}")
        
        print(f"✓ Saved {total_regs} parking regulations to raw collection.")
        
        try:
            await db.parking_regulations.create_index([("geometry", "2dsphere")])
        except Exception as e:
            print(f"Warning: Could not create index: {e}")
        
        matched_regs = await match_parking_regulations_to_segments(all_segments, regulations_df)
    
    print(f"✓ Matched {matched_regs} parking regulations")
    
    await checkpoint_mgr.save_checkpoint(3, "regulations_matched", {
        "matched_regulations": matched_regs
    })
    
    return all_segments


async def step4_match_meters(db, app_token, checkpoint_mgr, all_segments):
    """STEP 4: Match Parking Meters"""
    print("\n=== STEP 4: Matching Parking Meters ===")
    
    # Load meter schedules
    schedules_df = fetch_data_as_dataframe(METER_SCHEDULES_DATASET_ID, app_token)
    schedules_by_post = {}
    
    if not schedules_df.empty:
        for _, row in schedules_df.iterrows():
            post_id = row.get("post_id")
            if post_id:
                if post_id not in schedules_by_post:
                    schedules_by_post[post_id] = []
                schedules_by_post[post_id].append({
                    "beginTime": row.get("beg_time_dt"),
                    "endTime": row.get("end_time_dt"),
                    "rate": row.get("rate"),
                    "rateQualifier": None,
                    "rateUnit": "per hour",
                    "schedule_type": row.get("schedule_type")
                })
    
    print(f"✓ Loaded {len(schedules_by_post)} meter schedules")
    
    # Load metered blockfaces
    print("Building blockface_id → (CNN, side) lookup...")
    metered_blockfaces_df = fetch_data_as_dataframe(METERED_BLOCKFACES_ID, app_token)
    
    blockface_to_cnn_side = {}
    if not metered_blockfaces_df.empty:
        for _, bf_row in metered_blockfaces_df.iterrows():
            blockface_id = bf_row.get("blockface_id")
            side = bf_row.get("str_seg_orientation")
            street_name = bf_row.get("street_name")
            
            if blockface_id and side:
                blockface_to_cnn_side[str(blockface_id)] = {
                    "side": side,
                    "street_name": street_name,
                    "from_addr": bf_row.get("fm_addr_no"),
                    "to_addr": bf_row.get("to_addr_no")
                }
    
    print(f"✓ Built lookup table with {len(blockface_to_cnn_side)} metered blockface mappings")
    
    # Match meters
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    
    match_stats = {
        "blockface_match": 0,
        "cnn_fallback": 0,
        "failed": 0,
        "total_meters": 0
    }
    
    if not meters_df.empty:
        match_stats["total_meters"] = len(meters_df)
        print(f"Processing {len(meters_df)} parking meters...")
        
        for _, meter_row in meters_df.iterrows():
            cnn = meter_row.get("street_seg_ctrln_id")
            post_id = meter_row.get("post_id")
            blockface_id = meter_row.get("blockface_id")
            
            if not cnn or not post_id:
                match_stats["failed"] += 1
                continue
            
            matched_segment = None
            match_method = None
            
            # METHOD 1: Blockface ID Match
            if blockface_id and str(blockface_id) in blockface_to_cnn_side:
                bf_info = blockface_to_cnn_side[str(blockface_id)]
                target_side = bf_info["side"]
                
                for segment in all_segments:
                    if segment["cnn"] == cnn and segment["side"] == target_side:
                        matched_segment = segment
                        match_method = "blockface_match"
                        break
            
            # METHOD 2: CNN-only fallback
            if not matched_segment:
                street_num = meter_row.get("street_num")
                
                if street_num:
                    try:
                        meter_address = int(re.sub(r'\D', '', str(street_num)))
                        
                        for segment in all_segments:
                            if segment["cnn"] != cnn:
                                continue
                            
                            from_addr = segment.get("fromAddress")
                            to_addr = segment.get("toAddress")
                            
                            if from_addr and to_addr:
                                try:
                                    from_num = int(re.sub(r'\D', '', str(from_addr)))
                                    to_num = int(re.sub(r'\D', '', str(to_addr)))
                                    
                                    if from_num <= meter_address <= to_num:
                                        matched_segment = segment
                                        match_method = "cnn_fallback"
                                        break
                                except:
                                    continue
                    except:
                        pass
            
            # Add meter to segment
            if matched_segment:
                if "meters" not in matched_segment:
                    matched_segment["meters"] = []
                
                cap_color = meter_row.get("cap_color")
                cap_normalized = normalize_cap_color(cap_color)
                
                meter_schedules = schedules_by_post.get(post_id, [])
                prioritized_schedules = prioritize_meter_schedules(meter_schedules)
                
                matched_segment["meters"].append({
                    "post_id": post_id,
                    "cap_color": cap_color,
                    "cap_color_normalized": cap_normalized,
                    "location": {
                        "type": "Point",
                        "coordinates": [
                            float(meter_row.get("longitude", 0)),
                            float(meter_row.get("latitude", 0))
                        ]
                    },
                    "street_num": meter_row.get("street_num"),
                    "blockface_id": blockface_id,
                    "schedules": prioritized_schedules
                })
                
                match_stats[match_method] += 1
            else:
                match_stats["failed"] += 1
    
    print(f"\n✓ Meter Matching Complete!")
    print(f"  Total meters: {match_stats['total_meters']}")
    print(f"  Matched by blockface_id: {match_stats['blockface_match']} ({match_stats['blockface_match']/max(match_stats['total_meters'],1)*100:.1f}%)")
    print(f"  Matched by CNN+address: {match_stats['cnn_fallback']} ({match_stats['cnn_fallback']/max(match_stats['total_meters'],1)*100:.1f}%)")
    print(f"  Failed: {match_stats['failed']} ({match_stats['failed']/max(match_stats['total_meters'],1)*100:.1f}%)")
    print(f"  Success rate: {(match_stats['blockface_match']+match_stats['cnn_fallback'])/max(match_stats['total_meters'],1)*100:.1f}%")
    
    await checkpoint_mgr.save_checkpoint(4, "meters_matched", match_stats)
    
    return all_segments


async def step5_match_sweeping(db, app_token, checkpoint_mgr, all_segments):
    """STEP 5: Match Street Sweeping"""
    print("\n=== STEP 5: Matching Street Sweeping Schedules ===")
    
    sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    
    matched_sweeping = 0
    if not sweeping_df.empty:
        await db.street_cleaning_schedules.delete_many({})
        
        sweeping_records = sweeping_df.to_dict('records')
        chunk_size = 1000
        total_sweeping = len(sweeping_records)
        
        for i in range(0, total_sweeping, chunk_size):
            chunk = sweeping_records[i:i + chunk_size]
            await db.street_cleaning_schedules.insert_many(chunk)
            print(f"  Inserted street cleaning schedules {i} to {min(i+chunk_size, total_sweeping)}")
        
        print(f"✓ Saved {total_sweeping} street cleaning schedules to raw collection.")
        
        for _, row in sweeping_df.iterrows():
            cnn = row.get("cnn")
            side = row.get("cnnrightleft")
            
            if not cnn or not side:
                continue
            
            from_street, to_street = extract_street_limits(row)
            
            for segment in all_segments:
                if segment["cnn"] == cnn and segment["side"] == side:
                    normalized = normalize_regulation(row.to_dict(), dataset_type='street_cleaning')
                    
                    segment["rules"].append({
                        "type": "street-sweeping",
                        "day": row.get("weekday"),
                        "startTime": row.get("fromhour"),
                        "endTime": row.get("tohour"),
                        "activeDays": normalized['canonical']['days'],
                        "startTimeMin": normalized['canonical']['time_start'],
                        "endTimeMin": normalized['canonical']['time_end'],
                        "description": normalized['display']['summary'],
                        "displayDays": normalized['display']['days'],
                        "displayTime": normalized['display']['time'],
                        "blockside": row.get("blockside"),
                        "side": side,
                        "limits": row.get("limits")
                    })
                    
                    if not segment["fromStreet"] and from_street:
                        segment["fromStreet"] = from_street
                    if not segment["toStreet"] and to_street:
                        segment["toStreet"] = to_street
                    
                    matched_sweeping += 1
                    break
    
    print(f"✓ Matched {matched_sweeping} street sweeping schedules")
    
    # Apply manual overrides
    print("\n=== STEP 5.4: Applying Manual Data Overrides ===")
    override_stats = apply_manual_overrides_to_segments(all_segments)
    
    # Aggregate meter rules
    print("\n=== STEP 5.6: Aggregating Blockface Meter Rules ===")
    segments_with_meters = 0
    segments_with_tow = 0
    segments_with_commercial_only = 0
    
    for segment in all_segments:
        if segment.get("meters"):
            segments_with_meters += 1
            
            tow_agg = aggregate_blockface_tow_schedules(segment["meters"])
            segment["towScheduleAggregation"] = tow_agg
            
            if tow_agg['has_tow']:
                segments_with_tow += 1
            
            cap_agg = aggregate_blockface_cap_colors(segment["meters"])
            segment["capColorAggregation"] = cap_agg
            
            if not cap_agg['eligible_for_curby_user']:
                segments_with_commercial_only += 1
            
            segment["hasHomogeneousTow"] = tow_agg['all_have_tow']
            segment["hasHomogeneousCapColor"] = (cap_agg['majority_rule'] in ['ALL_ELIGIBLE', 'ALL_INELIGIBLE'])
            segment["blockfaceRestriction"] = cap_agg['restriction_type']
            segment["eligibleForStandardUser"] = cap_agg['eligible_for_curby_user']
    
    print(f"✓ Aggregated meter rules for {segments_with_meters} metered segments")
    print(f"  - With TOW schedules: {segments_with_tow}")
    print(f"  - Commercial-only: {segments_with_commercial_only}")
    
    # Finalize cardinal direction
    print("\n=== STEP 5.7: Finalizing Cardinal Direction ===")
    for segment in all_segments:
        cardinal = None
        for rule in segment.get("rules", []):
            if rule.get("blockside"):
                raw_cardinal = rule.get("blockside")
                cardinal_str = str(raw_cardinal).strip()
                if cardinal_str.lower() not in ['nan', 'none', 'null', '']:
                    cardinal = cardinal_str
                    break
        
        segment["cardinalDirection"] = cardinal
    
    await checkpoint_mgr.save_checkpoint(5, "sweeping_and_finalization", {
        "matched_sweeping": matched_sweeping,
        "segments_with_meters": segments_with_meters,
        "segments_with_tow": segments_with_tow
    })
    
    return all_segments


async def step6_save_to_db(db, app_token, checkpoint_mgr, all_segments, streets_metadata):
    """STEP 6: Save to Database"""
    print("\n=== STEP 6: Saving to Database ===")
    
    # Save other collections
    nodes_df = fetch_data_as_dataframe(STREET_NODES_ID, app_token)
    if not nodes_df.empty:
        await db.street_nodes.delete_many({})
        nodes_records = nodes_df.to_dict('records')
        chunk_size = 1000
        for i in range(0, len(nodes_records), chunk_size):
            chunk = nodes_records[i:i + chunk_size]
            await db.street_nodes.insert_many(chunk)
        print(f"✓ Saved {len(nodes_records)} street nodes")
    
    intersections_df = fetch_data_as_dataframe(INTERSECTIONS_DATASET_ID, app_token)
    if not intersections_df.empty:
        await db.intersections.delete_many({})
        intersections_records = intersections_df.to_dict('records')
        chunk_size = 1000
        for i in range(0, len(intersections_records), chunk_size):
            chunk = intersections_records[i:i + chunk_size]
            await db.intersections.insert_many(chunk)
        print(f"✓ Saved {len(intersections_records)} intersections")
    
    perms_df = fetch_data_as_dataframe(INTERSECTION_PERMUTATIONS_ID, app_token)
    if not perms_df.empty:
        await db.intersection_permutations.delete_many({})
        perms_records = perms_df.to_dict('records')
        chunk_size = 1000
        for i in range(0, len(perms_records), chunk_size):
            chunk = perms_records[i:i + chunk_size]
            await db.intersection_permutations.insert_many(chunk)
        print(f"✓ Saved {len(perms_records)} intersection permutations")
    
    # Save street segments
    if all_segments:
        await db.street_segments.delete_many({})
        
        chunk_size = 1000
        total = len(all_segments)
        for i in range(0, total, chunk_size):
            chunk = all_segments[i:i + chunk_size]
            await db.street_segments.insert_many(chunk)
            print(f"  Inserted segments {i} to {min(i+chunk_size, total)}")
        
        print("Creating indexes...")
        await db.street_segments.create_index([("cnn", 1), ("side", 1)], unique=True)
        await db.street_segments.create_index([("centerlineGeometry", "2dsphere")])
        
        print(f"✓ Saved {total} street segments to database")
        
        # Statistics
        segments_with_sweeping = sum(1 for s in all_segments if any(r["type"] == "street-sweeping" for r in s.get("rules", [])))
        segments_with_parking = sum(1 for s in all_segments if any(r["type"] == "parking-regulation" for r in s.get("rules", [])))
        segments_with_meters = sum(1 for s in all_segments if s.get("meters"))
        segments_with_blockface = sum(1 for s in all_segments if s.get("blockfaceGeometry"))
        
        print("\n=== Summary ===")
        print(f"Total segments: {total}")
        print(f"  - With street sweeping: {segments_with_sweeping}")
        print(f"  - With parking regulations: {segments_with_parking}")
        print(f"  - With meters: {segments_with_meters}")
        print(f"  - With blockface geometry: {segments_with_blockface}")
        print(f"Coverage: 100% ({total} segments for {len(streets_metadata)} CNNs)")
    
    await checkpoint_mgr.save_checkpoint(6, "saved_to_database", {
        "total_segments": len(all_segments)
    })


async def main():
    """Main resumable ingestion function"""
    parser = argparse.ArgumentParser(description='Resumable CNN Segment Ingestion')
    parser.add_argument('--resume-from', type=int, help='Step number to resume from (1-6)')
    parser.add_argument('--clear-checkpoints', action='store_true', help='Clear all checkpoints and start fresh')
    args = parser.parse_args()
    
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
    
    checkpoint_mgr = IngestionCheckpoint(db)
    
    if args.clear_checkpoints:
        await checkpoint_mgr.clear_checkpoints()
    
    # Determine starting step
    start_step = args.resume_from
    if not start_step:
        last_checkpoint = await checkpoint_mgr.get_last_checkpoint()
        if last_checkpoint:
            print(f"\n✓ Found checkpoint at step {last_checkpoint}")
            start_step = last_checkpoint + 1
        else:
            start_step = 1
    
    print(f"\n=== Starting ingestion from Step {start_step} ===\n")
    
    streets_metadata = None
    all_segments = None
    
    # Execute steps
    if start_step <= 1:
        streets_metadata, all_segments = await step1_create_segments(db, app_token, checkpoint_mgr)
    
    if start_step <= 2:
        if not all_segments:
            # Load from checkpoint
            checkpoint_data = await checkpoint_mgr.load_checkpoint(1)
            if not checkpoint_data:
                raise ValueError("Cannot resume: Step 1 checkpoint not found")
            # Need to reload segments from database or re-run step 1
            print("Re-running Step 1 to load segments...")
            streets_metadata, all_segments = await step1_create_segments(db, app_token, checkpoint_mgr)
        
