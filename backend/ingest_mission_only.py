"""
Mission Neighborhood Focused Data Ingestion Script

This script demonstrates how parking regulations, metered parking, and street cleaning
merge over active streets and blockfaces for the Mission neighborhood only.

Target Area: Mission District (Zip 94110, 94103)
Expected Output: ~4,000 street segments with merged data layers
"""

import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import motor.motor_asyncio
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, LineString, Point
from datetime import datetime

# --- Constants ---
SFMTA_DOMAIN = "data.sfgov.org"

# Dataset IDs
STREETS_DATASET_ID = "3psu-pn9h"              # Active Streets (Foundation)
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"           # Blockface Geometries (Enhancement)
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs"    # Street Cleaning (Direct Join)
PARKING_REGULATIONS_ID = "hi6h-neyh"          # Parking Regulations (Spatial Join)
METERS_DATASET_ID = "8vzz-qzz9"               # Parking Meters
METER_SCHEDULES_DATASET_ID = "6cqg-dxku"      # Meter Schedules

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

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
        
        # Get tangent vector
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
        
        # Cross product to determine side
        cross_product = cl_vec[0] * to_bf_vec[1] - cl_vec[1] * to_bf_vec[0]
        
        return 'L' if cross_product > 0 else 'R'
        
    except Exception as e:
        return None

def fetch_data_as_dataframe(dataset_id: str, app_token: Optional[str], limit: int = 200000, **kwargs) -> pd.DataFrame:
    """Fetches a dataset and returns it as a pandas DataFrame."""
    print(f"  Fetching dataset {dataset_id}...")
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(dataset_id, limit=limit, **kwargs)
        df = pd.DataFrame.from_records(results)
        print(f"  ✓ Fetched {len(df)} records")
        return df
    except Exception as e:
        print(f"  ✗ Error fetching dataset {dataset_id}: {e}")
        return pd.DataFrame()

