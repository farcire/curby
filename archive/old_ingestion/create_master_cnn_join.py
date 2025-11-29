"""
Create Master CNN Join Database

This script builds a comprehensive master join database that maps CNN identifiers
to all related street segment information including:
- Address ranges (odd/even)
- Cardinal directions (N, S, E, W, NE, NW, SE, SW, etc.)
- Blockface geometries
- Administrative boundaries
- All metadata from multiple SFMTA datasets

Usage:
    python3 create_master_cnn_join.py [--limit N] [--neighborhood NAME]
    
Options:
    --limit N: Process only N CNNs (for testing)
    --neighborhood NAME: Process only specific neighborhood (e.g., "Mission")
"""

import os
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv
from sodapy import Socrata
import motor.motor_asyncio
from typing import Dict, List, Optional
from shapely.geometry import shape, LineString

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Constants
SFMTA_DOMAIN = "data.sfgov.org"
ACTIVE_STREETS_ID = "3psu-pn9h"
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"
STREET_CLEANING_ID = "yhqp-riqs"

# Cardinal direction normalization
CARDINAL_DIRECTIONS = {
    'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West',
    'NE': 'Northeast', 'NW': 'Northwest', 'SE': 'Southeast', 'SW': 'Southwest',
    'NORTH': 'North', 'SOUTH': 'South', 'EAST': 'East', 'WEST': 'West',
    'NORTHEAST': 'Northeast', 'NORTHWEST': 'Northwest', 
    'SOUTHEAST': 'Southeast', 'SOUTHWEST': 'Southwest'
}

def normalize_cardinal_direction(direction: Optional[str]) -> Optional[str]:
    """Normalize cardinal direction to standard format."""
    if not direction:
        return None
    direction_upper = str(direction).strip().upper()
    return CARDINAL_DIRECTIONS.get(direction_upper, direction)

def get_side_of_street(centerline_geo: Dict, blockface_geo: Dict) -> Optional[str]:
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

def calculate_centroid(geometry: Dict) -> Optional[Dict]:
    """Calculate centroid of a geometry."""
    try:
        geom = shape(geometry)
        centroid = geom.centroid
        return {
            "type": "Point",
            "coordinates": [centroid.x, centroid.y]
        }
    except:
        return None

