#!/usr/bin/env python3
"""
Comprehensive Data Quality Detection Script for Parking Overlays

This script detects potential geometry issues across all street segments:
1. Blockface geometry on wrong side of centerline
2. Missing cardinal directions
3. Missing blockface geometries
4. Overlapping address ranges on same side
5. Inconsistent L/R to cardinal direction mappings
"""

import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json
from typing import List, Dict, Tuple
import math

load_dotenv()


def calculate_bearing(point1: List[float], point2: List[float]) -> float:
    """
    Calculate the bearing (direction) between two points in degrees.
    Returns: 0-360 degrees where 0/360 is North, 90 is East, 180 is South, 270 is West
    """
    lon1, lat1 = point1
    lon2, lat2 = point2
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    
    # Calculate bearing
    x = math.sin(dlon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    
    bearing = math.degrees(math.atan2(x, y))
    bearing = (bearing + 360) % 360  # Normalize to 0-360
    
    return bearing


def bearing_to_cardinal(bearing: float) -> str:
    """Convert bearing to cardinal direction (N, S, E, W)"""
    if 45 <= bearing < 135:
        return "E"
    elif 135 <= bearing < 225:
        return "S"
    elif 225 <= bearing < 315:
        return "W"
    else:
        return "N"


def calculate_perpendicular_offset_side(centerline_coords: List[List[float]], 
                                       blockface_coords: List[List[float]]) -> str:
    """
    Determine if blockface is on the left or right side of the centerline.
    Returns: "L" or "R" or "UNKNOWN"
    """
    if not centerline_coords or len(centerline_coords) < 2:
        return "UNKNOWN"
    if not blockface_coords or len(blockface_coords) < 1:
        return "UNKNOWN"
    
    # Use first segment of centerline to determine direction
    c1 = centerline_coords[0]
    c2 = centerline_coords[1] if len(centerline_coords) > 1 else centerline_coords[0]
    
    # Use first point of blockface
    b = blockface_coords[0]
    
    # Calculate cross product to determine which side
    # Vector from c1 to c2
    dx = c2[0] - c1[0]
    dy = c2[1] - c1[1]
    
    # Vector from c1 to blockface point
    bx = b[0] - c1[0]
    by = b[1] - c1[1]
    
    # Cross product (positive = left, negative = right)
    cross = dx * by - dy * bx
    
    if abs(cross) < 1e-10:  # Too close to centerline
        return "UNKNOWN"
    
    return "L" if cross > 0 else "R"


async def detect_issues():
    """Main function to detect data quality issues"""
    
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("DATA QUALITY DETECTION - PARKING OVERLAY GEOMETRY ISSUES")
    print("=" * 80)
    print()
    
    # Fetch all street segments
    print("Fetching all street segments from database...")
    all_segments = await db.street_segments.find({}).to_list(None)
    print(f"Total segments: {len(all_segments)}")
    print()
    
    # Initialize issue trackers
    issues = {
        'missing_cardinal': [],
        'missing_blockface': [],
        'swapped_geometry': [],
        'overlapping_ranges': [],
        'inconsistent_mapping': []
    }
    
    # Group segments by CNN for overlap detection
    segments_by_cnn = {}
    for seg in all_segments:
        cnn = seg.get('cnn')
        if cnn:
            if cnn not in segments_by_cnn:
                segments_by_cnn[cnn] = []
            segments_by_cnn[cnn].append(seg)
    
    print("Analyzing segments for data quality issues...")
    print()
    
    # Check each segment
    for i, seg in enumerate(all_segments):
        if i % 1000 == 0:
            print(f"  Progress: {i}/{len(all_segments)} segments analyzed...")
        
        cnn = seg.get('cnn')
        side = seg.get('side')
        cardinal = seg.get('cardinalDirection')
        
        # Issue 1: Missing cardinal direction
        if not cardinal:
            issues['missing_cardinal'].append({
                'cnn': cnn,
                'side': side,
                'streetName': seg.get('streetName'),
                'fromAddress': seg.get('fromAddress'),
                'toAddress': seg.get('toAddress')
            })
        
        # Issue 2: Missing blockface geometry
        if not seg.get('blockfaceGeometry'):
            issues['missing_blockface'].append({
                'cnn': cnn,
                'side': side,
                'streetName': seg.get('streetName'),
                'fromAddress': seg.get('fromAddress'),
                'toAddress': seg.get('toAddress')
            })
        
        # Issue 3: Check if blockface geometry is on wrong side
        centerline = seg.get('centerlineGeometry')
        blockface = seg.get('blockfaceGeometry')
        
        if centerline and blockface and side:
            centerline_coords = centerline.get('coordinates', [])
            blockface_coords = blockface.get('coordinates', [])
            
            if centerline_coords and blockface_coords:
                detected_side = calculate_perpendicular_offset_side(centerline_coords, blockface_coords)
                
                if detected_side != "UNKNOWN" and detected_side != side:
                    issues['swapped_geometry'].append({
                        'cnn': cnn,
                        'side': side,
                        'detected_side': detected_side,
                        'streetName': seg.get('streetName'),
                        'fromAddress': seg.get('fromAddress'),
                        'toAddress': seg.get('toAddress'),
                        'cardinal': cardinal
                    })
        
        # Issue 4: Check for inconsistent L/R to cardinal mapping
        if side and cardinal and centerline:
            centerline_coords = centerline.get('coordinates', [])
            if len(centerline_coords) >= 2:
                # Calculate street bearing
                bearing = calculate_bearing(centerline_coords[0], centerline_coords[-1])
                street_direction = bearing_to_cardinal(bearing)
                
                # Expected cardinal for each side based on street direction
                expected_cardinals = {
                    'N': {'L': 'W', 'R': 'E'},
                    'S': {'L': 'E', 'R': 'W'},
                    'E': {'L': 'N', 'R': 'S'},
                    'W': {'L': 'S', 'R': 'N'}
                }
                
                expected = expected_cardinals.get(street_direction, {}).get(side)
                if expected and cardinal and cardinal[0] != expected:
                    issues['inconsistent_mapping'].append({
                        'cnn': cnn,
                        'side': side,
                        'cardinal': cardinal,
                        'expected_cardinal': expected,
                        'street_direction': street_direction,
                        'streetName': seg.get('streetName'),
                        'fromAddress': seg.get('fromAddress'),
                        'toAddress': seg.get('toAddress')
                    })
    
    # Issue 5: Check for overlapping address ranges on same side
    print(f"  Progress: {len(all_segments)}/{len(all_segments)} segments analyzed.")
    print()
    print("Checking for overlapping address ranges...")
    
    for cnn, segments in segments_by_cnn.items():
        # Group by side
        by_side = {}
        for seg in segments:
            side = seg.get('side')
            if side:
                if side not in by_side:
                    by_side[side] = []
                by_side[side].append(seg)
        
        # Check for overlaps within each side
        for side, side_segments in by_side.items():
            for i, seg1 in enumerate(side_segments):
                for seg2 in side_segments[i+1:]:
                    try:
                        from1 = int(seg1.get('fromAddress', 0))
                        to1 = int(seg1.get('toAddress', 0))
                        from2 = int(seg2.get('fromAddress', 0))
                        to2 = int(seg2.get('toAddress', 0))
                        
                        # Check for overlap
                        if not (to1 < from2 or to2 < from1):
                            issues['overlapping_ranges'].append({
                                'cnn': cnn,
                                'side': side,
                                'streetName': seg1.get('streetName'),
                                'range1': f"{from1}-{to1}",
                                'range2': f"{from2}-{to2}"
                            })
                    except (ValueError, TypeError):
                        pass
    
    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY OF ISSUES DETECTED")
    print("=" * 80)
    print()
    
    print(f"1. Missing Cardinal Direction: {len(issues['missing_cardinal'])} segments")
    print(f"2. Missing Blockface Geometry: {len(issues['missing_blockface'])} segments")
    print(f"3. Swapped Geometry (blockface on wrong side): {len(issues['swapped_geometry'])} segments")
    print(f"4. Overlapping Address Ranges: {len(issues['overlapping_ranges'])} cases")
    print(f"5. Inconsistent L/R to Cardinal Mapping: {len(issues['inconsistent_mapping'])} segments")
    print()
    
    # Show examples of each issue type
    print("=" * 80)
    print("EXAMPLES OF EACH ISSUE TYPE")
    print("=" * 80)
    print()
    
    for issue_type, issue_list in issues.items():
        if issue_list:
            print(f"\n{issue_type.upper().replace('_', ' ')}:")
            print("-" * 60)
            for example in issue_list[:5]:  # Show first 5 examples
                print(f"  {example}")
            if len(issue_list) > 5:
                print(f"  ... and {len(issue_list) - 5} more")
            print()
    
    # Export detailed results
    output_file = 'geometry_issues_report.json'
    with open(output_file, 'w') as f:
        json.dump({
            'total_segments': len(all_segments),
            'issues': issues,
            'summary': {
                'missing_cardinal': len(issues['missing_cardinal']),
                'missing_blockface': len(issues['missing_blockface']),
                'swapped_geometry': len(issues['swapped_geometry']),
                'overlapping_ranges': len(issues['overlapping_ranges']),
                'inconsistent_mapping': len(issues['inconsistent_mapping'])
            }
        }, f, indent=2)
    
    print(f"Detailed report exported to: {output_file}")
    print()
    print("=" * 80)
    print("DETECTION COMPLETE")
    print("=" * 80)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(detect_issues())