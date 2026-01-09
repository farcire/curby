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
import argparse
# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from display_utils import generate_display_messages
from src.core.regulation_normalizer import (
    normalize_regulation,
    parse_days,
    parse_time_to_minutes,
    format_segment_for_modal
)
# Import business logic from new rule_engine module (with TOW detection fix)
from rule_engine import (
    normalize_cap_color,
    aggregate_blockface_cap_colors,
    aggregate_blockface_tow_schedules,
    prioritize_meter_schedules
)
from apply_manual_overrides import apply_manual_overrides_to_segments
from ingestion_checkpoint import CheckpointManager, add_checkpoint_args

# --- Constants ---
SFMTA_DOMAIN = "data.sfgov.org"

# Dataset IDs (Ordered per CORRECT architecture)
STREETS_DATASET_ID = "3psu-pn9h"       # 1. Active Streets (Primary Backbone)
STREET_NODES_ID = "vd6w-dq8r"          # 2. Street Nodes
INTERSECTIONS_DATASET_ID = "sw2d-qfup"  # 2. List of Intersections
INTERSECTION_PERMUTATIONS_ID = "jfxm-zeee" # 2. Intersection Permutations
METERS_DATASET_ID = "8vzz-qzz9"        # 3. Parking Meters (BEFORE schedules)
METERED_BLOCKFACES_ID = "mk27-a5x2"    # 4. Metered Blockfaces (Metadata)
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"    # 5. Blockface Geometries
METER_SCHEDULES_DATASET_ID = "6cqg-dxku" # 7. Meter Schedules (AFTER meters)
METER_RATES_DATASET_ID = "fwjv-32uk"   # 8. Meter Rates (NEW)
PARKING_REGULATIONS_ID = "hi6h-neyh"   # 9. Parking Regulations
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs" # 10. Street Cleaning Schedules

def map_regulation_type(reg_desc: str) -> str:
    """
    Maps raw regulation description to internal type.
    
    SEVERITY-BASED REGULATION HIERARCHY:
    - street-sweeping: Severity 3 (Most Severe) - Street-level absolute prohibition
    - metered: Severity 2 - Requires payment (includes TOW/ALTERNATE/OP/PRE+FREE meter schedules)
    - time-limit, rpp-zone, parking-regulation: Severity 1 (Least Severe)
    
    Meter Schedule Priority: TOW > ALTERNATE > OP > PRE+FREE (PRE and FREE equal priority)
    
    Note: TOW and ALTERNATE are meter-specific schedule types, not separate regulations.
    Display logic should always show the most severe active regulation.
    """
    if not reg_desc:
        return 'unknown'
    
    # Handle non-string values (e.g., float/NaN from pandas)
    if not isinstance(reg_desc, str):
        return 'unknown'
    
    reg_desc = reg_desc.lower()
    if 'sweeping' in reg_desc or 'cleaning' in reg_desc:
        return 'street-sweeping'  # Severity 3 - Most severe (street-level)
    if 'tow' in reg_desc:
        return 'tow-away'  # Could be street-level or meter-specific
    if 'no parking' in reg_desc:
        return 'no-parking'
    if 'time' in reg_desc or 'limit' in reg_desc:
        return 'time-limit'  # Severity 1
    if 'permit' in reg_desc or 'residential' in reg_desc:
        return 'rpp-zone'  # Severity 1
    return 'parking-regulation'  # Severity 1

def get_side_of_street(centerline_geo: Dict, blockface_geo: Dict) -> str:
    """
    Determines if the blockface geometry is on the Left or Right side of the centerline.
    Returns 'L', 'R', or None if indeterminate.
    
    Uses multiple sample points along the blockface for robust side determination.
    """
    try:
        cl_shape = shape(centerline_geo)
        bf_shape = shape(blockface_geo)
        
        if not isinstance(cl_shape, LineString) or not isinstance(bf_shape, LineString):
            return None
        
        # Sample multiple points along the blockface for voting
        sample_positions = [0.25, 0.5, 0.75]
        votes = {'L': 0, 'R': 0}
        
        for position in sample_positions:
            # Get point on blockface
            bf_point = bf_shape.interpolate(position, normalized=True)
            
            # Project onto centerline
            projected_dist = cl_shape.project(bf_point)
            projected_point = cl_shape.interpolate(projected_dist)
            
            # Get tangent vector at projected point
            # Use a small delta to calculate direction
            delta = min(0.0001, cl_shape.length * 0.01)  # Adaptive delta
            
            if projected_dist + delta > cl_shape.length:
                # Near end, look backward
                p1 = cl_shape.interpolate(projected_dist - delta)
                p2 = projected_point
            else:
                # Look forward
                p1 = projected_point
                p2 = cl_shape.interpolate(projected_dist + delta)
            
            # Tangent vector along centerline
            tangent = (p2.x - p1.x, p2.y - p1.y)
            
            # Vector from centerline to blockface point
            to_bf = (bf_point.x - projected_point.x, bf_point.y - projected_point.y)
            
            # Cross product: positive = left, negative = right
            # This is the 2D cross product (z-component of 3D cross product)
            cross = tangent[0] * to_bf[1] - tangent[1] * to_bf[0]
            
            if abs(cross) > 1e-10:  # Avoid numerical noise
                if cross > 0:
                    votes['L'] += 1
                else:
                    votes['R'] += 1
        
        # Return side with most votes
        if votes['L'] == 0 and votes['R'] == 0:
            return None
        
        return 'L' if votes['L'] > votes['R'] else 'R'
        
    except Exception as e:
        print(f"Error in get_side_of_street: {e}")
        return None

