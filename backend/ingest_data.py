import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, LineString, Point
import math

# --- Constants ---
SFMTA_DOMAIN = "data.sfgov.org"

# Dataset IDs (Ordered per instructions)
STREETS_DATASET_ID = "3psu-pn9h"       # 1. Active Streets (Primary Backbone + Address Ranges)
STREET_NODES_ID = "vd6w-dq8r"          # 2. Street Nodes
INTERSECTIONS_DATASET_ID = "sw2d-qfup"  # 3. List of Intersections
INTERSECTION_PERMUTATIONS_ID = "jfxm-zeee" # 4. Intersection Permutations
RPP_PARCELS_ID = "i886-hxz9"           # 4.5 RPP Eligibility Parcels (Address-based RPP matching)
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"    # 5. Blockface Geometries (Link cnn -> blockface_id)
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs" # 6. Street Cleaning Schedules
PARKING_REGULATIONS_ID = "hi6h-neyh"   # 7. Parking Regulations (Geometric fallback)
METERED_BLOCKFACES_ID = "mk27-a5x2"    # 8. Metered Blockfaces (Metadata)
METERS_DATASET_ID = "8vzz-qzz9"        # 9. Parking Meters (Link meters to streets)
METER_SCHEDULES_DATASET_ID = "6cqg-dxku" # 10. Meter Schedules

# --- Data Models ---
Blockface = Dict[str, Any]

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
        # Handle edge case where projection is at the very end
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
        # If > 0, point is to the Left (in standard Cartesian with Y up, but GeoJSON usually has Y=Lat)
        # Wait, standard math:
        # If you walk from p1 to p2, Left is positive cross product z-component.
        cross_product = cl_vec[0] * to_bf_vec[1] - cl_vec[1] * to_bf_vec[0]
        
        return 'L' if cross_product > 0 else 'R'
        
    except Exception as e:
        # print(f"Error determining side: {e}")
        return None

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

