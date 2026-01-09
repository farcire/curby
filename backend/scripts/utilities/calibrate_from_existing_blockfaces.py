#!/usr/bin/env python3
"""
Calibrate Blockface Offsets from Existing Data

Uses the existing blockface geometries in MongoDB (50% coverage) to learn
typical offset distances from CNN centerlines to blockface edges.

This is more accurate than fixed offsets because it learns from actual SFMTA data.
"""

import json
import numpy as np
from datetime import datetime
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client.curby


def calculate_perpendicular_offset(blockface_line, centerline):
    """
    Calculate perpendicular distance from blockface to centerline.
    
    Returns:
        float: Signed distance in meters (negative=left, positive=right)
    """
    # Sample points along the blockface
    num_samples = min(10, len(list(blockface_line.coords)))
    sample_points = []
    
    for i in range(num_samples):
        fraction = i / (num_samples - 1) if num_samples > 1 else 0
        point = blockface_line.interpolate(fraction, normalized=True)
        sample_points.append(point)
    
    # Calculate offset for each sample point
    offsets = []
    for point in sample_points:
        # Find nearest point on centerline
        nearest_pt = nearest_points(point, centerline)[1]
        
        # Calculate distance
        distance = point.distance(nearest_pt)
        
        # Determine sign using cross product
        # Get the segment of centerline nearest to the point
        coords = list(centerline.coords)
        min_dist = float('inf')
        nearest_segment_idx = 0
        
        for i in range(len(coords) - 1):
            seg = LineString([coords[i], coords[i+1]])
            dist = point.distance(seg)
            if dist < min_dist:
                min_dist = dist
                nearest_segment_idx = i
        
        # Get segment vector
        p1 = coords[nearest_segment_idx]
        p2 = coords[nearest_segment_idx + 1]
        
        # Vector from p1 to p2
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        # Vector from p1 to point
        mx = point.x - p1[0]
        my = point.y - p1[1]
        
        # Cross product (positive = right, negative = left)
        cross = dx * my - dy * mx
        
        # Convert distance to meters (approximate for SF lat/lon)
        distance_meters = distance * 111000  # Rough approximation
        
        # Apply sign
        signed_distance = distance_meters if cross > 0 else -distance_meters
        offsets.append(signed_distance)
    
    # Return median offset
    return np.median(offsets)


def analyze_existing_blockfaces():
    """
    Analyze existing blockface geometries in MongoDB to learn offset patterns.
    """
    print("Analyzing existing blockface geometries in MongoDB...")
    
    # Find segments with both centerline and blockface geometries
    segments = list(db.street_segments.find({
        'centerlineGeometry': {'$exists': True},
        'blockfaceGeometry': {'$exists': True, '$ne': None}
    }))
    
    print(f"✓ Found {len(segments)} segments with blockface geometries")
    
    offset_data = []
    skipped = {
        'invalid_geometry': 0,
        'calculation_error': 0
    }
    
    for i, segment in enumerate(segments):
        if (i + 1) % 1000 == 0:
            print(f"  Analyzed {i + 1:,} segments...")
        
        try:
            # Get geometries
            centerline_geom = segment.get('centerlineGeometry')
            blockface_geom = segment.get('blockfaceGeometry')
            
            if not centerline_geom or not blockface_geom:
                skipped['invalid_geometry'] += 1
                continue
            
            # Create Shapely objects
            centerline_coords = centerline_geom.get('coordinates', [])
            blockface_coords = blockface_geom.get('coordinates', [])
            
            if len(centerline_coords) < 2 or len(blockface_coords) < 2:
                skipped['invalid_geometry'] += 1
                continue
            
            centerline = LineString(centerline_coords)
            blockface = LineString(blockface_coords)
            
            # Calculate offset
            offset = calculate_perpendicular_offset(blockface, centerline)
            
            # Store result
            offset_data.append({
                'cnn': segment.get('cnn'),
                'side': segment.get('side'),
                'offset_meters': offset,
                'street_name': segment.get('streetName')
            })
            
        except Exception as e:
            skipped['calculation_error'] += 1
            continue
    
    print(f"\n✓ Analyzed {len(offset_data)} blockface offsets")
    print(f"  Skipped: {sum(skipped.values())} segments")
    for reason, count in skipped.items():
        if count > 0:
            print(f"    - {reason}: {count}")
    
    return offset_data