def match_regulation_to_segment(regulation_geo: Dict, 
                                centerline_geo: Dict,
                                segment_side: str,
                                max_distance: float = 0.0005) -> bool:
    """
    Determines if a parking regulation applies to a specific street segment side.
    Uses multi-point sampling for robust side determination.
    
    Args:
        regulation_geo: GeoJSON geometry of parking regulation line
        centerline_geo: GeoJSON geometry of street centerline
        segment_side: Which side we're checking ("L" or "R")
        max_distance: Maximum distance in degrees (~50 meters)
    
    Returns:
        True if regulation applies to this segment side
    """
    try:
        reg_line = shape(regulation_geo)
        center_line = shape(centerline_geo)
        
        # Step 1: Check if regulation is near this centerline
        distance = reg_line.distance(center_line)
        if distance > max_distance:
            return False  # Too far away
        
        # Step 2: Determine which side the regulation is on
        # Sample multiple points along the regulation line
        sample_points = [0.25, 0.5, 0.75]  # 25%, 50%, 75% along line
        side_votes = {"L": 0, "R": 0}
        
        for position in sample_points:
            reg_point = reg_line.interpolate(position, normalized=True)
            
            # Project onto centerline
            projected_dist = center_line.project(reg_point)
            projected_point = center_line.interpolate(projected_dist)
            
            # Get tangent vector at projected point
            delta = 0.001  # Small step for tangent calculation
            if projected_dist + delta > center_line.length:
                p1 = center_line.interpolate(projected_dist - delta)
                p2 = projected_point
            else:
                p1 = projected_point
                p2 = center_line.interpolate(projected_dist + delta)
            
            # Tangent vector along centerline
            tangent = (p2.x - p1.x, p2.y - p1.y)
            
            # Vector from centerline to regulation point
            to_reg = (reg_point.x - projected_point.x, 
                     reg_point.y - projected_point.y)
            
            # Cross product determines side
            # Positive = Left, Negative = Right
            cross = tangent[0] * to_reg[1] - tangent[1] * to_reg[0]
            
            if cross > 0:
                side_votes["L"] += 1
            elif cross < 0:
                side_votes["R"] += 1
        
        # Step 3: Majority vote determines side
        determined_side = "L" if side_votes["L"] > side_votes["R"] else "R"
        
        # Step 4: Check if matches segment side
        return determined_side == segment_side
        
    except Exception as e:
        print(f"Error in match_regulation_to_segment: {e}")
        return False

def generate_offset_geometry(centerline_geo: Dict, side: str, offset_degrees: float = None) -> Optional[Dict]:
    """
    Generates a synthetic blockface geometry by offsetting the centerline.
    Uses calibrated offsets learned from actual meter locations.
    
    Calibration data (from blockface_offset_calibration.json):
    - Left side (L): median = 5.55 meters (positive offset)
    - Right side (R): median = 5.55 meters (absolute value, negative offset)
    
    offset_degrees: If not provided, uses calibrated values:
    - 0.00005 degrees ≈ 5.55 meters at SF latitude
    """
    try:
        cl_shape = shape(centerline_geo)
        
        # parallel_offset only works on LineString
        if not isinstance(cl_shape, LineString):
            return None
        
        # Use calibrated offset if not provided
        # Calibration shows median offset of 5.55m for both sides
        if offset_degrees is None:
            offset_degrees = 0.00005  # ~5.55 meters, calibrated from meter data
            
        # Shapely parallel_offset:
        # side='left' means left of the line direction (positive offset)
        # side='right' means right of the line direction (negative offset)
        
        if side == 'L':
            offset_shape = cl_shape.parallel_offset(offset_degrees, 'left')
        elif side == 'R':
            offset_shape = cl_shape.parallel_offset(offset_degrees, 'right')
        else:
            return None
            
        if offset_shape.is_empty:
            return None

        # Handling MultiLineString return (can happen with complex offsets or self-intersections)
        if offset_shape.geom_type == 'MultiLineString':
             # Take the longest segment
             offset_shape = max(offset_shape.geoms, key=lambda g: g.length)

        # Ensure direction consistency (fix for potential reversing by parallel_offset)
        # Check if start point of offset is closer to start or end of original
        p1_orig = Point(cl_shape.coords[0])
        p1_off = Point(offset_shape.coords[0])
        p2_orig = Point(cl_shape.coords[-1])
        
        # If start of offset is closer to END of original than START of original, it's reversed
        if p1_off.distance(p1_orig) > p1_off.distance(p2_orig):
            offset_shape = LineString(list(offset_shape.coords)[::-1])
            
        return mapping(offset_shape)
        
    except Exception as e:
        print(f"Error generating offset: {e}")
        return None

