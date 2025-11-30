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
# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from display_utils import generate_display_messages, format_restriction_description
from deterministic_parser import _parse_days, parse_time_to_minutes

# --- Constants ---
SFMTA_DOMAIN = "data.sfgov.org"

# Dataset IDs (Ordered per instructions)
STREETS_DATASET_ID = "3psu-pn9h"       # 1. Active Streets (Primary Backbone)
STREET_NODES_ID = "vd6w-dq8r"          # 2. Street Nodes
INTERSECTIONS_DATASET_ID = "sw2d-qfup"  # 3. List of Intersections
INTERSECTION_PERMUTATIONS_ID = "jfxm-zeee" # 4. Intersection Permutations
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"    # 5. Blockface Geometries (Link cnn -> blockface_id)
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs" # 6. Street Cleaning Schedules
PARKING_REGULATIONS_ID = "hi6h-neyh"   # 7. Parking Regulations
METERED_BLOCKFACES_ID = "mk27-a5x2"    # 8. Metered Blockfaces (Metadata)
METERS_DATASET_ID = "8vzz-qzz9"        # 9. Parking Meters (Link meters to streets)
METER_SCHEDULES_DATASET_ID = "6cqg-dxku" # 10. Meter Schedules

def map_regulation_type(reg_desc: str) -> str:
    """Maps raw regulation description to internal type."""
    if not reg_desc:
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

def get_side_of_street(centerline_geo: Dict, blockface_geo: Dict) -> str:
    """
    Determines if the blockface geometry is on the Left or Right side of the centerline.
    Returns 'L', 'R', or None if indeterminate.
    """
    try:
        cl_shape = shape(centerline_geo)
        bf_shape = shape(blockface_geo)
        
        if not isinstance(cl_shape, LineString) or not isinstance(bf_shape, LineString):
            return None
            
        # Get midpoint of blockface
        bf_mid = bf_shape.interpolate(0.5, normalized=True)
        
        # Project midpoint onto centerline
        projected_dist = cl_shape.project(bf_mid)
        projected_point = cl_shape.interpolate(projected_dist)
        
        # Get a point slightly further along the centerline to determine tangent vector
        delta = 0.001
        if projected_dist + delta > cl_shape.length:
             p1 = cl_shape.interpolate(projected_dist - delta)
             p2 = projected_point
        else:
             p1 = projected_point
             p2 = cl_shape.interpolate(projected_dist + delta)
             
        # Vector along centerline (tangent)
        cl_vec = (p2.x - p1.x, p2.y - p1.y)
        
        # Vector from centerline to blockface point
        to_bf_vec = (bf_mid.x - projected_point.x, bf_mid.y - projected_point.y)
        
        # Cross product (2D): A x B = Ax*By - Ay*Bx
        cross_product = cl_vec[0] * to_bf_vec[1] - cl_vec[1] * to_bf_vec[0]
        
        return 'L' if cross_product > 0 else 'R'
        
    except Exception as e:
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