async def main():
    """Main function to orchestrate the data ingestion process."""
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

    # Store Base Street Metadata (CNN -> Name, Address Ranges, etc.)
    # We use this to enrich the blockfaces created from pep9
    # Address ranges (lf_fadd, lf_toadd, rt_fadd, rt_toadd) enable address-based RPP matching
    streets_metadata = {}
    
    # Store address range index for RPP matching
    # Structure: { street_name: [ {cnn, lf_fadd, lf_toadd, rt_fadd, rt_toadd}, ... ] }
    address_range_index = {}

    # List to hold all distinct blockface objects
    all_blockfaces = []
    
    # Index to quickly find blockfaces by CNN for enrichment
    # Structure: { cnn_id: [ reference_to_blockface_1, reference_to_blockface_2, ... ] }
    cnn_to_blockfaces_index = {}

    # ==========================================
    # 1. Ingest Active Streets (The Backbone) - 3psu-pn9h
    # ==========================================
    print("\n--- 1. Processing Active Streets (The Backbone) ---")
    # Filter for Zip Code 94110 (Mission) and 94103 (SOMA/Mission/Mariposa area)
    streets_df = fetch_data_as_dataframe(STREETS_DATASET_ID, app_token, where="zip_code='94110' OR zip_code='94103'")
    
    if not streets_df.empty:
        # Save raw collection
        await db.streets.delete_many({})
        await db.streets.insert_many(streets_df.to_dict('records'))
        print("Saved raw 'streets' collection.")

        # Build Metadata Map with Address Ranges
        for _, row in streets_df.iterrows():
            cnn = row.get("cnn")
            street_name = row.get("streetname")
            if cnn:
                streets_metadata[cnn] = {
                    "streetName": street_name,
                    "centerlineGeometry": row.get("line"),
                    # Address ranges for RPP matching
                    "lf_fadd": row.get("lf_fadd"),  # Left from address
                    "lf_toadd": row.get("lf_toadd"),  # Left to address
                    "rt_fadd": row.get("rt_fadd"),  # Right from address
                    "rt_toadd": row.get("rt_toadd")   # Right to address
                }
                
                # Build address range index by street name
                if street_name:
                    if street_name not in address_range_index:
                        address_range_index[street_name] = []
                    address_range_index[street_name].append({
                        'cnn': cnn,
                        'lf_fadd': row.get("lf_fadd"),
                        'lf_toadd': row.get("lf_toadd"),
                        'rt_fadd': row.get("rt_fadd"),
                        'rt_toadd': row.get("rt_toadd")
                    })
        
        print(f"Loaded metadata for {len(streets_metadata)} streets.")
        print(f"Built address range index for {len(address_range_index)} street names.")

    # ==========================================
    # 2. Ingest Street Nodes - vd6w-dq8r
    # ==========================================
    print("\n--- 2. Processing Street Nodes ---")
    nodes_df = fetch_data_as_dataframe(STREET_NODES_ID, app_token)
    if not nodes_df.empty:
        await db.street_nodes.delete_many({})
        await db.street_nodes.insert_many(nodes_df.to_dict('records'))
        print("Saved 'street_nodes'.")

    # ==========================================
    # 3. Ingest Intersections - sw2d-qfup
    # ==========================================
    print("\n--- 3. Processing Intersections ---")
    intersections_df = fetch_data_as_dataframe(INTERSECTIONS_DATASET_ID, app_token)
    if not intersections_df.empty:
        await db.intersections.delete_many({})
        await db.intersections.insert_many(intersections_df.to_dict('records'))
        print("Saved 'intersections'.")

    # ==========================================
    # 4. Ingest Intersection Permutations - jfxm-zeee
    # ==========================================
    print("\n--- 4. Processing Intersection Permutations ---")
    perms_df = fetch_data_as_dataframe(INTERSECTION_PERMUTATIONS_ID, app_token)
    if not perms_df.empty:
        await db.intersection_permutations.delete_many({})
        await db.intersection_permutations.insert_many(perms_df.to_dict('records'))
        print("Saved 'intersection_permutations'.")

    # ==========================================
    # 4.5 Ingest RPP Eligibility Parcels - i886-hxz9
    # ==========================================
    print("\n--- 4.5. Processing RPP Eligibility Parcels (Address-Based RPP Matching) ---")
    # Fetch parcels with RPP eligibility codes
    # Filter for Mission/SOMA RPP areas: W, I, J, K, Q, R, S, T, U, V, X, Y, Z
    rpp_parcels_df = fetch_data_as_dataframe(
        RPP_PARCELS_ID,
        app_token,
        where="rppeligib IN ('W', 'I', 'J', 'K', 'Q', 'R', 'S', 'T', 'U', 'V', 'X', 'Y', 'Z')"
    )
    
    # Build address-to-RPP mapping for later use
    # Structure: { (street_name, address): rpp_code }
    address_to_rpp = {}
    
    if not rpp_parcels_df.empty:
        # Save raw collection for reference
        await db.rpp_parcels.delete_many({})
        await db.rpp_parcels.insert_many(rpp_parcels_df.to_dict('records'))
        
        # Create geospatial index for spatial queries (fallback method)
        try:
            await db.rpp_parcels.create_index([("shape", "2dsphere")])
            print("Created 2dsphere index on 'rpp_parcels'.")
        except Exception as e:
            print(f"Warning: Could not create index on rpp_parcels: {e}")
        
        print(f"Saved {len(rpp_parcels_df)} RPP parcels to collection.")
        
        # Build address-to-RPP mapping for address-based matching
        for _, row in rpp_parcels_df.iterrows():
            street_address = row.get("from_st")
            street_name = row.get("street")
            rpp_code = row.get("rppeligib")
            
            if street_address and street_name and rpp_code:
                try:
                    address_num = int(street_address)
                    key = (street_name.upper().strip(), address_num)
                    address_to_rpp[key] = rpp_code
                except (ValueError, TypeError):
                    continue
        
        print(f"Built address-to-RPP mapping with {len(address_to_rpp)} entries.")
        
        # Log sample mappings
        sample_count = min(5, len(address_to_rpp))
        if sample_count > 0:
            print(f"\nSample RPP Address Mappings:")
            for i, (key, rpp) in enumerate(list(address_to_rpp.items())[:sample_count]):
                street, addr = key
                print(f"  {addr} {street} → RPP Area {rpp}")

    # ==========================================
    # 5. Create Blockfaces from Geometries - pep9-66vw
    # ==========================================
    print("\n--- 5. Creating Blockfaces from pep9-66vw ---")
    # Fetch all, or filter if possible. Ideally we filter by the same area as streets,
    # but pep9 might not have zip code. We'll filter by matching CNNs we know about.
    geo_df = fetch_data_as_dataframe(BLOCKFACE_GEOMETRY_ID, app_token)
    
    if not geo_df.empty:
        count = 0
        for _, row in geo_df.iterrows():
            cnn = row.get("cnn_id")
            
            # Only process if this CNN belongs to our target area (found in Active Streets)
            if cnn in streets_metadata:
                metadata = streets_metadata[cnn]
                
                # Use globalid or blockface_ identifier
                bf_id = row.get("globalid") or row.get("blockface_") or f"{cnn}_{count}"
                bf_geo = row.get("shape")
                
                # Determine Side
                side = None
                if metadata.get("centerlineGeometry") and bf_geo:
                    side = get_side_of_street(metadata["centerlineGeometry"], bf_geo)
                
                new_blockface = {
                    "id": bf_id,
                    "cnn": cnn,
                    "streetName": metadata.get("streetName"),
                    "side": side, # 'L' or 'R'
                    "geometry": bf_geo, # Use the side-specific geometry
                    "rules": [],
                    "schedules": []
                }
                
                all_blockfaces.append(new_blockface)
                
                # Update Index
                if cnn not in cnn_to_blockfaces_index:
                    cnn_to_blockfaces_index[cnn] = []
                cnn_to_blockfaces_index[cnn].append(new_blockface)
                
                count += 1
        print(f"Created {count} distinct blockfaces from pep9-66vw.")

    # ==========================================
    # 6. Enrich with Street Cleaning - yhqp-riqs
    # ==========================================
    print("\n--- 6. Enriching with Street Cleaning ---")
    sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    if not sweeping_df.empty:
        await db.street_cleaning_schedules.delete_many({})
        await db.street_cleaning_schedules.insert_many(sweeping_df.to_dict('records'))
        print("Saved 'street_cleaning_schedules' collection.")

        count = 0
        for _, row in sweeping_df.iterrows():
            cnn = row.get("cnn")
            # Find all blockfaces for this CNN
            related_blockfaces = cnn_to_blockfaces_index.get(cnn, [])
            
            rule_side = row.get("cnnrightleft")
            
            for bf in related_blockfaces:
                # If we know the blockface side, and the rule specifies a side, check for match
                bf_side = bf.get("side")
                
                # If rule_side is specified (L/R) and bf_side is known, they MUST match.
                # If rule_side is None or Both, or bf_side is unknown, we might attach conservatively?
                # Usually cleaning is specific.
                
                if rule_side and bf_side:
                    if rule_side != bf_side:
                        continue # Skip this blockface, it's the wrong side
                
                rule = {
                    "type": "street-sweeping",
                    "day": row.get("weekday"),
                    "startTime": row.get("fromhour"),
                    "endTime": row.get("tohour"),
                    "side": rule_side, # R or L
                    "description": f"Street Cleaning {row.get('weekday')} {row.get('fromhour')}-{row.get('tohour')}"
                }
                bf["rules"].append(rule)
                count += 1
        print(f"Added {count} sweeping rules to blockfaces.")

    # ==========================================
    # 7. Ingest Parking Regulations - hi6h-neyh
    # ==========================================
    print("\n--- 7. Processing Parking Regulations ---")
    # Filter for Mission neighborhood to match the streets
    regulations_df = fetch_data_as_dataframe(PARKING_REGULATIONS_ID, app_token, where="analysis_neighborhood='Mission'")
    if not regulations_df.empty:
        await db.parking_regulations.delete_many({})
        # Convert to dicts
        reg_records = regulations_df.to_dict('records')
        
        # Insert raw
        await db.parking_regulations.insert_many(reg_records)
        
        # Create geospatial index for querying
        try:
            await db.parking_regulations.create_index([("geometry", "2dsphere")])
            print("Ensured 2dsphere index on 'parking_regulations'.")
        except Exception as e:
            print(f"Warning: Could not create index on regulations: {e}")
            
        print(f"Saved {len(reg_records)} parking regulations to collection.")
        
        # NOW JOIN REGULATIONS TO BLOCKFACES using SPATIAL intersection and geometric side matching
        print("Enriching blockfaces with parking regulations via spatial join and geometric analysis...")
        count = 0
        skipped_no_geometry = 0
        skipped_no_spatial_match = 0
        
        for idx, row in regulations_df.iterrows():
            reg_geo = row.get("shape") or row.get("geometry")
            if not reg_geo:
                skipped_no_geometry += 1
                continue
            
            try:
                reg_shape = shape(reg_geo)
            except Exception as e:
                skipped_no_geometry += 1
                continue
            
            # Find blockfaces that spatially intersect with this regulation
            # We'll check all blockfaces and find ones whose geometry is close to the regulation
            matched_blockface = None
            min_distance = float('inf')
            
            for bf in all_blockfaces:
                bf_geo = bf.get("geometry")
                if not bf_geo:
                    continue
                
                try:
                    bf_shape = shape(bf_geo)
                    
                    # Check if geometries are nearby (within ~50 meters)
                    distance = reg_shape.distance(bf_shape)
                    
                    if distance < 0.0005:  # roughly 50 meters in degrees
                        # Get the CNN for this blockface to find the centerline
                        cnn = bf.get("cnn")
                        if cnn and cnn in streets_metadata:
                            centerline_geo = streets_metadata[cnn].get("centerlineGeometry")
                            
                            if centerline_geo:
                                # Determine which side the regulation is on
                                reg_side = get_side_of_street(centerline_geo, reg_geo)
                                bf_side = bf.get("side")
                                
                                # Must match sides
                                if reg_side and bf_side and reg_side == bf_side:
                                    if distance < min_distance:
                                        min_distance = distance
                                        matched_blockface = (bf, reg_side)
                                # If sides aren't both known, match by closest distance
                                elif not reg_side or not bf_side:
                                    if distance < min_distance:
                                        min_distance = distance
                                        matched_blockface = (bf, reg_side)
                
                except Exception as e:
                    continue
            
            # Attach regulation to the best matching blockface
            if matched_blockface:
                bf, reg_side = matched_blockface
                bf["rules"].append({
                    "type": "parking-regulation",
                    "regulation": row.get("regulation"),
                    "timeLimit": row.get("hrlimit"),
                    "permitArea": row.get("rpparea1") or row.get("rpparea2"),
                    "days": row.get("days"),
                    "hours": row.get("hours"),
                    "fromTime": row.get("from_time"),
                    "toTime": row.get("to_time"),
                    "details": row.get("regdetails"),
                    "exceptions": row.get("exceptions"),
                    "side": reg_side
                })
                count += 1
            else:
                skipped_no_spatial_match += 1
        
        print(f"Added {count} parking regulations to blockfaces.")
        if skipped_no_geometry > 0:
            print(f"  Skipped {skipped_no_geometry} regulations without valid geometry")
        if skipped_no_spatial_match > 0:
            print(f"  Skipped {skipped_no_spatial_match} regulations with no spatial match to blockfaces")

    # ==========================================
    # 8. Metered Blockfaces (Metadata) - mk27-a5x2
    # ==========================================
    print("\n--- 8. Processing Metered Blockfaces (Metadata) ---")
    metered_bf_df = fetch_data_as_dataframe(METERED_BLOCKFACES_ID, app_token)
    # We mostly use this for linking if needed, or supplementary data.
    # Currently relying on Meters dataset for the actual meter info.

    # ==========================================
    # 9 & 10. Meters & Schedules
    # ==========================================
    print("\n--- 9-10. Enriching with Meters & Schedules ---")
    
    # 10. Meter Schedules (Lookup by post_id)
    schedules_df = fetch_data_as_dataframe(METER_SCHEDULES_DATASET_ID, app_token)
    schedules_by_post = {}
    if not schedules_df.empty:
        for _, row in schedules_df.iterrows():
            post_id = row.get("post_id")
            if post_id:
                if post_id not in schedules_by_post:
                    schedules_by_post[post_id] = []
                schedules_by_post[post_id].append({
                    "type": "meter-schedule",
                    "start": row.get("beg_time_dt"),
                    "end": row.get("end_time_dt"),
                    "rate": row.get("rate"),
                    "days": row.get("days_applied") # if available
                })

    # 9. Meters (Link post_id -> cnn)
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    if not meters_df.empty:
        count = 0
        for _, row in meters_df.iterrows():
            cnn = row.get("street_seg_ctrln_id") # This is CNN
            post_id = row.get("post_id")
            
            # Find related blockfaces
            related_blockfaces = cnn_to_blockfaces_index.get(cnn, [])
            
            if related_blockfaces and post_id:
                # Add meter info to ALL related blockfaces for now
                # (Ideally we match meter location to blockface geometry closer,
                # but CNN level is the best link we have without spatial join)
                meter_info = {
                    "type": "meter",
                    "postId": post_id,
                    "active": row.get("active_meter_flag"),
                    "schedules": schedules_by_post.get(post_id, [])
                }
                
                for bf in related_blockfaces:
                    bf["schedules"].append(meter_info)
                    count += 1
        print(f"Linked {count} meters to blockfaces.")

    # ==========================================
    # Final Save
    # ==========================================
    print("\n--- Saving Unified Blockfaces to MongoDB ---")
    
    # Filter out invalid geometries just in case
    final_blockfaces = [b for b in all_blockfaces if b.get("geometry")]

    if final_blockfaces:
        await db.blockfaces.delete_many({})
        
        # Batch insert
        chunk_size = 1000
        total = len(final_blockfaces)
        for i in range(0, total, chunk_size):
            chunk = final_blockfaces[i:i + chunk_size]
            await db.blockfaces.insert_many(chunk)
            print(f"Inserted batch {i} to {min(i+chunk_size, total)}")
        
        # Create Geospatial Index
        print("Creating geospatial index...")
        await db.blockfaces.create_index([("geometry", "2dsphere")])
        print(f"Successfully saved {total} unified blockfaces.")
    else:
        print("No blockfaces to save!")

    client.close()
    print("\nIngestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())