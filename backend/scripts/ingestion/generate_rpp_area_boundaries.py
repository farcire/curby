#!/usr/bin/env python3
"""
Generate RPP Area Boundaries from matched parking regulations
Creates convex hull boundaries for each RPP area to enable fallback spatial matching
"""

from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
from shapely.geometry import shape, MultiPoint
from shapely.ops import unary_union
import math

def connect_to_mongodb():
    """Connect to MongoDB"""
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file")
    
    client = MongoClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    return db

def is_valid_area(area):
    """Check if area value is valid (not nan, null, or empty)"""
    if area is None:
        return False
    area_str = str(area).lower()
    return area_str not in ['nan', 'none', '', 'null']

def extract_coordinates_from_geometry(geom):
    """Extract all coordinates from a geometry"""
    if not geom:
        return []
    
    try:
        geom_type = geom.get('type')
        coords = geom.get('coordinates', [])
        
        if geom_type == 'LineString':
            return coords
        elif geom_type == 'MultiLineString':
            # Flatten multi-linestring coordinates
            points = []
            for line in coords:
                points.extend(line)
            return points
        elif geom_type == 'Polygon':
            # Use exterior ring only
            return coords[0] if coords else []
        elif geom_type == 'MultiPolygon':
            # Use first polygon's exterior ring
            return coords[0][0] if coords and coords[0] else []
    except Exception as e:
        print(f"  Warning: Error extracting coordinates: {e}")
        return []
    
    return []

def generate_convex_hull(points):
    """Generate convex hull from list of coordinate points"""
    if len(points) < 3:
        return None
    
    try:
        # Create MultiPoint and get convex hull
        multi_point = MultiPoint(points)
        hull = multi_point.convex_hull
        
        # Convert to GeoJSON with proper coordinate format
        if hull.geom_type == 'Polygon':
            # Ensure coordinates are in [[[lon, lat], [lon, lat], ...]] format
            coords = [[[float(x), float(y)] for x, y in hull.exterior.coords]]
        else:
            # For Point or LineString (degenerate cases)
            coords = [[float(x), float(y)] for x, y in hull.coords]
        
        return {
            "type": hull.geom_type,
            "coordinates": coords
        }
    except Exception as e:
        print(f"  Error generating convex hull: {e}")
        return None

def main():
    print("=" * 80)
    print("RPP AREA BOUNDARY GENERATION")
    print("=" * 80)
    
    db = connect_to_mongodb()
    
    # 1. Extract RPP area data
    print("\n1. Extracting RPP area assignments from street_segments...")
    
    pipeline = [
        {
            "$match": {
                "rules": {
                    "$elemMatch": {
                        "$or": [
                            {"permitArea": {"$exists": True, "$ne": None}},
                            {"rppArea": {"$exists": True, "$ne": None}}
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "cnn": 1,
                "side": 1,
                "streetName": 1,
                "rules": 1,
                "centerlineGeometry": 1,
                "blockfaceGeometry": 1
            }
        }
    ]
    
    segments = list(db.street_segments.aggregate(pipeline))
    print(f"  Found {len(segments)} segments with RPP data")
    
    # 2. Collect geometries per RPP area
    print("\n2. Collecting geometries per RPP area...")
    
    rpp_geometries = defaultdict(list)
    skipped_nan = 0
    skipped_no_geom = 0
    
    for segment in segments:
        # Get geometry (prefer blockface, fallback to centerline)
        geom = segment.get('blockfaceGeometry') or segment.get('centerlineGeometry')
        
        if not geom:
            skipped_no_geom += 1
            continue
        
        # Extract coordinates
        coords = extract_coordinates_from_geometry(geom)
        if not coords:
            skipped_no_geom += 1
            continue
        
        # Extract RPP areas from rules
        for rule in segment.get('rules', []):
            area = rule.get('permitArea') or rule.get('rppArea')
            
            # Filter out invalid areas
            if not is_valid_area(area):
                skipped_nan += 1
                continue
            
            # Add coordinates to this area
            rpp_geometries[str(area)].extend(coords)
    
    print(f"  Collected geometries for {len(rpp_geometries)} RPP areas")
    print(f"  Skipped {skipped_nan} nan/null area values")
    print(f"  Skipped {skipped_no_geom} segments without geometry")
    
    # 3. Generate convex hull boundaries
    print("\n3. Generating convex hull boundaries...")
    
    boundaries = []
    successful = 0
    failed = 0
    
    for area, coords in sorted(rpp_geometries.items()):
        print(f"  Processing area {area}: {len(coords)} coordinate points")
        
        hull = generate_convex_hull(coords)
        
        if hull:
            boundaries.append({
                "area": area,
                "boundary": hull,
                "point_count": len(coords),
                "generated_at": datetime.utcnow()
            })
            successful += 1
        else:
            print(f"    ✗ Failed to generate hull for area {area}")
            failed += 1
    
    print(f"\n  Successfully generated {successful} boundaries")
    if failed > 0:
        print(f"  Failed to generate {failed} boundaries")
    
    # 4. Store in database
    print("\n4. Storing boundaries in database...")
    
    if boundaries:
        # Create collection with geospatial index
        collection = db.rpp_area_boundaries
        
        # Drop existing collection
        collection.drop()
        print(f"  Dropped existing rpp_area_boundaries collection")
        
        # Insert boundaries
        result = collection.insert_many(boundaries)
        print(f"  Inserted {len(result.inserted_ids)} boundaries")
        
        # Create geospatial index
        collection.create_index([("boundary", "2dsphere")])
        print(f"  Created 2dsphere index on boundary field")
        
        # Create index on area field
        collection.create_index("area")
        print(f"  Created index on area field")
    else:
        print(f"  No boundaries to store")
    
    # 5. Generate summary
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    
    print(f"\n✓ Results:")
    print(f"  - {successful} RPP area boundaries generated")
    print(f"  - {len(coords)} total coordinate points processed")
    print(f"  - {skipped_nan} invalid area values filtered out")
    print(f"  - {skipped_no_geom} segments without geometry skipped")
    
    if successful > 0:
        print(f"\n✅ SUCCESS: RPP area boundaries ready for fallback matching")
        print(f"\n📋 Usage:")
        print("  - Query: db.rpp_area_boundaries.find({'boundary': {'$geoIntersects': {'$geometry': <point>}}})")
        print("  - Returns RPP areas that intersect with given point/geometry")
        print("  - Use for fallback matching of unmatched regulations")
    
    # Save summary
    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_boundaries": successful,
        "failed_boundaries": failed,
        "total_points_processed": sum(len(coords) for coords in rpp_geometries.values()),
        "skipped_nan_values": skipped_nan,
        "skipped_no_geometry": skipped_no_geom,
        "top_areas": [
            {
                "area": area,
                "point_count": len(coords)
            }
            for area, coords in sorted(rpp_geometries.items(), key=lambda x: len(x[1]), reverse=True)[:20]
        ]
    }
    
    output_file = "rpp_boundary_generation_summary.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n\nSummary saved to: {output_file}")

if __name__ == "__main__":
    main()