def generate_offset_geometry(centerline_geo: Dict, side: str, offset_degrees: float = 0.00005) -> Optional[Dict]:
    """
    Generates a synthetic blockface geometry by offsetting the centerline.
    offset_degrees: 0.00005 is roughly 5 meters
    """
    try:
        cl_shape = shape(centerline_geo)
        
        # parallel_offset only works on LineString
        if not isinstance(cl_shape, LineString):
            return None
            
        # Shapely parallel_offset:
        # side='left' means left of the line direction
        # side='right' means right of the line direction
        
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
        client = Socrata(SFMTA_DOMAIN, app_token)
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
    
    Returns: Number of regulations successfully matched
    """
    matched_count = 0
    skipped_no_geometry = 0
    skipped_no_match = 0
    
    print(f"Processing {len(regulations_df)} parking regulations...")
    
    for idx, reg_row in regulations_df.iterrows():
        reg_geo = reg_row.get("shape") or reg_row.get("geometry")
        
        # Skip if no geometry or if geometry is not a dict (handles NaN/null values)
        if not reg_geo or not isinstance(reg_geo, dict):
            skipped_no_geometry += 1
            continue
        
        # Find closest segment(s) that this regulation could apply to
        best_match = None
        best_score = 0
        
        for segment in segments:
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
            
            active_days = _parse_days(reg_row.get("days"))
            start_min = parse_time_to_minutes(reg_row.get("from_time"))
            end_min = parse_time_to_minutes(reg_row.get("to_time"))
            
            # Parse time limit (convert hours to minutes)
            time_limit_mins = None
            try:
                hr_limit = float(reg_row.get("hrlimit", 0))
                if hr_limit > 0:
                    time_limit_mins = int(hr_limit * 60)
            except:
                pass
                
            description = format_restriction_description(
                reg_type,
                day=reg_row.get("days"),
                start_time=reg_row.get("from_time"),
                end_time=reg_row.get("to_time"),
                time_limit=time_limit_mins,
                permit_area=reg_row.get("rpparea1") or reg_row.get("rpparea2")
            )

            best_match["rules"].append({
                "type": reg_type,
                "regulation": raw_reg,
                "timeLimit": reg_row.get("hrlimit"),
                "permitArea": reg_row.get("rpparea1") or reg_row.get("rpparea2"),
                "days": reg_row.get("days"),
                "hours": reg_row.get("hours"),
                "fromTime": reg_row.get("from_time"),
                "toTime": reg_row.get("to_time"),
                
                # New pre-computed fields
                "activeDays": active_days,
                "startTimeMin": start_min,
                "endTimeMin": end_min,
                "description": description,
                
                "details": reg_row.get("regdetails"),
                "exceptions": reg_row.get("exceptions"),
                "side": best_match.get("side"),
                "matchConfidence": min(best_score, 1.0)  # For debugging
            })
            matched_count += 1
        else:
            skipped_no_match += 1
    
    if skipped_no_geometry > 0:
        print(f"  Skipped {skipped_no_geometry} regulations without geometry")
    if skipped_no_match > 0:
        print(f"  Skipped {skipped_no_match} regulations with no segment match")
    
    return matched_count

async def main():
    """Main function to orchestrate CNN-segment-based data ingestion."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    # Store metadata for enrichment
    streets_metadata = {}
    all_segments = []

    # ==========================================
    # STEP 1: Load Active Streets & Create Segments
    # ==========================================
    print("\n=== STEP 1: Creating CNN-Based Street Segments ===")
    # Fetch ALL San Francisco streets (no zip code filter)
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token)
    
    if not streets_df.empty:
        # Save raw collection
        await db.streets.delete_many({})
        await db.streets.insert_many(streets_df.to_dict('records'))
        print(f"Saved {len(streets_df)} streets to raw collection.")

        # Create segments for each CNN (Left and Right)
        for _, row in streets_df.iterrows():
            cnn = row.get("cnn")
            if not cnn:
                continue
            
            # Store metadata
            streets_metadata[cnn] = {
                "streetName": row.get("streetname"),
                "centerlineGeometry": row.get("line"),
                "zip_code": row.get("zip_code"),
                "layer": row.get("layer")
            }
            
            # Create LEFT segment
            left_segment = {
                "cnn": cnn,
                "side": "L",
                "streetName": row.get("streetname"),
                "centerlineGeometry": row.get("line"),
                "blockfaceGeometry": None,  # Will populate if available
                "rules": [],
                "schedules": [],
                "zip_code": row.get("zip_code"),
                "layer": row.get("layer"),
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
                "streetName": row.get("streetname"),
                "centerlineGeometry": row.get("line"),
                "blockfaceGeometry": None,
                "rules": [],
                "schedules": [],
                "zip_code": row.get("zip_code"),
                "layer": row.get("layer"),
                "fromStreet": None,
                "toStreet": None,
                "fromAddress": row.get("rt_fadd"),  # Right side from address
                "toAddress": row.get("rt_toadd")    # Right side to address
            }
            all_segments.append(right_segment)
        
        print(f"✓ Created {len(all_segments)} street segments (2 per CNN)")
        print(f"  - {len(streets_df)} CNNs × 2 sides = {len(all_segments)} segments")

    # ==========================================
    # STEP 2: Add Blockface Geometries (Optional Enhancement)
    # ==========================================
    print("\n=== STEP 2: Adding Blockface Geometries (where available) ===")
    geo_df = fetch_data_as_dataframe(BLOCKFACE_GEOMETRY_ID, app_token)
    
    blockface_count = 0
    if not geo_df.empty:
        for _, row in geo_df.iterrows():
            cnn = row.get("cnn_id")
            bf_geo = row.get("shape")
            
            if not cnn or not bf_geo or cnn not in streets_metadata:
                continue
            
            # Determine which side this blockface is on
            centerline_geo = streets_metadata[cnn].get("centerlineGeometry")
            if centerline_geo:
                side = get_side_of_street(centerline_geo, bf_geo)
                
                # Find matching segment and add blockface geometry
                for segment in all_segments:
                    if segment["cnn"] == cnn and segment["side"] == side:
                        segment["blockfaceGeometry"] = bf_geo
                        blockface_count += 1
                        break
    
    print(f"✓ Added {blockface_count} blockface geometries to segments")

    # ==========================================
    # STEP 2.5: Generate Synthetic Blockfaces (Offset) for missing ones
    # ==========================================
    print("\n=== STEP 2.5: Generating Synthetic Blockfaces for Missing Geometries ===")
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

    # ==========================================
    # STEP 3: Match Street Sweeping (Direct CNN + Side)
    # ==========================================
    print("\n=== STEP 3: Matching Street Sweeping Schedules ===")
    sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    
    matched_sweeping = 0
    if not sweeping_df.empty:
        await db.street_cleaning_schedules.delete_many({})
        await db.street_cleaning_schedules.insert_many(sweeping_df.to_dict('records'))
        
        for _, row in sweeping_df.iterrows():
            cnn = row.get("cnn")
            side = row.get("cnnrightleft")
            
            if not cnn or not side:
                continue
            
            # Extract street limits
            from_street, to_street = extract_street_limits(row)
            
            # Find matching segment (direct match on CNN + side)
            for segment in all_segments:
                if segment["cnn"] == cnn and segment["side"] == side:
                    # Pre-calculate fields
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
                        # New pre-computed fields
                        "activeDays": active_days,
                        "startTimeMin": start_min,
                        "endTimeMin": end_min,
                        "description": description,
                        "blockside": row.get("blockside"), # Capture cardinal direction
                        
                        "side": side,
                        "limits": row.get("limits")
                    })
                    
                    # Update street limits if not already set
                    if not segment["fromStreet"] and from_street:
                        segment["fromStreet"] = from_street
                    if not segment["toStreet"] and to_street:
                        segment["toStreet"] = to_street
                    
                    matched_sweeping += 1
                    break
    
    print(f"✓ Matched {matched_sweeping} street sweeping schedules")

    # ==========================================
    # STEP 4: Match Parking Regulations (Complex - Spatial + Side)
    # ==========================================
    print("\n=== STEP 4: Matching Parking Regulations (Enhanced Algorithm) ===")
    # Fetch ALL San Francisco parking regulations (no neighborhood filter)
    regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, app_token)
    
    matched_regs = 0
    if not regulations_df.empty:
        await db.parking_regulations.delete_many({})
        await db.parking_regulations.insert_many(regulations_df.to_dict('records'))
        
        # Create geospatial index
        try:
            await db.parking_regulations.create_index([("geometry", "2dsphere")])
        except Exception as e:
            print(f"Warning: Could not create index: {e}")
        
        matched_regs = await match_parking_regulations_to_segments(all_segments, regulations_df)
    
    print(f"✓ Matched {matched_regs} parking regulations")

    # ==========================================
    # STEP 5: Match Meters (CNN + Location)
    # ==========================================
    print("\n=== STEP 5: Matching Parking Meters ===")
    
    # Load meter schedules first
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

    # Match meters to segments
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    matched_meters = 0
    if not meters_df.empty:
        for _, row in meters_df.iterrows():
            cnn = row.get("street_seg_ctrln_id")
            post_id = row.get("post_id")
            
            if not cnn or not post_id:
                continue
            
            # Find segments for this CNN
            # For now, add to both sides (could be refined with location data)
            for segment in all_segments:
                if segment["cnn"] == cnn:
                    segment["schedules"].extend(schedules_by_post.get(post_id, []))
                    matched_meters += 1
    
    print(f"✓ Matched {matched_meters} parking meters")

    # ==========================================
    # STEP 5.5: Finalize Segments (Display Strings & Cardinal)
    # ==========================================
    print("\n=== STEP 5.5: Finalizing Segments ===")
    for segment in all_segments:
        # Determine cardinal direction from rules
        cardinal = None
        for rule in segment.get("rules", []):
            if rule.get("blockside"):
                # Ensure we handle non-string values (e.g. float/nan) safely
                raw_cardinal = rule.get("blockside")
                cardinal_str = str(raw_cardinal).strip()
                if cardinal_str.lower() not in ['nan', 'none', 'null', '']:
                    cardinal = cardinal_str
                    break
        
        segment["cardinalDirection"] = cardinal
        
        # Determine address parity
        parity = None
        if segment.get("fromAddress"):
            try:
                # Basic check: last digit even/odd
                # Or cast to int
                addr_num = int(re.sub(r'\D', '', str(segment["fromAddress"])))
                parity = "even" if addr_num % 2 == 0 else "odd"
            except:
                pass

        # Generate display messages
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

    # ==========================================
    # STEP 6: Save Street Segments to Database
    # ==========================================
    print("\n=== STEP 6: Saving Street Segments to Database ===")
    
    # Save other collections
    nodes_df = fetch_data_as_dataframe(STREET_NODES_ID, app_token)
    if not nodes_df.empty:
        await db.street_nodes.delete_many({})
        await db.street_nodes.insert_many(nodes_df.to_dict('records'))
        print(f"✓ Saved {len(nodes_df)} street nodes")

    intersections_df = fetch_data_as_dataframe(INTERSECTIONS_DATASET_ID, app_token)
    if not intersections_df.empty:
        await db.intersections.delete_many({})
        await db.intersections.insert_many(intersections_df.to_dict('records'))
        print(f"✓ Saved {len(intersections_df)} intersections")

    perms_df = fetch_data_as_dataframe(INTERSECTION_PERMUTATIONS_ID, app_token)
    if not perms_df.empty:
        await db.intersection_permutations.delete_many({})
        await db.intersection_permutations.insert_many(perms_df.to_dict('records'))
        print(f"✓ Saved {len(perms_df)} intersection permutations")

    # Save street segments
    if all_segments:
        await db.street_segments.delete_many({})
        
        # Batch insert
        chunk_size = 1000
        total = len(all_segments)
        for i in range(0, total, chunk_size):
            chunk = all_segments[i:i + chunk_size]
            await db.street_segments.insert_many(chunk)
            print(f"  Inserted segments {i} to {min(i+chunk_size, total)}")
        
        # Create indexes
        print("Creating indexes...")
        await db.street_segments.create_index([("cnn", 1), ("side", 1)], unique=True)
        await db.street_segments.create_index([("centerlineGeometry", "2dsphere")])
        
        print(f"✓ Saved {total} street segments to database")
        
        # Print statistics
        segments_with_sweeping = sum(1 for s in all_segments if any(r["type"] == "street-sweeping" for r in s.get("rules", [])))
        segments_with_parking = sum(1 for s in all_segments if any(r["type"] == "parking-regulation" for r in s.get("rules", [])))
        segments_with_meters = sum(1 for s in all_segments if s.get("schedules"))
        segments_with_blockface = sum(1 for s in all_segments if s.get("blockfaceGeometry"))
        
        print("\n=== Summary ===")
        print(f"Total segments: {total}")
        print(f"  - With street sweeping: {segments_with_sweeping}")
        print(f"  - With parking regulations: {segments_with_parking}")
        print(f"  - With meters: {segments_with_meters}")
        print(f"  - With blockface geometry: {segments_with_blockface}")
        print(f"Coverage: 100% ({total} segments for {len(streets_metadata)} CNNs)")
    else:
        print("ERROR: No segments created!")

    client.close()
    print("\n✓ CNN Segment Ingestion Complete!")

if __name__ == "__main__":
    asyncio.run(main())