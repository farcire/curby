#!/usr/bin/env python3
"""
Blockface Offset Calibration Script V2

Uses existing CNN Master file with meter mappings to calibrate blockface offsets.
This version doesn't need to fetch from Socrata - it uses the already-integrated data.

This script:
1. Loads CNN Master file (with meters already mapped to CNN+side)
2. Loads Active Streets for CNN centerline geometries
3. Calculates perpendicular distance from each meter to its CNN centerline
4. Analyzes offset patterns by side (L/R)
5. Generates calibration model for synthetic blockface generation

Output: blockface_offset_calibration.json
"""

import json
import numpy as np
from datetime import datetime
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
ACTIVE_STREETS_ID = "3psu-pn9h"


def load_cnn_master():
    """Load CNN Master file with meter mappings."""
    print("Loading CNN Master file...")
    with open('cnn_master_reference.json', 'r') as f:
        cnn_master = json.load(f)
    
    print(f"✓ Loaded {len(cnn_master)} CNN Master entries")
    return cnn_master


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


def analyze_offsets_from_cnn_master(cnn_master, cnn_geometries):
    """
    Analyze offset patterns from CNN Master data.
    
    Returns:
        list: Offset data for each meter
    """
    print("\nAnalyzing meter offsets from CNN Master...")
    
    offset_data = []
    skipped = {
        'no_meters': 0,
        'no_geometry': 0,
        'no_coordinates': 0,
        'invalid_side': 0
    }
    
    for entry in cnn_master:
        cnn = entry.get('cnn')
        side = entry.get('side')
        
        if not cnn or not side or side not in ['L', 'R']:
            continue
        
        # Get CNN geometry (centerline)
        centerline = cnn_geometries.get(str(cnn))
        if not centerline:
            skipped['no_geometry'] += 1
            continue
        
        # Get meters for this CNN+side
        meters = entry.get('meters', [])
        if not meters:
            skipped['no_meters'] += 1
            continue
        
        for meter in meters:
            # Get meter coordinates
            location = meter.get('location')
            if not location:
                skipped['no_coordinates'] += 1
                continue
            
            try:
                lon = float(location.get('longitude'))
                lat = float(location.get('latitude'))
            except (TypeError, ValueError, AttributeError):
                skipped['no_coordinates'] += 1
                continue
            
            meter_point = Point(lon, lat)
            
            # Calculate offset from meter to CNN centerline
            offset = calculate_perpendicular_offset(meter_point, centerline)
            
            offset_data.append({
                'cnn': cnn,
                'side': side,
                'offset_meters': offset,
                'post_id': meter.get('post_id'),
                'street_name': entry.get('street_name', 'Unknown')
            })
    
    print(f"✓ Analyzed {len(offset_data)} meters")
    print(f"  Skipped: {sum(skipped.values())} entries")
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
            'version': '2.0',
            'source': 'cnn_master_reference.json'
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
    print(f"Source: {model['metadata']['source']}")
    
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
    print("BLOCKFACE OFFSET CALIBRATION V2")
    print("="*60)
    print("\nThis script uses the CNN Master file to calibrate")
    print("the typical offset distance from CNN centerlines to actual")
    print("blockface edges.\n")
    
    # Step 1: Load CNN Master
    cnn_master = load_cnn_master()
    
    # Step 2: Fetch Active Streets geometries
    cnn_geometries = fetch_active_streets()
    
    # Step 3: Analyze offsets
    offset_data = analyze_offsets_from_cnn_master(cnn_master, cnn_geometries)
    
    if not offset_data:
        print("\n❌ ERROR: No offset data collected. Cannot build calibration model.")
        return
    
    # Step 4: Build calibration model
    model = build_calibration_model(offset_data)
    
    # Step 5: Save model
    output_file = 'blockface_offset_calibration.json'
    with open(output_file, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n✓ Calibration model saved to: {output_file}")
    
    # Step 6: Save raw offset data for analysis
    raw_output_file = 'blockface_offset_raw_data.json'
    with open(raw_output_file, 'w') as f:
        json.dump(offset_data, f, indent=2)
    
    print(f"✓ Raw offset data saved to: {raw_output_file}")
    
    # Step 7: Print summary
    print_calibration_summary(model)
    
    print("\n✅ Calibration complete!")
    print("\nNext steps:")
    print("1. Review the calibration statistics above")
    print("2. Use this model to generate blockface geometries")
    print("3. Run: python generate_blockface_geometries.py")


if __name__ == "__main__":
    main()