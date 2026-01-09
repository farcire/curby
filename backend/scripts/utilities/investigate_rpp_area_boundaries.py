#!/usr/bin/env python3
"""
Investigate RPP Area boundary generation feasibility
Analyzes parking regulations matched to CNN+side to determine if we can
synthetically generate RPP area boundaries for fallback matching
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
    try:
        db = client.get_default_database()
    except:
        db = client["curby"]
    return db

def main():
    print("=" * 80)
    print("RPP AREA BOUNDARY GENERATION - FEASIBILITY ANALYSIS")
    print("=" * 80)
    
    db = connect_to_mongodb()
    
    # 1. Check for RPP data in street_segments
    print("\n1. Analyzing RPP area data in street_segments...")
    
    # Query segments with RPP regulations
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
    
    rpp_segments = list(db.street_segments.aggregate(pipeline))
    
    print(f"  Segments with RPP data: {len(rpp_segments)}")
    
    if not rpp_segments:
        print("  ✗ No RPP data found - cannot generate boundaries")
        return
    
    # 2. Extract and analyze RPP areas
    print("\n2. Extracting RPP area assignments...")
    
    rpp_area_data = defaultdict(lambda: {
        'segments': [],
        'with_centerline': 0,
        'with_blockface': 0
    })
    
    segments_with_multiple_areas = []
    
    for segment in rpp_segments:
        cnn = segment.get('cnn')
        side = segment.get('side')
        street = segment.get('streetName')
        has_centerline = segment.get('centerlineGeometry') is not None
        has_blockface = segment.get('blockfaceGeometry') is not None
        
        # Extract RPP areas from rules
        rpp_areas = set()
        for rule in segment.get('rules', []):
            area = rule.get('permitArea') or rule.get('rppArea')
            if area:
                rpp_areas.add(area)
        
        # Track data per RPP area
        for area in rpp_areas:
            rpp_area_data[area]['segments'].append({
                'cnn': cnn,
                'side': side,
                'street': street
            })
            if has_centerline:
                rpp_area_data[area]['with_centerline'] += 1
            if has_blockface:
                rpp_area_data[area]['with_blockface'] += 1
        
        # Track overlaps
        if len(rpp_areas) > 1:
            segments_with_multiple_areas.append({
                'cnn': cnn,
                'side': side,
                'street': street,
                'areas': [str(a) for a in rpp_areas]
            })
    
    # 3. Display statistics
    print(f"\n  Unique RPP Areas: {len(rpp_area_data)}")
    print(f"  Segments with Multiple Areas: {len(segments_with_multiple_areas)}")
    
    print(f"\n  RPP Area Statistics (Top 20 by segment count):")
    print(f"  {'Area':<10} {'Segments':<10} {'Centerline':<12} {'Blockface':<12} {'Coverage'}")
    print(f"  {'-'*70}")
    
    sorted_areas = sorted(rpp_area_data.items(), 
                         key=lambda x: len(x[1]['segments']), 
                         reverse=True)
    
    total_segments = 0
    total_with_geometry = 0
    
    for area, data in sorted_areas[:20]:
        seg_count = len(data['segments'])
        centerline_count = data['with_centerline']
        blockface_count = data['with_blockface']
        geom_count = max(centerline_count, blockface_count)
        coverage = (geom_count / seg_count * 100) if seg_count > 0 else 0
        
        print(f"  {str(area):<10} {seg_count:<10} {centerline_count:<12} {blockface_count:<12} {coverage:.1f}%")
        
        total_segments += seg_count
        total_with_geometry += geom_count
    
    # 4. Overlap analysis
    print("\n3. Analyzing overlap patterns...")
    
    overlap_pct = (len(segments_with_multiple_areas) / len(rpp_segments) * 100) if rpp_segments else 0
    print(f"  Overlap percentage: {overlap_pct:.1f}%")
    
    if segments_with_multiple_areas:
        print(f"\n  Sample overlapping segments (first 5):")
        for i, seg in enumerate(segments_with_multiple_areas[:5], 1):
            print(f"    {i}. {seg['street']} (CNN {seg['cnn']}{seg['side']}): {', '.join(seg['areas'])}")
    
    # 5. Confidence assessment
    print("\n" + "=" * 80)
    print("FEASIBILITY ASSESSMENT")
    print("=" * 80)
    
    geometry_coverage = (total_with_geometry / total_segments * 100) if total_segments > 0 else 0
    
    print(f"\n✓ Data Quality:")
    print(f"  - {len(rpp_area_data)} unique RPP areas")
    print(f"  - {len(rpp_segments)} segments with RPP assignments")
    print(f"  - {geometry_coverage:.1f}% geometry coverage")
    print(f"  - {overlap_pct:.1f}% segments in multiple areas")
    
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
    print(f"  1. Extract RPP area assignments from street_segments")
    print(f"  2. Collect geometries (centerline or blockface) per area")
    print(f"  3. Generate convex hull boundary for each area")
    print(f"  4. Store boundaries in rpp_area_boundaries collection")
    print(f"  5. Use for spatial fallback matching of unmatched regulations")
    
    print(f"\n✅ Benefits:")
    print(f"  - Enables fallback matching for regulations with geometry")
    print(f"  - Approximate boundaries sufficient for spatial queries")
    print(f"  - Overlaps allowed (no conflict resolution needed)")
    print(f"  - Auto-updates when regulations change")
    
    # Save results
    results = {
        "total_areas": len(rpp_area_data),
        "total_segments": len(rpp_segments),
        "geometry_coverage_percent": geometry_coverage,
        "overlap_percentage": overlap_pct,
        "confidence_level": confidence,
        "top_areas": [
            {
                "area": area,
                "segment_count": len(data['segments']),
                "centerline_count": data['with_centerline'],
                "blockface_count": data['with_blockface']
            }
            for area, data in sorted_areas[:20]
        ],
        "sample_overlaps": segments_with_multiple_areas[:10]
    }
    
    output_file = "rpp_area_boundary_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n\nDetailed results saved to: {output_file}")
    print("\nNext step: Run generate_rpp_area_boundaries.py to create boundaries")

if __name__ == "__main__":
    main()