#!/usr/bin/env python3
"""
Blockface Offset Calibration Script

Analyzes metered blockfaces to learn typical offset distances from CNN centerlines
to actual blockface edges. Uses parking meter locations as ground truth.

This script:
1. Loads metered blockfaces with known CNN + side
2. Calculates perpendicular distance from each meter to its CNN centerline
3. Analyzes offset patterns by street type and side
4. Generates calibration model for synthetic blockface generation

Output: blockface_offset_calibration.json
"""

import json
import numpy as np
from datetime import datetime
from collections import defaultdict
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from sodapy import Socrata
import os
from dotenv import load_dotenv

load_dotenv()

# Socrata API configuration
SOCRATA_DOMAIN = "data.sfgov.org"
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

# Dataset IDs
METERED_BLOCKFACES_ID = "mk27-a5x2"
PARKING_METERS_ID = "8vzz-qzz9"
ACTIVE_STREETS_ID = "3psu-pn9h"


def fetch_metered_blockfaces():
    """Fetch metered blockfaces dataset with CNN and side information."""
    print("Fetching metered blockfaces...")
    client = Socrata(SOCRATA_DOMAIN, SOCRATA_APP_TOKEN)
    
    # Fetch all metered blockfaces
    blockfaces = client.get(METERED_BLOCKFACES_ID, limit=50000)
    
    print(f"✓ Loaded {len(blockfaces)} metered blockfaces")
    
    # Build lookup: blockface_id -> {cnn, side, street_name, address_range}
    blockface_lookup = {}
    for bf in blockfaces:
        bf_id = bf.get('blockface_id')
        if not bf_id:
            continue
            
        blockface_lookup[str(bf_id)] = {
            'blockface_id': bf_id,
            'cnn': bf.get('cnn'),
            'side': bf.get('str_seg_orientation'),  # L or R
            'street_name': bf.get('street_name'),
            'from_addr': bf.get('fm_addr_no'),
            'to_addr': bf.get('to_addr_no')
        }
    
    return blockface_lookup


def fetch_parking_meters():
    """Fetch parking meters with coordinates and blockface IDs."""
    print("Fetching parking meters...")
    client = Socrata(SOCRATA_DOMAIN, SOCRATA_APP_TOKEN)
    
    # Fetch on-street meters only
    meters = client.get(
        PARKING_METERS_ID,
        where="meter_type='SS'",  # On-street meters
        limit=50000
    )
    
    print(f"✓ Loaded {len(meters)} on-street parking meters")
    return meters


def fetch_active_streets():
    """Fetch Active Streets dataset for CNN centerline geometries."""
    print("Fetching Active Streets for CNN geometries...")
    client = Socrata(SOCRATA_DOMAIN, SOCRATA_APP_TOKEN)
    
    # Fetch active streets with geometries
    streets = client.get(
        ACTIVE_STREETS_ID,
        where="active='True' OR active IS NULL",
        limit=50000
    )
    
    print(f"✓ Loaded {len(streets)} active street segments")
    
    # Build lookup: cnn -> geometry
    cnn_geometries = {}
    for street in streets:
        cnn = street.get('cnn')
        if not cnn:
            continue
            
        # Parse LineString geometry
        line_geom = street.get('line')
        if line_geom and line_geom.get('type') == 'LineString':
            coords = line_geom['coordinates']
            # Convert to Shapely LineString
            cnn_geometries[str(cnn)] = LineString(coords)
    
    print(f"✓ Built geometry lookup for {len(cnn_geometries)} CNNs")
    return cnn_geometries


def calculate_perpendicular_offset(meter_point, centerline):
    """
    Calculate perpendicular distance from meter to centerline.
    
    Returns:
        float: Signed distance in meters (negative=left, positive=right)
    """
    # Find nearest point on centerline
    nearest_pt = nearest_points(meter_point, centerline)[1]
    
    # Calculate distance
    distance = meter_point.distance(nearest_pt)
    
    # Determine sign (left vs right)
    # Use cross product to determine which side
    # Get the segment of centerline nearest to the point
    coords = list(centerline.coords)
    min_dist = float('inf')
    nearest_segment_idx = 0
    
    for i in range(len(coords) - 1):
        seg = LineString([coords[i], coords[i+1]])
        dist = meter_point.distance(seg)
        if dist < min_dist:
            min_dist = dist
            nearest_segment_idx = i
    
    # Get segment vector
    p1 = coords[nearest_segment_idx]
    p2 = coords[nearest_segment_idx + 1]
    
    # Vector from p1 to p2
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    
    # Vector from p1 to meter
    mx = meter_point.x - p1[0]
    my = meter_point.y - p1[1]
    
    # Cross product (positive = right, negative = left)
    cross = dx * my - dy * mx
    
    # Convert distance to meters (approximate for SF lat/lon)
    # 1 degree longitude ≈ 85km at SF latitude
    # 1 degree latitude ≈ 111km
    distance_meters = distance * 111000  # Rough approximation
    
    # Apply sign
    return distance_meters if cross > 0 else -distance_meters