def extract_street_limits(sweeping_schedule: Dict) -> tuple:
    """
    Extract FROM/TO street names from sweeping schedule limits.
    Example: "York St  -  Bryant St" -> ("York St", "Bryant St")
    """
    limits = sweeping_schedule.get("limits", "")
    if not limits or "-" not in limits:
        return (None, None)
    
    parts = limits.split("-")
    if len(parts) == 2:
        from_street = parts[0].strip()
        to_street = parts[1].strip()
        return (from_street, to_street)
    
    return (None, None)

def fetch_data_as_dataframe(dataset_id: str, app_token: Optional[str], limit: int = 200000, **kwargs) -> pd.DataFrame:
    """Fetches a dataset and returns it as a pandas DataFrame."""
    print(f"Fetching dataset {dataset_id}...")
    try:
        client = Socrata(SFMTA_DOMAIN, app_token, timeout=60)  # Increased timeout to 60 seconds for large datasets
        results = client.get(dataset_id, limit=limit, **kwargs)
        df = pd.DataFrame.from_records(results)
        print(f"Successfully fetched {len(df)} records from {dataset_id}.")
        return df
    except Exception as e:
        print(f"Error fetching dataset {dataset_id}: {e}")
        return pd.DataFrame()

async def match_parking_regulations_to_segments(segments: List[Dict],
                                                regulations_df: pd.DataFrame) -> int:
    """
    Match parking regulations to street segments using spatial + geometric analysis.
    OPTIMIZED: Uses supervisor_district pre-filtering for 10.6x speedup.
    
    Returns: Number of regulations successfully matched
    """
    matched_count = 0
    skipped_no_geometry = 0
    skipped_no_match = 0
    
    # Track skipped regulation Object IDs for investigation
    skipped_no_geometry_ids = []
    skipped_no_match_ids = []
    
    total_regs = len(regulations_df)
    print(f"Processing {total_regs} parking regulations...")
    
    # OPTIMIZATION: Group segments by supervisor_district for fast lookup
    print("  Building supervisor_district index...")
    segments_by_district = {}
    segments_without_district = []
    
    for segment in segments:
        district = segment.get('supervisor_district')
        if district and pd.notna(district):
            district_str = str(district).strip()
            if district_str not in segments_by_district:
                segments_by_district[district_str] = []
            segments_by_district[district_str].append(segment)
        else:
            segments_without_district.append(segment)
    
    print(f"  ✓ Indexed {len(segments_by_district)} districts, {len(segments_without_district)} segments without district")
    
    for idx, reg_row in regulations_df.iterrows():
        # Progress reporting every 500 regulations
        if idx > 0 and idx % 500 == 0:
            print(f"  Progress: {idx}/{total_regs} regulations processed ({idx/total_regs*100:.1f}%)")
        
        reg_geo = reg_row.get("shape") or reg_row.get("geometry")
        
        # Skip if no geometry or if geometry is not a dict (handles NaN/null values)
        if not reg_geo or not isinstance(reg_geo, dict):
            skipped_no_geometry += 1
            # Save objectid for investigation
            objectid = reg_row.get('objectid')
            if objectid:
                skipped_no_geometry_ids.append(str(objectid))
            continue
        
        # OPTIMIZATION: Filter candidate segments by supervisor_district
        reg_district = reg_row.get('supervisor_district')
        candidate_segments = []
        
        if reg_district and pd.notna(reg_district):
            # Parse multi-district regulations (e.g., "1, 2" → ["1", "2"])
            district_str = str(reg_district).strip()
            districts = [d.strip() for d in district_str.split(',')]
            
            # Get segments from all matching districts
            for district in districts:
                candidate_segments.extend(segments_by_district.get(district, []))
            
            # Also check segments without district (fallback)
            candidate_segments.extend(segments_without_district)
        else:
            # Regulation has no district: check all segments
            candidate_segments = segments
        
        # Find closest segment(s) that this regulation could apply to
        best_match = None
        best_score = 0
        
        for segment in candidate_segments:
            centerline_geo = segment.get("centerlineGeometry")
            if not centerline_geo:
                continue
            
            # Check if regulation matches this segment's side
            if match_regulation_to_segment(
                reg_geo,
                centerline_geo,
                segment.get("side")
            ):
                # Calculate confidence score
                try:
                    reg_line = shape(reg_geo)
                    center_line = shape(centerline_geo)
                    distance = reg_line.distance(center_line)
                    
                    # Closer = higher confidence
                    score = 1.0 / (distance + 0.0001)
                    
                    if score > best_score:
                        best_score = score
                        best_match = segment
                except Exception as e:
                    continue
        
        # Attach regulation to best matching segment
        if best_match:
            # Map type and format description
            raw_reg = reg_row.get("regulation", "")
            reg_type = map_regulation_type(raw_reg)
            
            # Use new regulation normalizer
            normalized = normalize_regulation(reg_row.to_dict(), dataset_type='parking_reg')
            
            # FILTER: Skip 72hr RPP rules (permit-holder only, not relevant for non-permit users)
            # Only filter THIS SPECIFIC RULE, not the entire segment
            if normalized['canonical']['is_rpp_72hr']:
                # Skip this rule - it's for permit holders only
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
                
                # Pre-computed fields from normalizer (day/time)
                "activeDays": normalized['canonical']['days'],
                "startTimeMin": normalized['canonical']['time_start'],
                "endTimeMin": normalized['canonical']['time_end'],
                "description": normalized['display']['summary'],
                "displayDays": normalized['display']['days'],
                "displayTime": normalized['display']['time'],
                
                # Pre-computed fields from normalizer (duration)
                "durationMinutes": normalized['canonical']['duration_minutes'],
                "hasLimit": normalized['canonical']['has_limit'],
                "displayDuration": normalized['display']['duration'],
                "displayDurationLong": normalized['display']['duration_long'],
                
                "details": reg_row.get("regdetails"),
                "exceptions": reg_row.get("exceptions"),
                "side": best_match.get("side"),
                "matchConfidence": min(best_score, 1.0)  # For debugging
            })
            matched_count += 1
        else:
            skipped_no_match += 1
            # Save objectid for investigation
            objectid = reg_row.get('objectid')
            if objectid:
                skipped_no_match_ids.append(str(objectid))
    
    if skipped_no_geometry > 0:
        print(f"  Skipped {skipped_no_geometry} regulations without geometry")
        print(f"  Object IDs (no geometry): {', '.join(skipped_no_geometry_ids)}")
    if skipped_no_match > 0:
        print(f"  Skipped {skipped_no_match} regulations with no segment match")
        print(f"  Object IDs (no match): {', '.join(skipped_no_match_ids)}")
    
    # Save IDs to file for easy reference
    if skipped_no_geometry_ids or skipped_no_match_ids:
        with open('skipped_regulation_ids.txt', 'w') as f:
            f.write("REGULATIONS WITHOUT GEOMETRY:\n")
            f.write("=" * 50 + "\n")
            for oid in skipped_no_geometry_ids:
                f.write(f"{oid}\n")
            f.write("\n")
            f.write("REGULATIONS WITH NO SEGMENT MATCH:\n")
            f.write("=" * 50 + "\n")
            for oid in skipped_no_match_ids:
                f.write(f"{oid}\n")
        print(f"  ✓ Saved skipped regulation IDs to skipped_regulation_ids.txt")
    
    return matched_count

