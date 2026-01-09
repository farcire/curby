"""
Optimized ingestion script with batching for all large insert operations.
This prevents MongoDB Atlas timeout issues.
"""
import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, LineString, Point, mapping
import math
import re
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from display_utils import generate_display_messages, format_restriction_description
from deterministic_parser import _parse_days, parse_time_to_minutes
from apply_manual_overrides import apply_manual_overrides_to_segments

# Import all functions from the main ingestion script
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

async def batch_insert(collection, records: List[Dict], batch_size: int = 500, collection_name: str = "records"):
    """Insert records in batches to avoid timeouts"""
    total = len(records)
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        await collection.insert_many(batch)
        print(f"  Inserted {collection_name} batch {i+1}-{min(i+batch_size, total)} of {total}")
    print(f"✓ Saved {total} {collection_name}")

async def main():
    """Main function with optimized batching"""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    # Create client with longer timeout settings
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
    
    # Test connection
    try:
        await db.command('ping')
        print("✓ Successfully connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        client.close()
        return

    streets_metadata = {}
    all_segments = []

    # STEP 1: Load Active Streets & Create Segments
    print("\n=== STEP 1: Creating CNN-Based Street Segments ===")
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token)
    
    if not streets_df.empty:
        # Save raw collection with batching
        await db.streets.delete_many({})
        await batch_insert(db.streets, streets_df.to_dict('records'), batch_size=500, collection_name="streets")

        # Create segments for each CNN
        for _, row in streets_df.iterrows():
            cnn = row.get("cnn")
            if not cnn:
                continue
            
            streets_metadata[cnn] = {
                "streetName": row.get("streetname"),
                "centerlineGeometry": row.get("line"),
                "zip_code": row.get("zip_code"),
                "layer": row.get("layer")
            }
            
            # Create LEFT and RIGHT segments
            for side, fadd_key, toadd_key in [("L", "lf_fadd", "lf_toadd"), ("R", "rt_fadd", "rt_toadd")]:
                all_segments.append({
                    "cnn": cnn,
                    "side": side,
                    "streetName": row.get("streetname"),
                    "centerlineGeometry": row.get("line"),
                    "blockfaceGeometry": None,
                    "rules": [],
                    "schedules": [],
                    "zip_code": row.get("zip_code"),
                    "layer": row.get("layer"),
                    "fromStreet": None,
                    "toStreet": None,
                    "fromAddress": row.get(fadd_key),
                    "toAddress": row.get(toadd_key)
                })
        
        print(f"✓ Created {len(all_segments)} street segments (2 per CNN)")

    # STEP 2: Add Blockface Geometries
    print("\n=== STEP 2: Adding Blockface Geometries (where available) ===")
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
    
    print(f"✓ Added {blockface_count} blockface geometries to segments")

    # STEP 2.5: Generate Synthetic Blockfaces
    print("\n=== STEP 2.5: Generating Synthetic Blockfaces ===")
    synthetic_count = 0
    for segment in all_segments:
        if not segment["blockfaceGeometry"] and segment["centerlineGeometry"]:
            synthetic_geo = generate_offset_geometry(segment["centerlineGeometry"], segment["side"])
            if synthetic_geo:
                segment["blockfaceGeometry"] = synthetic_geo
                synthetic_count += 1
    print(f"✓ Generated {synthetic_count} synthetic blockface geometries")

    # STEP 3: Match Street Sweeping
    print("\n=== STEP 3: Matching Street Sweeping Schedules ===")
    sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    
    matched_sweeping = 0
    if not sweeping_df.empty:
        await db.street_cleaning_schedules.delete_many({})
        await batch_insert(db.street_cleaning_schedules, sweeping_df.to_dict('records'), 
                          batch_size=500, collection_name="street_cleaning_schedules")
        
        for _, row in sweeping_df.iterrows():
            cnn = row.get("cnn")
            side = row.get("cnnrightleft")
            if not cnn or not side:
                continue
            
            from_street, to_street = extract_street_limits(row)
            
            for segment in all_segments:
                if segment["cnn"] == cnn and segment["side"] == side:
                    active_days = _parse_days(row.get("weekday"))
                    start_min = parse_time_to_minutes(row.get("fromhour"))
                    end_min = parse_time_to_minutes(row.get("tohour"))
                    description = format_restriction_description(
                        "street-sweeping",
                        day=row.get("weekday"),
                        start_time=row.get("fromhour"),
                        end_time=row.get("tohour")
                    )

                    segment["rules"].append({
                        "type": "street-sweeping",
                        "day": row.get("weekday"),
                        "startTime": row.get("fromhour"),
                        "endTime": row.get("tohour"),
                        "activeDays": active_days,
                        "startTimeMin": start_min,
                        "endTimeMin": end_min,
                        "description": description,
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

    # STEP 4: Match Parking Regulations
    print("\n=== STEP 4: Matching Parking Regulations ===")
    regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, app_token)
    
    matched_regs = 0
    if not regulations_df.empty:
        await db.parking_regulations.delete_many({})
        await batch_insert(db.parking_regulations, regulations_df.to_dict('records'),
                          batch_size=500, collection_name="parking_regulations")
        
        try:
            await db.parking_regulations.create_index([("geometry", "2dsphere")])
        except Exception as e:
            print(f"Warning: Could not create index: {e}")
        
        matched_regs = await match_parking_regulations_to_segments(all_segments, regulations_df)
    
    print(f"✓ Matched {matched_regs} parking regulations")

    # STEP 5: Match Meters
    print("\n=== STEP 5: Matching Parking Meters ===")
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
                    "rateUnit": "per hour"
                })

    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    matched_meters = 0
    if not meters_df.empty:
        for _, row in meters_df.iterrows():
            cnn = row.get("street_seg_ctrln_id")
            post_id = row.get("post_id")
            if not cnn or not post_id:
                continue
            for segment in all_segments:
                if segment["cnn"] == cnn:
                    segment["schedules"].extend(schedules_by_post.get(post_id, []))
                    matched_meters += 1
    
    print(f"✓ Matched {matched_meters} parking meters")

    # STEP 5.4: Apply Manual Data Overrides
    print("\n=== STEP 5.4: Applying Manual Data Overrides ===")
    override_stats = apply_manual_overrides_to_segments(all_segments)

    # STEP 5.5: Finalize Segments
    print("\n=== STEP 5.5: Finalizing Segments ===")
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
        
        parity = None
        if segment.get("fromAddress"):
            try:
                addr_num = int(re.sub(r'\D', '', str(segment["fromAddress"])))
                parity = "even" if addr_num % 2 == 0 else "odd"
            except:
                pass

        msgs = generate_display_messages(
            street_name=segment.get("streetName", ""),
            side_code=segment.get("side", ""),
            cardinal_direction=cardinal,
            from_address=segment.get("fromAddress"),
            to_address=segment.get("toAddress"),
            address_parity=parity
        )
        
        segment["displayName"] = msgs["display_name"]
        segment["displayNameShort"] = msgs["display_name_short"]
        segment["displayAddressRange"] = msgs["display_address_range"]
        segment["displayCardinal"] = msgs["display_cardinal"]

    # STEP 6: Save Everything
    print("\n=== STEP 6: Saving to Database ===")
    
    # Save other collections with batching
    nodes_df = fetch_data_as_dataframe(STREET_NODES_ID, app_token)
    if not nodes_df.empty:
        await db.street_nodes.delete_many({})
        await batch_insert(db.street_nodes, nodes_df.to_dict('records'), 
                          batch_size=500, collection_name="street_nodes")

    intersections_df = fetch_data_as_dataframe(INTERSECTIONS_DATASET_ID, app_token)
    if not intersections_df.empty:
        await db.intersections.delete_many({})
        await batch_insert(db.intersections, intersections_df.to_dict('records'),
                          batch_size=500, collection_name="intersections")

    perms_df = fetch_data_as_dataframe(INTERSECTION_PERMUTATIONS_ID, app_token)
    if not perms_df.empty:
        await db.intersection_permutations.delete_many({})
        await batch_insert(db.intersection_permutations, perms_df.to_dict('records'),
                          batch_size=500, collection_name="intersection_permutations")

    # Save street segments with batching
    if all_segments:
        await db.street_segments.delete_many({})
        await batch_insert(db.street_segments, all_segments, batch_size=500, collection_name="street_segments")
        
        print("Creating indexes...")
        await db.street_segments.create_index([("cnn", 1), ("side", 1)], unique=True)
        await db.street_segments.create_index([("centerlineGeometry", "2dsphere")])
        
        segments_with_sweeping = sum(1 for s in all_segments if any(r["type"] == "street-sweeping" for r in s.get("rules", [])))
        segments_with_parking = sum(1 for s in all_segments if any(r["type"] == "parking-regulation" for r in s.get("rules", [])))
        segments_with_meters = sum(1 for s in all_segments if s.get("schedules"))
        segments_with_blockface = sum(1 for s in all_segments if s.get("blockfaceGeometry"))
        
        print("\n=== Summary ===")
        print(f"Total segments: {len(all_segments)}")
        print(f"  - With street sweeping: {segments_with_sweeping}")
        print(f"  - With parking regulations: {segments_with_parking}")
        print(f"  - With meters: {segments_with_meters}")
        print(f"  - With blockface geometry: {segments_with_blockface}")
    
    client.close()
    print("\n✓ CNN Segment Ingestion Complete!")

if __name__ == "__main__":
    asyncio.run(main())