async def main(limit: Optional[int] = None, neighborhood: Optional[str] = None):
    """Main function to build master CNN join database."""
    
    print("="*80)
    print("CREATING MASTER CNN JOIN DATABASE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if limit:
        print(f"Limit: {limit} CNNs")
    if neighborhood:
        print(f"Neighborhood: {neighborhood}")
    print()
    
    # Setup
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    # Data structures
    cnn_master = {}  # CNN → master record
    
    # ==========================================
    # STEP 1: Fetch Active Streets (Foundation)
    # ==========================================
    print("STEP 1: Fetching Active Streets data...")
    socrata_client = Socrata(SFMTA_DOMAIN, app_token)
    
    where_clause = None
    if neighborhood:
        where_clause = f"analysis_neighborhood='{neighborhood}'"
    
    streets_data = socrata_client.get(
        ACTIVE_STREETS_ID,
        limit=limit or 200000,
        where=where_clause
    )
    
    print(f"  ✓ Fetched {len(streets_data)} street records")
    
    # Build base records
    for row in streets_data:
        cnn = row.get("cnn")
        if not cnn:
            continue
        
        cnn_master[cnn] = {
            "cnn": cnn,
            "cnn_left": f"{cnn}_L",
            "cnn_right": f"{cnn}_R",
            "street_name": row.get("streetname"),
            "from_street": row.get("from_street"),
            "to_street": row.get("to_street"),
            "street_type": row.get("st_type"),
            "zip_code": row.get("zip_code"),
            "left_side": {
                "side_code": "L",
                "cardinal_direction": None,
                "from_address": row.get("lf_fadd"),
                "to_address": row.get("lf_toadd"),
                "blockface_id": None,
                "geometry": None,
                "centroid": None
            },
            "right_side": {
                "side_code": "R",
                "cardinal_direction": None,
                "from_address": row.get("rt_fadd"),
                "to_address": row.get("rt_toadd"),
                "blockface_id": None,
                "geometry": None,
                "centroid": None
            },
            "centerline_geometry": row.get("line"),
            "neighborhood": row.get("analysis_neighborhood"),
            "supervisor_district": row.get("supervisor_district"),
            "data_sources": ["active_streets"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "version": 1
        }
    
    print(f"  ✓ Created {len(cnn_master)} base records")
    
    # ==========================================
    # STEP 2: Add Blockface Geometries
    # ==========================================
    print("\nSTEP 2: Adding blockface geometries...")
    
    blockface_data = socrata_client.get(BLOCKFACE_GEOMETRY_ID, limit=200000)
    print(f"  ✓ Fetched {len(blockface_data)} blockface records")
    
    matched = 0
    for row in blockface_data:
        cnn = row.get("cnn_id")
        if cnn not in cnn_master:
            continue
        
        master_record = cnn_master[cnn]
        bf_geo = row.get("shape")
        bf_id = row.get("globalid")
        
        if not bf_geo:
            continue
        
        # Determine side
        centerline_geo = master_record["centerline_geometry"]
        if centerline_geo:
            side = get_side_of_street(centerline_geo, bf_geo)
            
            if side == 'L':
                master_record["left_side"]["blockface_id"] = bf_id
                master_record["left_side"]["geometry"] = bf_geo
                master_record["left_side"]["centroid"] = calculate_centroid(bf_geo)
                matched += 1
            elif side == 'R':
                master_record["right_side"]["blockface_id"] = bf_id
                master_record["right_side"]["geometry"] = bf_geo
                master_record["right_side"]["centroid"] = calculate_centroid(bf_geo)
                matched += 1
        
        if "blockface_geometries" not in master_record["data_sources"]:
            master_record["data_sources"].append("blockface_geometries")
    
    print(f"  ✓ Matched {matched} blockface geometries")
    
    # ==========================================
    # STEP 3: Add Cardinal Directions from Street Cleaning
    # ==========================================
    print("\nSTEP 3: Adding cardinal directions from street cleaning...")
    
    cleaning_data = socrata_client.get(STREET_CLEANING_ID, limit=200000)
    print(f"  ✓ Fetched {len(cleaning_data)} street cleaning records")
    
    cardinal_added = 0
    for row in cleaning_data:
        cnn = row.get("cnn")
        if cnn not in cnn_master:
            continue
        
        master_record = cnn_master[cnn]
        side = row.get("cnnrightleft")
        cardinal = row.get("blockside")
        
        if side and cardinal:
            normalized_cardinal = normalize_cardinal_direction(cardinal)
            
            if side == 'L' and not master_record["left_side"]["cardinal_direction"]:
                master_record["left_side"]["cardinal_direction"] = normalized_cardinal
                cardinal_added += 1
            elif side == 'R' and not master_record["right_side"]["cardinal_direction"]:
                master_record["right_side"]["cardinal_direction"] = normalized_cardinal
                cardinal_added += 1
        
        if "street_cleaning" not in master_record["data_sources"]:
            master_record["data_sources"].append("street_cleaning")
    
    print(f"  ✓ Added {cardinal_added} cardinal directions")
    
    # ==========================================
    # STEP 4: Save to MongoDB
    # ==========================================
    print("\nSTEP 4: Saving to MongoDB...")
    
    # Clear existing data
    await db.cnn_master_join.delete_many({})
    print("  ✓ Cleared existing data")
    
    # Insert new data
    records = list(cnn_master.values())
    if records:
        chunk_size = 1000
        total = len(records)
        for i in range(0, total, chunk_size):
            chunk = records[i:i + chunk_size]
            await db.cnn_master_join.insert_many(chunk)
            print(f"  Saved batch {i//chunk_size + 1}/{(total + chunk_size - 1)//chunk_size}")
    
    # ==========================================
    # STEP 5: Create Indexes
    # ==========================================
    print("\nSTEP 5: Creating indexes...")
    
    await db.cnn_master_join.create_index([("cnn", 1)], unique=True)
    print("  ✓ Created CNN index")
    
    await db.cnn_master_join.create_index([("cnn_left", 1)])
    await db.cnn_master_join.create_index([("cnn_right", 1)])
    print("  ✓ Created composite key indexes")
    
    await db.cnn_master_join.create_index([("left_side.geometry", "2dsphere")])
    await db.cnn_master_join.create_index([("right_side.geometry", "2dsphere")])
    await db.cnn_master_join.create_index([("left_side.centroid", "2dsphere")])
    await db.cnn_master_join.create_index([("right_side.centroid", "2dsphere")])
    print("  ✓ Created geospatial indexes")
    
    await db.cnn_master_join.create_index([
        ("street_name", "text"),
        ("from_street", "text"),
        ("to_street", "text")
    ])
    print("  ✓ Created text search index")
    
    await db.cnn_master_join.create_index([("neighborhood", 1)])
    await db.cnn_master_join.create_index([("zip_code", 1)])
    print("  ✓ Created administrative indexes")
    
    # ==========================================
    # STEP 6: Statistics
    # ==========================================
    print("\n" + "="*80)
    print("MASTER CNN JOIN DATABASE CREATED")
    print("="*80)
    
    total_records = len(records)
    with_left_cardinal = sum(1 for r in records if r["left_side"]["cardinal_direction"])
    with_right_cardinal = sum(1 for r in records if r["right_side"]["cardinal_direction"])
    with_left_geo = sum(1 for r in records if r["left_side"]["geometry"])
    with_right_geo = sum(1 for r in records if r["right_side"]["geometry"])
    
    print(f"\nTotal CNN Records: {total_records}")
    print(f"\nLeft Side:")
    print(f"  - With Cardinal Direction: {with_left_cardinal} ({with_left_cardinal/total_records*100:.1f}%)")
    print(f"  - With Geometry: {with_left_geo} ({with_left_geo/total_records*100:.1f}%)")
    print(f"\nRight Side:")
    print(f"  - With Cardinal Direction: {with_right_cardinal} ({with_right_cardinal/total_records*100:.1f}%)")
    print(f"  - With Geometry: {with_right_geo} ({with_right_geo/total_records*100:.1f}%)")
    
    # Show sample
    sample = records[0] if records else None
    if sample:
        print(f"\nSample Record:")
        print(f"  CNN: {sample['cnn']}")
        print(f"  Street: {sample['street_name']}")
        print(f"  Left Side: {sample['left_side']['cardinal_direction']} ({sample['left_side']['from_address']}-{sample['left_side']['to_address']})")
        print(f"  Right Side: {sample['right_side']['cardinal_direction']} ({sample['right_side']['from_address']}-{sample['right_side']['to_address']})")
    
    client.close()
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create Master CNN Join Database')
    parser.add_argument('--limit', type=int, help='Limit number of CNNs to process')
    parser.add_argument('--neighborhood', type=str, help='Process specific neighborhood only')
    args = parser.parse_args()
    
    asyncio.run(main(limit=args.limit, neighborhood=args.neighborhood))