def build_calibration_model(offset_data):
    """
    Build calibration model from offset data.
    """
    print("\nBuilding calibration model...")
    
    # Group by side
    by_side = {'L': [], 'R': []}
    for d in offset_data:
        side = d['side']
        if side in by_side:
            by_side[side].append(d['offset_meters'])
    
    # Calculate statistics
    model = {
        'metadata': {
            'created_at': datetime.utcnow().isoformat(),
            'total_samples': len(offset_data),
            'version': '2.0',
            'source': 'mongodb_existing_blockfaces'
        },
        'by_side': {}
    }
    
    for side, offsets in by_side.items():
        if not offsets:
            continue
            
        model['by_side'][side] = {
            'mean': float(np.mean(offsets)),
            'median': float(np.median(offsets)),
            'std': float(np.std(offsets)),
            'min': float(np.min(offsets)),
            'max': float(np.max(offsets)),
            'count': len(offsets),
            'percentile_25': float(np.percentile(offsets, 25)),
            'percentile_75': float(np.percentile(offsets, 75))
        }
    
    # Global statistics
    all_offsets = [d['offset_meters'] for d in offset_data]
    model['global'] = {
        'mean': float(np.mean(all_offsets)),
        'median': float(np.median(all_offsets)),
        'std': float(np.std(all_offsets)),
        'count': len(all_offsets)
    }
    
    return model


def print_calibration_summary(model):
    """Print summary of calibration results."""
    print("\n" + "="*60)
    print("BLOCKFACE OFFSET CALIBRATION SUMMARY")
    print("="*60)
    
    print(f"\nTotal samples: {model['metadata']['total_samples']:,}")
    print(f"Created: {model['metadata']['created_at']}")
    print(f"Source: {model['metadata']['source']}")
    
    print("\nOffset Statistics by Side:")
    print("-" * 60)
    
    for side in ['L', 'R']:
        if side not in model['by_side']:
            continue
            
        stats = model['by_side'][side]
        print(f"\n{side} Side (n={stats['count']:,}):")
        print(f"  Mean:   {stats['mean']:>8.2f} meters")
        print(f"  Median: {stats['median']:>8.2f} meters")
        print(f"  Std:    {stats['std']:>8.2f} meters")
        print(f"  Range:  {stats['min']:>8.2f} to {stats['max']:>8.2f} meters")
        print(f"  IQR:    {stats['percentile_25']:>8.2f} to {stats['percentile_75']:>8.2f} meters")
    
    print("\n" + "="*60)
    print("\nInterpretation:")
    print("- Negative offsets = Left side of street")
    print("- Positive offsets = Right side of street")
    print("- Typical offset = distance from centerline to curb edge")
    print("="*60)


def main():
    """Main execution function."""
    print("="*60)
    print("BLOCKFACE OFFSET CALIBRATION")
    print("FROM EXISTING MONGODB DATA")
    print("="*60)
    print("\nThis script analyzes existing blockface geometries in MongoDB")
    print("to learn typical offset distances from centerlines.\n")
    
    # Step 1: Analyze existing blockfaces
    offset_data = analyze_existing_blockfaces()
    
    if not offset_data:
        print("\n❌ ERROR: No offset data collected. Cannot build calibration model.")
        print("Make sure MongoDB has segments with blockfaceGeometry.")
        return
    
    # Step 2: Build calibration model
    model = build_calibration_model(offset_data)
    
    # Step 3: Save model
    output_file = 'blockface_offset_calibration.json'
    with open(output_file, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n✓ Calibration model saved to: {output_file}")
    
    # Step 4: Save raw offset data
    raw_output_file = 'blockface_offset_raw_data.json'
    with open(raw_output_file, 'w') as f:
        json.dump(offset_data, f, indent=2)
    
    print(f"✓ Raw offset data saved to: {raw_output_file}")
    
    # Step 5: Print summary
    print_calibration_summary(model)
    
    print("\n✅ Calibration complete!")
    print("\nNext steps:")
    print("1. Review the calibration statistics above")
    print("2. Run: python generate_blockface_geometries.py")
    print("3. This will use the learned offsets to generate synthetic blockfaces")


if __name__ == "__main__":
    main()