def analyze_offsets(meters, blockface_lookup, cnn_geometries):
    """
    Analyze offset patterns from meters to centerlines.
    
    Returns:
        dict: Calibration model with offset statistics
    """
    print("\nAnalyzing meter offsets...")
    
    offset_data = []
    skipped = {
        'no_blockface_id': 0,
        'blockface_not_found': 0,
        'no_cnn': 0,
        'no_geometry': 0,
        'no_coordinates': 0
    }
    
    for meter in meters:
        # Get blockface ID
        bf_id = meter.get('blockface_id')
        if not bf_id:
            skipped['no_blockface_id'] += 1
            continue
        
        # Look up blockface info
        bf_info = blockface_lookup.get(str(bf_id))
        if not bf_info:
            skipped['blockface_not_found'] += 1
            continue
        
        cnn = bf_info.get('cnn')
        side = bf_info.get('side')
        if not cnn or not side:
            skipped['no_cnn'] += 1
            continue
        
        # Get CNN geometry
        centerline = cnn_geometries.get(str(cnn))
        if not centerline:
            skipped['no_geometry'] += 1
            continue
        
        # Get meter coordinates
        location = meter.get('location')
        if not location:
            skipped['no_coordinates'] += 1
            continue
        
        try:
            lon = float(location.get('longitude'))
            lat = float(location.get('latitude'))
        except (TypeError, ValueError):
            skipped['no_coordinates'] += 1
            continue
        
        meter_point = Point(lon, lat)
        
        # Calculate offset
        offset = calculate_perpendicular_offset(meter_point, centerline)
        
        offset_data.append({
            'cnn': cnn,
            'side': side,
            'offset_meters': offset,
            'blockface_id': bf_id,
            'post_id': meter.get('post_id'),
            'street_name': bf_info.get('street_name')
        })
    
    print(f"✓ Analyzed {len(offset_data)} meters")
    print(f"  Skipped: {sum(skipped.values())} meters")
    for reason, count in skipped.items():
        if count > 0:
            print(f"    - {reason}: {count}")
    
    return offset_data


def build_calibration_model(offset_data):
    """
    Build calibration model from offset data.
    
    Returns:
        dict: Calibration model with statistics by side
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
            'version': '1.0'
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
    
    print(f"\nTotal samples: {model['metadata']['total_samples']}")
    print(f"Created: {model['metadata']['created_at']}")
    
    print("\nOffset Statistics by Side:")
    print("-" * 60)
    
    for side in ['L', 'R']:
        if side not in model['by_side']:
            continue
            
        stats = model['by_side'][side]
        print(f"\n{side} Side (n={stats['count']}):")
        print(f"  Mean:   {stats['mean']:>8.2f} meters")
        print(f"  Median: {stats['median']:>8.2f} meters")
        print(f"  Std:    {stats['std']:>8.2f} meters")
        print(f"  Range:  {stats['min']:>8.2f} to {stats['max']:>8.2f} meters")
        print(f"  IQR:    {stats['percentile_25']:>8.2f} to {stats['percentile_75']:>8.2f} meters")
    
    print("\n" + "="*60)
    print("\nInterpretation:")
    print("- Negative offsets = Left side of street")
    print("- Positive offsets = Right side of street")
    print("- Typical offset = distance from centerline to parking edge")
    print("="*60)


def main():
    """Main execution function."""
    print("="*60)
    print("BLOCKFACE OFFSET CALIBRATION")
    print("="*60)
    print("\nThis script analyzes parking meter locations to calibrate")
    print("the typical offset distance from CNN centerlines to actual")
    print("blockface edges.\n")
    
    # Step 1: Fetch data
    blockface_lookup = fetch_metered_blockfaces()
    meters = fetch_parking_meters()
    cnn_geometries = fetch_active_streets()
    
    # Step 2: Analyze offsets
    offset_data = analyze_offsets(meters, blockface_lookup, cnn_geometries)
    
    if not offset_data:
        print("\n❌ ERROR: No offset data collected. Cannot build calibration model.")
        return
    
    # Step 3: Build calibration model
    model = build_calibration_model(offset_data)
    
    # Step 4: Save model
    output_file = 'blockface_offset_calibration.json'
    with open(output_file, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n✓ Calibration model saved to: {output_file}")
    
    # Step 5: Save raw offset data for analysis
    raw_output_file = 'blockface_offset_raw_data.json'
    with open(raw_output_file, 'w') as f:
        json.dump(offset_data, f, indent=2)
    
    print(f"✓ Raw offset data saved to: {raw_output_file}")
    
    # Step 6: Print summary
    print_calibration_summary(model)
    
    print("\n✅ Calibration complete!")
    print("\nNext steps:")
    print("1. Review the calibration statistics above")
    print("2. Use this model to generate blockface geometries")
    print("3. Run: python generate_blockface_geometries.py")


if __name__ == "__main__":
    main()