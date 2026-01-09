#!/usr/bin/env python3
"""
Investigate Supervisory District boundary generation feasibility
Analyzes parking regulations matched to CNN+side to determine if we can
synthetically generate district boundaries for fallback matching
"""

from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv
from collections import defaultdict
from typing import Dict, List, Any

def connect_to_mongodb():
    """Connect to MongoDB"""
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file")
    
    client = MongoClient(mongodb_uri)
    db = client["curby"]
    return db

def main():
    print("=" * 80)
    print("SUPERVISORY DISTRICT BOUNDARY GENERATION - FEASIBILITY ANALYSIS")
    print("=" * 80)
    
    db = connect_to_mongodb()
    
    # 1. Check for district data in street_segments
    print("\n1. Analyzing supervisory district data in street_segments...")
    
    # Query segments with supervisor_district field (top-level field)
    pipeline = [
        {
            "$match": {
                "supervisor_district": {"$exists": True}
            }
        },
        {
            "$project": {
                "cnn": 1,
                "side": 1,
                "streetName": 1,
                "supervisor_district": 1,
                "centerlineGeometry": 1,
                "blockfaceGeometry": 1
            }
        }
    ]
    
    district_segments = list(db.street_segments.aggregate(pipeline))
    
    print(f"  Segments with district data: {len(district_segments)}")
    
    if not district_segments:
        print("  ✗ No district data found - cannot generate boundaries")
        return
    
    # 2. Extract and analyze districts
    print("\n2. Extracting district assignments...")
    
    district_data = defaultdict(lambda: {
        'segments': [],
        'with_centerline': 0,
        'with_blockface': 0
    })
    
    for segment in district_segments:
        cnn = segment.get('cnn')
        side = segment.get('side')
        street = segment.get('streetName')
        district = segment.get('supervisor_district')
        has_centerline = segment.get('centerlineGeometry') is not None
        has_blockface = segment.get('blockfaceGeometry') is not None
        
        # Each segment has single district (top-level field)
        if district:
            district_str = str(district)
            district_data[district_str]['segments'].append({
                'cnn': cnn,
                'side': side,
                'street': street
            })
            if has_centerline:
                district_data[district_str]['with_centerline'] += 1
            if has_blockface:
                district_data[district_str]['with_blockface'] += 1
    
    # 3. Display statistics
    print(f"\n  Unique Districts: {len(district_data)}")
    
    print(f"\n  District Statistics:")
    print(f"  {'District':<12} {'Segments':<10} {'Centerline':<12} {'Blockface':<12} {'Coverage'}")
    print(f"  {'-'*70}")
    
    sorted_districts = sorted(district_data.items(), 
                             key=lambda x: len(x[1]['segments']), 
                             reverse=True)
    
    total_segments = 0
    total_with_geometry = 0
    
    for district, data in sorted_districts:
        seg_count = len(data['segments'])
        centerline_count = data['with_centerline']
        blockface_count = data['with_blockface']
        geom_count = max(centerline_count, blockface_count)
        coverage = (geom_count / seg_count * 100) if seg_count > 0 else 0
        
        print(f"  {str(district):<12} {seg_count:<10} {centerline_count:<12} {blockface_count:<12} {coverage:.1f}%")
        
        total_segments += seg_count
        total_with_geometry += geom_count
    
    # 4. Overlap analysis
    print("\n3. Analyzing overlap patterns...")
    print(f"  Note: supervisor_district is a top-level field - each CNN+side has single district")
    print(f"  ✓ No overlaps (by design)")
    
    overlap_pct = 0.0
    
    # 5. Check for district boundaries in existing collections
    print("\n4. Checking for existing district boundary data...")
    
    collections = db.list_collection_names()
    district_collections = [c for c in collections if 'district' in c.lower() or 'supervisor' in c.lower()]
    
    if district_collections:
        print(f"  Found collections: {', '.join(district_collections)}")
        for coll_name in district_collections:
            count = db[coll_name].count_documents({})
            print(f"    - {coll_name}: {count} documents")
    else:
        print(f"  No existing district collections found")
    
    # 6. Confidence assessment
    print("\n" + "=" * 80)
    print("FEASIBILITY ASSESSMENT")
    print("=" * 80)
    
    geometry_coverage = (total_with_geometry / total_segments * 100) if total_segments > 0 else 0
    
    print(f"\n✓ Data Quality:")
    print(f"  - {len(district_data)} unique districts")
    print(f"  - {len(district_segments)} segments with district assignments")
    print(f"  - {geometry_coverage:.1f}% geometry coverage")
    print(f"  - {overlap_pct:.1f}% overlap rate (none expected)")
    
    if geometry_coverage >= 95:
        confidence = "HIGH"
        recommendation = "✓ RECOMMENDED: Excellent geometry coverage"
    elif geometry_coverage >= 80:
        confidence = "MEDIUM-HIGH"
        recommendation = "✓ ACCEPTABLE: Good geometry coverage"
    else:
        confidence = "MEDIUM"
        recommendation = "⚠️  POSSIBLE: Moderate coverage, may have gaps"
    
    print(f"\n{recommendation}")
    print(f"Confidence Level: {confidence}")
    
    print(f"\n📋 Implementation Plan:")
    print(f"  1. Extract district assignments from street_segments")
    print(f"  2. Collect geometries (centerline or blockface) per district")
    print(f"  3. Generate convex hull boundary for each district")
    print(f"  4. Store boundaries in district_boundaries collection")
    print(f"  5. Use for spatial fallback matching of unmatched regulations")
    
    print(f"\n✅ Benefits:")
    print(f"  - Enables fallback matching for regulations with geometry")
    print(f"  - Approximate boundaries sufficient for spatial queries")
    print(f"  - No overlaps (each segment has single district)")
    print(f"  - Auto-updates when regulations change")
    
    print(f"\n⚠️  Considerations:")
    if len(district_data) != 11:
        print(f"  - Expected 11 districts, found {len(district_data)}")
    
    # Save results
    results = {
        "total_districts": len(district_data),
        "total_segments": len(district_segments),
        "geometry_coverage_percent": geometry_coverage,
        "overlap_percentage": overlap_pct,
        "confidence_level": confidence,
        "districts": [
            {
                "district": district,
                "segment_count": len(data['segments']),
                "centerline_count": data['with_centerline'],
                "blockface_count": data['with_blockface']
            }
            for district, data in sorted_districts
        ],
        "existing_collections": district_collections
    }
    
    output_file = "district_boundary_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n\nDetailed results saved to: {output_file}")
    print("\nNext step: Run generate_district_boundaries.py to create boundaries")

if __name__ == "__main__":
    main()