async def main(resume: bool = True, resume_from: str = None, force_restart: bool = False):
    """Main function to orchestrate CNN-segment-based data ingestion with checkpoint support."""
    print("🚀 Starting ingestion script...")
    print("📂 Loading environment variables...")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")
    print(f"✓ Environment loaded (MongoDB URI: {'present' if mongodb_uri else 'MISSING'})")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    # Initialize checkpoint manager
    print("📋 Initializing checkpoint manager...")
    checkpoint = CheckpointManager(checkpoint_dir=os.path.dirname(os.path.abspath(__file__)))
    
    # Handle checkpoint loading
    checkpoint_data = None
    start_step = "1"
    
    if force_restart:
        print("\n🔄 Force restart requested - clearing checkpoint and starting fresh")
        checkpoint.clear()
    elif resume_from:
        print(f"\n🔄 Resuming from step {resume_from} (ignoring checkpoint)")
        start_step = resume_from
    elif resume and checkpoint.exists():
        print("\n📂 Loading checkpoint...")
        checkpoint_data = checkpoint.load()
        if checkpoint_data:
            start_step = checkpoint_data['next_step']
            print(f"✓ Will resume from step {start_step}")
        else:
            print("⚠️  Failed to load checkpoint, starting fresh")
    else:
        print("\n🆕 Starting fresh ingestion (no checkpoint)")

    # Create client with longer timeout settings for large uploads
    print("🔌 Creating MongoDB client...")
    client = motor.motor_asyncio.AsyncIOMotorClient(
        mongodb_uri,
        serverSelectionTimeoutMS=120000,  # 120 seconds
        connectTimeoutMS=120000,  # 120 seconds
        socketTimeoutMS=300000  # 300 seconds (5 minutes) for large batch operations
    )
    print("✓ MongoDB client created")
    
    print("🗄️  Getting database reference...")
    try:
        db = client.get_default_database()
        print("✓ Using default database")
    except Exception:
        db = client["curby"]
        print("✓ Using 'curby' database")
    
    # Test connection
    print("🔍 Testing MongoDB connection...")
    try:
        await db.command('ping')
        print("✓ Successfully connected to MongoDB")
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        print("Please check your network connection and MongoDB Atlas settings.")
        client.close()
        return

    # Store metadata for enrichment
    print("📊 Initializing data structures...")
    streets_metadata = {}
    all_segments = []
    
    # Load from checkpoint if available
    if checkpoint_data:
        print("📦 Loading data from checkpoint...")
        all_segments = checkpoint_data.get('all_segments', [])
        streets_metadata = checkpoint_data.get('streets_metadata', {})
        print(f"✓ Loaded {len(all_segments)} segments from checkpoint")

    # ==========================================
    # STEP 1: Load Active Streets & Create Segments
    # ==========================================
    if start_step <= "1":
        print("\n=== STEP 1: Creating CNN-Based Street Segments ===")
        # Fetch ALL San Francisco streets (no zip code filter)
        streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token)
    else:
        print("\n=== STEP 1: Skipping (already completed) ===")
        streets_df = pd.DataFrame()
    
    if not streets_df.empty:
        # Save raw collection with batching
        await db.streets.delete_many({})
        
        # Batch insert to avoid timeout on large datasets
        streets_records = streets_df.to_dict('records')
        chunk_size = 1000
        total_streets = len(streets_records)
        
        for i in range(0, total_streets, chunk_size):
            chunk = streets_records[i:i + chunk_size]
            await db.streets.insert_many(chunk)
            print(f"  Inserted streets {i} to {min(i+chunk_size, total_streets)}")
        
        print(f"✓ Saved {total_streets} streets to raw collection.")

        # Create segments for each CNN (Left and Right)
        for _, row in streets_df.iterrows():
            cnn = row.get("cnn")
            if not cnn:
                continue
            
            # Store metadata
            streets_metadata[cnn] = {
                "streetName": row.get("streetname_gc"),
                "centerlineGeometry": row.get("line"),
                "zip_code": row.get("zip_code"),
                "layer": row.get("layer")
            }
            
            # Create LEFT segment
            left_segment = {
                "cnn": cnn,
                "side": "L",
                "streetName": row.get("streetname_gc"),
                "centerlineGeometry": row.get("line"),
                "blockfaceGeometry": None,  # Will populate if available
                "rules": [],
                "schedules": [],
                "zip_code": row.get("zip_code"),
                "layer": row.get("layer"),
                "supervisor_district": row.get("supervisor_district"),
                "fromStreet": None,
                "toStreet": None,
                "fromAddress": row.get("lf_fadd"),  # Left side from address
                "toAddress": row.get("lf_toadd")    # Left side to address
            }
            all_segments.append(left_segment)
            
            # Create RIGHT segment
            right_segment = {
                "cnn": cnn,
                "side": "R",
                "streetName": row.get("streetname_gc"),
                "centerlineGeometry": row.get("line"),
                "blockfaceGeometry": None,
                "rules": [],
                "schedules": [],
                "zip_code": row.get("zip_code"),
                "layer": row.get("layer"),
                "supervisor_district": row.get("supervisor_district"),
                "fromStreet": None,
                "toStreet": None,
                "fromAddress": row.get("rt_fadd"),  # Right side from address
                "toAddress": row.get("rt_toadd")    # Right side to address
            }
            all_segments.append(right_segment)
        
        print(f"✓ Created {len(all_segments)} street segments (2 per CNN)")
        print(f"  - {len(streets_df)} CNNs × 2 sides = {len(all_segments)} segments")
        
        # Save checkpoint after Step 1
        checkpoint.save("1", all_segments, streets_metadata, {"segments_created": len(all_segments)})

    # ==========================================
    # STEP 2: Add Intersections & Permutations
    # ==========================================
    if start_step <= "2":
        print("\n=== STEP 2: Adding Intersections & Permutations ===")
        
        # Save street nodes
        nodes_df = fetch_data_as_dataframe(STREET_NODES_ID, app_token)
        if not nodes_df.empty:
            await db.street_nodes.delete_many({})
            
            # Batch insert street nodes
            nodes_records = nodes_df.to_dict('records')
            chunk_size = 1000
            total_nodes = len(nodes_records)
            
            for i in range(0, total_nodes, chunk_size):
                chunk = nodes_records[i:i + chunk_size]
                await db.street_nodes.insert_many(chunk)
            
            print(f"✓ Saved {total_nodes} street nodes")

        # Save intersections
        intersections_df = fetch_data_as_dataframe(INTERSECTIONS_DATASET_ID, app_token)
        if not intersections_df.empty:
            await db.intersections.delete_many({})
            
            # Batch insert intersections
            intersections_records = intersections_df.to_dict('records')
            chunk_size = 1000
            total_intersections = len(intersections_records)
            
            for i in range(0, total_intersections, chunk_size):
                chunk = intersections_records[i:i + chunk_size]
                await db.intersections.insert_many(chunk)
            
            print(f"✓ Saved {total_intersections} intersections")

        # Save intersection permutations
        perms_df = fetch_data_as_dataframe(INTERSECTION_PERMUTATIONS_ID, app_token)
        if not perms_df.empty:
            await db.intersection_permutations.delete_many({})
            
            # Batch insert intersection permutations
            perms_records = perms_df.to_dict('records')
            chunk_size = 1000
            total_perms = len(perms_records)
            
            for i in range(0, total_perms, chunk_size):
                chunk = perms_records[i:i + chunk_size]
                await db.intersection_permutations.insert_many(chunk)
            
            print(f"✓ Saved {total_perms} intersection permutations")
        
        # Save checkpoint after Step 2
        checkpoint.save("2", all_segments, streets_metadata, {
            "nodes": len(nodes_df) if not nodes_df.empty else 0,
            "intersections": len(intersections_df) if not intersections_df.empty else 0,
            "permutations": len(perms_df) if not perms_df.empty else 0
        })
    else:
        print("\n=== STEP 2: Skipping (already completed) ===")

    # ==========================================
    # STEP 3: Match Parking Meters (WITHOUT schedules)
    # CRITICAL FIX: Load meters FIRST, schedules come later in Step 6
    # ==========================================
    if start_step <= "3":
        print("\n=== STEP 3: Matching Parking Meters (WITHOUT schedules) ===")
        
        # Load metered blockfaces to get blockface_id → (CNN, side) mapping
        print("Building blockface_id → (CNN, side) lookup from metered blockfaces...")
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
        
        # Match meters to segments using blockface_id
        meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
        
        if not meters_df.empty:
            await db.meters.delete_many({})
            
            meters_records = meters_df.to_dict('records')
            chunk_size = 1000
            total_meters_raw = len(meters_records)
            
            for i in range(0, total_meters_raw, chunk_size):
                chunk = meters_records[i:i + chunk_size]
                await db.meters.insert_many(chunk)
                print(f"  Inserted meters {i} to {min(i+chunk_size, total_meters_raw)}")
            
            print(f"✓ Saved {total_meters_raw} meters to raw collection.")
        
        match_stats = {
            "blockface_match": 0,
            "cnn_fallback": 0,
            "failed": 0,
            "total_meters": 0
        }
        
        if not meters_df.empty:
            match_stats["total_meters"] = len(meters_df)
            print(f"Processing {len(meters_df)} parking meters...")
            
            for idx, meter_row in meters_df.iterrows():
                if idx > 0 and idx % 5000 == 0:
                    print(f"  Progress: {idx}/{len(meters_df)} meters processed ({idx/len(meters_df)*100:.1f}%)")
                
                cnn = meter_row.get("street_seg_ctrln_id")
                post_id = meter_row.get("post_id")
                blockface_id = meter_row.get("blockface_id")
                
                if not cnn or not post_id:
                    match_stats["failed"] += 1
                    continue
                
                matched_segment = None
                match_method = None
                
                # METHOD 1: Blockface ID Match (Primary)
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
                
                # Add meter to matched segment (WITHOUT schedules)
                if matched_segment:
                    if "meters" not in matched_segment:
                        matched_segment["meters"] = []
                    
                    cap_color = meter_row.get("cap_color")
                    cap_normalized = normalize_cap_color(cap_color)
                    
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
                        "schedules": []  # Empty - will be populated in Step 6
                    })
                    
                    match_stats[match_method] += 1
                else:
                    match_stats["failed"] += 1
        
        print(f"\n✓ Meter Matching Complete!")
        print(f"  Total meters processed: {match_stats['total_meters']}")
        print(f"  Matched by blockface_id: {match_stats['blockface_match']} ({match_stats['blockface_match']/max(match_stats['total_meters'],1)*100:.1f}%)")
        print(f"  Matched by CNN+address fallback: {match_stats['cnn_fallback']} ({match_stats['cnn_fallback']/max(match_stats['total_meters'],1)*100:.1f}%)")
        print(f"  Failed to match: {match_stats['failed']} ({match_stats['failed']/max(match_stats['total_meters'],1)*100:.1f}%)")
        
        checkpoint.save("3", all_segments, streets_metadata, {"meter_stats": match_stats})
    else:
        print("\n=== STEP 3: Skipping (already completed) ===")

    # ==========================================
    # STEP 4: Add Blockface Geometries with Meters (Direct CNN Matching)
    # ==========================================
    if start_step <= "4":
        print("\n=== STEP 4: Adding Blockface Geometries (where available) ===")
        geo_df = fetch_data_as_dataframe(BLOCKFACE_GEOMETRY_ID, app_token)
    else:
        print("\n=== STEP 4: Skipping (already completed) ===")
        geo_df = pd.DataFrame()
    
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
    checkpoint.save("4", all_segments, streets_metadata, {"blockface_count": blockface_count})

    # ==========================================
    # STEP 5: Generate Synthetic Blockfaces (Offset) for missing ones
    # ==========================================
    if start_step <= "5":
        print("\n=== STEP 5: Generating Synthetic Blockfaces for Missing Geometries ===")
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
        
        print(f"✓ Generated {synthetic_count} synthetic blockface geometries")
        checkpoint.save("5", all_segments, streets_metadata, {"synthetic_count": synthetic_count})
    else:
        print("\n=== STEP 5: Skipping (already completed) ===")

    # ==========================================
    # STEP 6: Attach Meter Schedules TO Meters
    # CRITICAL FIX: Schedules loaded AFTER meters and attached via post_id
    # ==========================================
    if start_step <= "6":
        print("\n=== STEP 6: Attaching Meter Schedules TO Meters ===")
        
        schedules_df = fetch_data_as_dataframe(METER_SCHEDULES_DATASET_ID, app_token)
        
        schedules_by_post = {}
        schedule_diagnostics = {
            "total_schedule_records": 0,
            "unique_post_ids": 0,
            "schedules_with_all_fields": 0,
            "schedules_missing_fields": 0
        }
        
        if not schedules_df.empty:
            await db.meter_schedules.delete_many({})
            
            schedules_records = schedules_df.to_dict('records')
            chunk_size = 1000
            total_schedules = len(schedules_records)
            schedule_diagnostics["total_schedule_records"] = total_schedules
            
            for i in range(0, total_schedules, chunk_size):
                chunk = schedules_records[i:i + chunk_size]
                await db.meter_schedules.insert_many(chunk)
                print(f"  Inserted meter schedules {i} to {min(i+chunk_size, total_schedules)}")
            
            print(f"✓ Saved {total_schedules} meter schedules to raw collection.")
            
            # Build lookup dictionary
            for idx, row in schedules_df.iterrows():
                post_id = row.get("post_id")
                if post_id:
                    if post_id not in schedules_by_post:
                        schedules_by_post[post_id] = []
                    
                    schedule_entry = {
                        "days_applied": row.get("days_applied"),
                        "from_time": row.get("from_time"),
                        "to_time": row.get("to_time"),
                        "time_limit": row.get("time_limit"),
                        "schedule_type": row.get("schedule_type"),
                        "cap_color": row.get("cap_color"),
                        "priority": row.get("priority"),
                        "block_side": row.get("block_side")
                    }
                    schedules_by_post[post_id].append(schedule_entry)
                    
                    if all([row.get("days_applied"), row.get("from_time"), row.get("to_time"), row.get("schedule_type")]):
                        schedule_diagnostics["schedules_with_all_fields"] += 1
                    else:
                        schedule_diagnostics["schedules_missing_fields"] += 1
            
            schedule_diagnostics["unique_post_ids"] = len(schedules_by_post)
        
        print(f"✓ Loaded {len(schedules_by_post)} unique post IDs with schedules")
        
        # Attach schedules to meters
        meters_with_schedules = 0
        meters_without_schedules = 0
        
        for segment in all_segments:
            if segment.get("meters"):
                for meter in segment["meters"]:
                    post_id = meter.get("post_id")
                    if post_id and post_id in schedules_by_post:
                        meter_schedules = schedules_by_post[post_id]
                        prioritized_schedules = prioritize_meter_schedules(meter_schedules)
                        meter["schedules"] = prioritized_schedules
                        meters_with_schedules += 1
                    else:
                        meters_without_schedules += 1
        
        print(f"  Meters WITH schedules: {meters_with_schedules}")
        print(f"  Meters WITHOUT schedules: {meters_without_schedules}")
        
        checkpoint.save("6", all_segments, streets_metadata, {
            "schedule_diagnostics": schedule_diagnostics,
            "meters_with_schedules": meters_with_schedules,
            "meters_without_schedules": meters_without_schedules
        })
    else:
        print("\n=== STEP 6: Skipping (already completed) ===")

    # ==========================================
    # STEP 7: Match Parking Regulations (Non-Metered)
    # ==========================================
    if start_step <= "7":
        print("\n=== STEP 7: Matching Parking Regulations (Non-Metered Parking Availability) ===")
        regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, app_token)
    else:
        print("\n=== STEP 7: Skipping (already completed) ===")
        regulations_df = pd.DataFrame()
    
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
    checkpoint.save("7", all_segments, streets_metadata, {"matched_regulations": matched_regs})

    # ==========================================
    # STEP 8: Match Street Sweeping (Direct CNN + Side)
    # ==========================================
    if start_step <= "8":
        print("\n=== STEP 8: Matching Street Sweeping Schedules (Absolute Prohibition) ===")
        sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    else:
        print("\n=== STEP 8: Skipping (already completed) ===")
        sweeping_df = pd.DataFrame()
    
    matched_sweeping = 0
    if not sweeping_df.empty:
        # Try to delete existing records, but continue if it times out
        try:
            await db.street_cleaning_schedules.delete_many({})
            print("✓ Cleared existing street cleaning schedules")
        except Exception as e:
            print(f"⚠️  Warning: Could not clear existing schedules (continuing anyway): {str(e)[:100]}")
        
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
    checkpoint.save("8", all_segments, streets_metadata, {"matched_sweeping": matched_sweeping})

    # ==========================================
    # STEP 9: Apply Manual Data Overrides
    # ==========================================
    if start_step <= "9":
        print("\n=== STEP 9: Applying Manual Data Overrides ===")
        override_stats = apply_manual_overrides_to_segments(all_segments)
        checkpoint.save("9", all_segments, streets_metadata, {"override_stats": override_stats})
    else:
        print("\n=== STEP 9: Skipping (already completed) ===")
    
    # ==========================================
    # STEP 10: Aggregate Blockface-Level Meter Rules
    # ==========================================
    if start_step <= "10":
        print("\n=== STEP 10: Aggregating Blockface Meter Rules ===")
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
        print(f"  - Segments with TOW schedules: {segments_with_tow}")
        print(f"  - Segments commercial-only: {segments_with_commercial_only}")
        checkpoint.save("10", all_segments, streets_metadata, {
            "segments_with_meters": segments_with_meters,
            "segments_with_tow": segments_with_tow,
            "segments_commercial_only": segments_with_commercial_only
        })
    else:
        print("\n=== STEP 10: Skipping (already completed) ===")
    
    # ==========================================
    # STEP 11: Finalize Cardinal Direction
    # ==========================================
    if start_step <= "11":
        print("\n=== STEP 11: Finalizing Cardinal Direction ===")
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
        checkpoint.save("11", all_segments, streets_metadata, {})
    else:
        print("\n=== STEP 11: Skipping (already completed) ===")

    # ==========================================
    # STEP 12: Save Street Segments to Database
    # ==========================================
    if start_step <= "12":
        print("\n=== STEP 12: Saving Street Segments to Database ===")
    else:
        print("\n=== STEP 12: Skipping (already completed) ===")
        client.close()
        print("\n✓ CNN Segment Ingestion Complete!")
        return
    
    # Save street segments
    if all_segments:
        await db.street_segments.delete_many({})
        
        chunk_size = 100
        total = len(all_segments)
        max_retries = 3
        
        for i in range(0, total, chunk_size):
            chunk = all_segments[i:i + chunk_size]
            
            for attempt in range(max_retries):
                try:
                    await db.street_segments.insert_many(chunk)
                    print(f"  Inserted segments {i} to {min(i+chunk_size, total)}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️  Retry {attempt + 1}/{max_retries} for batch {i}-{min(i+chunk_size, total)}: {str(e)[:100]}")
                        await asyncio.sleep(2 ** attempt)
                    else:
                        print(f"  ❌ Failed to insert batch {i}-{min(i+chunk_size, total)} after {max_retries} attempts")
                        raise
        
        print("Creating indexes...")
        await db.street_segments.create_index([("cnn", 1), ("side", 1)], unique=True)
        await db.street_segments.create_index([("centerlineGeometry", "2dsphere")])
        
        print(f"✓ Saved {total} street segments to database")
        
        # Print statistics
        segments_with_sweeping = sum(1 for s in all_segments if any(r["type"] == "street-sweeping" for r in s.get("rules", [])))
        segments_with_parking = sum(1 for s in all_segments if any(r["type"] == "parking-regulation" for r in s.get("rules", [])))
        segments_with_meters = sum(1 for s in all_segments if s.get("meters"))
        segments_with_blockface = sum(1 for s in all_segments if s.get("blockfaceGeometry"))
        segments_commercial_only = sum(1 for s in all_segments if not s.get("eligibleForStandardUser", True) and s.get("meters"))
        segments_with_tow_agg = sum(1 for s in all_segments if s.get("towScheduleAggregation", {}).get("has_tow", False))
        
        print("\n=== Summary ===")
        print(f"Total segments: {total}")
        print(f"  - With street sweeping: {segments_with_sweeping}")
        print(f"  - With parking regulations: {segments_with_parking}")
        print(f"  - With meters: {segments_with_meters}")
        print(f"    • Commercial vehicles only: {segments_commercial_only}")
        print(f"    • With TOW schedules: {segments_with_tow_agg}")
        print(f"    • Standard parking available: {segments_with_meters - segments_commercial_only}")
        print(f"  - With blockface geometry: {segments_with_blockface}")
        print(f"Coverage: 100% ({total} segments for {len(streets_metadata)} CNNs)")
    else:
        print("ERROR: No segments created!")

    client.close()
    print("\n✓ CNN Segment Ingestion Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest CNN-based street segments with checkpoint support (REFACTORED V2)")
    add_checkpoint_args(parser)
    args = parser.parse_args()
    
    checkpoint = CheckpointManager(checkpoint_dir=os.path.dirname(os.path.abspath(__file__)))
    
    if args.checkpoint_info:
        info = checkpoint.get_info()
        if info:
            print("Checkpoint Info:")
            print(f"  Last completed step: {info.get('last_completed_step')}")
            print(f"  Next step: {info.get('next_step')}")
            print(f"  Timestamp: {info.get('timestamp')}")
            print(f"  Segment count: {info.get('segment_count')}")
        else:
            print("No checkpoint found")
        sys.exit(0)
    
    if args.clear_checkpoint:
        checkpoint.clear()
        sys.exit(0)
    
    asyncio.run(main(
        resume=args.resume,
        resume_from=args.resume_from,
        force_restart=args.force_restart
    ))