async def main():
    """Main function to orchestrate the Mission neighborhood data ingestion."""
    
    print_section("MISSION NEIGHBORHOOD DATA INGESTION")
    print("Target: Mission District (Zip 94110, 94103)")
    print("Demonstrating: How parking regs, meters, and street cleaning merge over streets")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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

    # Data structures for tracking merges
    streets_metadata = {}  # CNN → street info
    all_blockfaces = []    # Final merged segments
    cnn_to_blockfaces_index = {}  # CNN → [blockface references]
    
    # Statistics tracking
    stats = {
        'total_cnns': 0,
        'total_segments': 0,
        'with_blockface_geo': 0,
        'with_street_cleaning': 0,
        'with_parking_regs': 0,
        'with_meters': 0
    }

    # ==========================================
    # LAYER 1: Active Streets (Foundation)
    # ==========================================
    print_section("LAYER 1: Active Streets (Foundation)")
    print("This layer provides:")
    print("  • CNN identifiers")
    print("  • Street names")
    print("  • Address ranges (Left & Right)")
    print("  • Centerline geometries")
    print("\nFiltering for Mission neighborhood (Zip 94110, 94103)...")
    
    streets_df = fetch_data_as_dataframe(
        STREETS_DATASET_ID, 
        app_token, 
        where="zip_code='94110' OR zip_code='94103'"
    )
    
    if not streets_df.empty:
        stats['total_cnns'] = len(streets_df)
        print(f"\n✓ Found {stats['total_cnns']} CNNs in Mission neighborhood")
        print(f"  → Will create {stats['total_cnns'] * 2} segments (Left & Right sides)")
        
        # Build metadata map
        for _, row in streets_df.iterrows():
            cnn = row.get("cnn")
            if cnn:
                streets_metadata[cnn] = {
                    "streetName": row.get("streetname"),
                    "centerlineGeometry": row.get("line"),
                    "lf_fadd": row.get("lf_fadd"),
                    "lf_toadd": row.get("lf_toadd"),
                    "rt_fadd": row.get("rt_fadd"),
                    "rt_toadd": row.get("rt_toadd"),
                    "zip_code": row.get("zip_code")
                }
        
        # Show sample
        sample_cnn = list(streets_metadata.keys())[0]
        sample = streets_metadata[sample_cnn]
        print(f"\nSample Street:")
        print(f"  CNN: {sample_cnn}")
        print(f"  Name: {sample['streetName']}")
        print(f"  Left Addresses: {sample['lf_fadd']}-{sample['lf_toadd']}")
        print(f"  Right Addresses: {sample['rt_fadd']}-{sample['rt_toadd']}")

    # ==========================================
    # LAYER 2: Blockface Geometries (Enhancement)
    # ==========================================
    print_section("LAYER 2: Blockface Geometries (Enhancement)")
    print("This layer provides:")
    print("  • Precise curb-side geometries (offset from centerline)")
    print("  • GlobalID identifiers")
    print("  • Side determination (L/R via geometric analysis)")
    print("\nFetching blockface geometries...")
    
    geo_df = fetch_data_as_dataframe(BLOCKFACE_GEOMETRY_ID, app_token)
    
    if not geo_df.empty:
        print(f"\nProcessing blockface geometries...")
        count = 0
        for _, row in geo_df.iterrows():
            cnn = row.get("cnn_id")
            
            # Only process if CNN is in Mission
            if cnn in streets_metadata:
                metadata = streets_metadata[cnn]
                
                bf_id = row.get("globalid") or f"{cnn}_{count}"
                bf_geo = row.get("shape")
                
                # Determine Side using geometric analysis
                side = None
                if metadata.get("centerlineGeometry") and bf_geo:
                    side = get_side_of_street(metadata["centerlineGeometry"], bf_geo)
                
                new_blockface = {
                    "id": bf_id,
                    "cnn": cnn,
                    "streetName": metadata.get("streetName"),
                    "side": side,
                    "geometry": bf_geo,
                    "centerlineGeometry": metadata.get("centerlineGeometry"),
                    "fromAddress": metadata.get("lf_fadd") if side == 'L' else metadata.get("rt_fadd"),
                    "toAddress": metadata.get("lf_toadd") if side == 'L' else metadata.get("rt_toadd"),
                    "zip_code": metadata.get("zip_code"),
                    "rules": [],
                    "schedules": [],
                    "data_layers": ["active_streets", "blockface_geometry"]
                }
                
                all_blockfaces.append(new_blockface)
                
                if cnn not in cnn_to_blockfaces_index:
                    cnn_to_blockfaces_index[cnn] = []
                cnn_to_blockfaces_index[cnn].append(new_blockface)
                
                count += 1
                if bf_geo:
                    stats['with_blockface_geo'] += 1
        
        stats['total_segments'] = count
        print(f"\n✓ Created {count} blockface segments")
        print(f"  → {stats['with_blockface_geo']} with precise blockface geometry")
        print(f"  → Coverage: {(stats['with_blockface_geo']/count*100):.1f}%")

    # ==========================================
    # LAYER 3: Street Cleaning (Direct Join)
    # ==========================================
    print_section("LAYER 3: Street Cleaning (Direct Join)")
    print("This layer provides:")
    print("  • Street sweeping schedules")
    print("  • Day and time restrictions")
    print("  • Cardinal directions (N, S, E, W)")
    print("\nJoin Method: Direct CNN + Side match (no spatial analysis needed!)")
    print("Fetching street cleaning schedules...")
    
    sweeping_df = fetch_data_as_dataframe(STREET_CLEANING_SCHEDULES_ID, app_token)
    
    if not sweeping_df.empty:
        print(f"\nMerging street cleaning data...")
        count = 0
        for _, row in sweeping_df.iterrows():
            cnn = row.get("cnn")
            related_blockfaces = cnn_to_blockfaces_index.get(cnn, [])
            
            rule_side = row.get("cnnrightleft")
            
            for bf in related_blockfaces:
                bf_side = bf.get("side")
                
                # Direct side match - this is the key efficiency!
                if rule_side and bf_side and rule_side == bf_side:
                    rule = {
                        "type": "street-sweeping",
                        "day": row.get("weekday"),
                        "startTime": row.get("fromhour"),
                        "endTime": row.get("tohour"),
                        "side": rule_side,
                        "cardinalDirection": row.get("blockside"),
                        "description": f"Street Cleaning {row.get('weekday')} {row.get('fromhour')}-{row.get('tohour')}"
                    }
                    bf["rules"].append(rule)
                    if "street_cleaning" not in bf["data_layers"]:
                        bf["data_layers"].append("street_cleaning")
                    count += 1
        
        segments_with_cleaning = len([bf for bf in all_blockfaces if any(r['type'] == 'street-sweeping' for r in bf['rules'])])
        stats['with_street_cleaning'] = segments_with_cleaning
        print(f"\n✓ Added {count} street cleaning rules")
        print(f"  → {segments_with_cleaning} segments now have street cleaning schedules")
        print(f"  → Coverage: {(segments_with_cleaning/stats['total_segments']*100):.1f}%")

    # ==========================================
    # LAYER 4: Parking Regulations (Spatial Join)
    # ==========================================
    print_section("LAYER 4: Parking Regulations (Spatial Join)")
    print("This layer provides:")
    print("  • Time limits (2 HR, 4 HR, etc.)")
    print("  • RPP zones")
    print("  • Tow-away zones")
    print("  • Loading zones")
    print("\nJoin Method: Spatial proximity + geometric side determination")
    print("Filtering for Mission neighborhood...")
    
    regulations_df = fetch_data_as_dataframe(
        PARKING_REGULATIONS_ID, 
        app_token, 
        where="analysis_neighborhood='Mission'"
    )
    
    if not regulations_df.empty:
        print(f"\nMerging parking regulations via spatial analysis...")
        count = 0
        skipped_no_geometry = 0
        skipped_no_match = 0
        
        for idx, row in regulations_df.iterrows():
            reg_geo = row.get("shape") or row.get("geometry")
            if not reg_geo:
                skipped_no_geometry += 1
                continue
            
            try:
                reg_shape = shape(reg_geo)
            except Exception:
                skipped_no_geometry += 1
                continue
            
            # Find best matching blockface
            matched_blockface = None
            min_distance = float('inf')
            
            for bf in all_blockfaces:
                bf_geo = bf.get("geometry")
                if not bf_geo:
                    continue
                
                try:
                    bf_shape = shape(bf_geo)
                    distance = reg_shape.distance(bf_shape)
                    
                    if distance < 0.0005:  # ~50 meters
                        cnn = bf.get("cnn")
                        if cnn and cnn in streets_metadata:
                            centerline_geo = streets_metadata[cnn].get("centerlineGeometry")
                            
                            if centerline_geo:
                                # Geometric side determination
                                reg_side = get_side_of_street(centerline_geo, reg_geo)
                                bf_side = bf.get("side")
                                
                                if reg_side and bf_side and reg_side == bf_side:
                                    if distance < min_distance:
                                        min_distance = distance
                                        matched_blockface = bf
                except Exception:
                    continue
            
            if matched_blockface:
                matched_blockface["rules"].append({
                    "type": "parking-regulation",
                    "regulation": row.get("regulation"),
                    "timeLimit": row.get("hrlimit"),
                    "permitArea": row.get("rpparea1") or row.get("rpparea2"),
                    "days": row.get("days"),
                    "hours": row.get("hours"),
                    "details": row.get("regdetails")
                })
                if "parking_regulations" not in matched_blockface["data_layers"]:
                    matched_blockface["data_layers"].append("parking_regulations")
                count += 1
            else:
                skipped_no_match += 1
        
        segments_with_regs = len([bf for bf in all_blockfaces if any(r['type'] == 'parking-regulation' for r in bf['rules'])])
        stats['with_parking_regs'] = segments_with_regs
        print(f"\n✓ Added {count} parking regulations")
        print(f"  → {segments_with_regs} segments now have parking regulations")
        print(f"  → Skipped {skipped_no_geometry} without geometry")
        print(f"  → Skipped {skipped_no_match} without spatial match")

    # ==========================================
    # LAYER 5: Parking Meters (CNN Join + Schedules)
    # ==========================================
    print_section("LAYER 5: Parking Meters (CNN Join + Schedules)")
    print("This layer provides:")
    print("  • Meter locations")
    print("  • Rate schedules")
    print("  • Operating hours")
    print("\nJoin Method: CNN match + schedule lookup")
    print("Fetching meter schedules...")
    
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
                    "days": row.get("days_applied")
                })
    
    print("Fetching parking meters...")
    meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)
    
    if not meters_df.empty:
        print(f"\nMerging parking meters...")
        count = 0
        for _, row in meters_df.iterrows():
            cnn = row.get("street_seg_ctrln_id")
            post_id = row.get("post_id")
            
            related_blockfaces = cnn_to_blockfaces_index.get(cnn, [])
            
            if related_blockfaces and post_id:
                meter_info = {
                    "type": "meter",
                    "postId": post_id,
                    "active": row.get("active_meter_flag"),
                    "schedules": schedules_by_post.get(post_id, [])
                }
                
                for bf in related_blockfaces:
                    bf["schedules"].append(meter_info)
                    if "parking_meters" not in bf["data_layers"]:
                        bf["data_layers"].append("parking_meters")
                    count += 1
        
        segments_with_meters = len([bf for bf in all_blockfaces if len(bf['schedules']) > 0])
        stats['with_meters'] = segments_with_meters
        print(f"\n✓ Linked {count} meter instances")
        print(f"  → {segments_with_meters} segments now have meter data")

    # ==========================================
    # Save to MongoDB
    # ==========================================
    print_section("SAVING MERGED DATA TO MONGODB")
    
    final_blockfaces = [b for b in all_blockfaces if b.get("geometry")]
    
    if final_blockfaces:
        print(f"Saving {len(final_blockfaces)} merged segments...")
        await db.blockfaces.delete_many({})
        
        chunk_size = 1000
        total = len(final_blockfaces)
        for i in range(0, total, chunk_size):
            chunk = final_blockfaces[i:i + chunk_size]
            await db.blockfaces.insert_many(chunk)
            print(f"  Saved batch {i//chunk_size + 1}/{(total + chunk_size - 1)//chunk_size}")
        
        print("\nCreating geospatial index...")
        await db.blockfaces.create_index([("geometry", "2dsphere")])
        print("✓ Index created")

    # ==========================================
    # Final Statistics
    # ==========================================
    print_section("MISSION NEIGHBORHOOD DATA MERGE COMPLETE")
    
    print("Coverage Statistics:")
    print(f"  Total CNNs: {stats['total_cnns']}")
    print(f"  Total Segments: {stats['total_segments']}")
    print(f"  With Blockface Geometry: {stats['with_blockface_geo']} ({stats['with_blockface_geo']/stats['total_segments']*100:.1f}%)")
    print(f"  With Street Cleaning: {stats['with_street_cleaning']} ({stats['with_street_cleaning']/stats['total_segments']*100:.1f}%)")
    print(f"  With Parking Regulations: {stats['with_parking_regs']} ({stats['with_parking_regs']/stats['total_segments']*100:.1f}%)")
    print(f"  With Parking Meters: {stats['with_meters']} ({stats['with_meters']/stats['total_segments']*100:.1f}%)")
    
    print("\nData Layer Merge Summary:")
    layer_counts = {}
    for bf in all_blockfaces:
        layer_count = len(bf.get("data_layers", []))
        layer_counts[layer_count] = layer_counts.get(layer_count, 0) + 1
    
    for count in sorted(layer_counts.keys(), reverse=True):
        print(f"  {layer_counts[count]} segments with {count} data layers")
    
    # Show sample merged segment
    sample_with_all = [bf for bf in all_blockfaces if len(bf.get("data_layers", [])) >= 4]
    if sample_with_all:
        sample = sample_with_all[0]
        print(f"\nSample Fully Merged Segment:")
        print(f"  Street: {sample['streetName']} ({sample['side']} side)")
        print(f"  CNN: {sample['cnn']}")
        print(f"  Address Range: {sample['fromAddress']}-{sample['toAddress']}")
        print(f"  Data Layers: {', '.join(sample['data_layers'])}")
        print(f"  Rules: {len(sample['rules'])}")
        print(f"  Meter Schedules: {len(sample['schedules'])}")

    client.close()
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())