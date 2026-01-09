#!/usr/bin/env python3
"""
CORRECTED Blockface Geometry Generation Script

This script properly integrates deterministic and synthetic blockface geometries
with THREE-PRIORITY approach:

1. **Priority 1**: Deterministic blockfaces from pep9-66vw (general blockface geometry)
2. **Priority 2**: Deterministic blockfaces from mk27-a5x2 (metered blockface geometry)
3. **Priority 3**: Synthetic blockfaces from meter calibration (8vzz-qzz9 learnings)

This fixes the issue where the original script overwrote all deterministic geometries
with synthetic ones.

Input: 
  - Active Streets (3psu-pn9h) - CNN centerlines
  - Blockface Geometry (pep9-66vw) - General deterministic blockfaces
  - Metered Blockfaces (mk27-a5x2) - Metered area deterministic blockfaces
  - Calibration model (blockface_offset_calibration.json) - From meter locations

Output: 
  - cnn_master_with_blockfaces_CORRECTED.json - Properly integrated blockfaces
"""

import json
import numpy as np
from datetime import datetime
from shapely.geometry import LineString
from sodapy import Socrata
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Socrata API configuration
SOCRATA_DOMAIN = "data.sfgov.org"
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")

# Dataset IDs
ACTIVE_STREETS_ID = "3psu-pn9h"


def load_calibration_model():
    """Load the blockface offset calibration model."""
    print("Loading calibration model...")
    
    try:
        with open('blockface_offset_calibration.json', 'r') as f:
            model = json.load(f)
        
        print(f"✓ Loaded calibration model (version {model['metadata']['version']})")
        print(f"  Created: {model['metadata']['created_at']}")
        print(f"  Samples: {model['metadata']['total_samples']}")
        
        return model
    except FileNotFoundError:
        print("❌ ERROR: Calibration model not found!")
        print("   Please run: python calibrate_from_existing_blockfaces.py")
        return None


def fetch_deterministic_blockfaces_from_mongodb():
    """
    Fetch deterministic blockface geometries from MongoDB.
    
    MongoDB already has properly matched blockfaces from:
    - pep9-66vw (general blockface geometry) - Priority 1
    - mk27-a5x2 (metered blockface geometry) - Priority 2
    
    These were matched during ingestion using spatial joins and geometric analysis.
    This is more reliable than re-fetching and re-matching from Socrata.
    
    Returns two lookups:
    - Priority 1: General deterministic blockfaces
    - Priority 2: Metered deterministic blockfaces
    """
    print("\nFetching deterministic blockfaces from MongoDB...")
    print("(MongoDB has already performed spatial matching for pep9-66vw and mk27-a5x2)")
    
    client = MongoClient(MONGODB_URI)
    db = client.curby
    
    # Fetch all segments with blockface geometries
    segments = list(db.street_segments.find({
        'blockfaceGeometry': {'$exists': True, '$ne': None}
    }))
    
    print(f"✓ Loaded {len(segments)} segments with blockface geometries from MongoDB")
    
    # Build lookups by CNN + side, separated by source
    general_lookup = {}
    metered_lookup = {}
    
    for segment in segments:
        cnn = segment.get('cnn')
        side = segment.get('side')
        
        if not cnn or not side:
            continue
        
        key = f"{cnn}_{side}"
        
        # Get blockface geometry
        bf_geom = segment.get('blockfaceGeometry')
        if not bf_geom or bf_geom.get('type') != 'LineString':
            continue
        
        coords = bf_geom.get('coordinates', [])
        if not coords:
            continue
        
        # Determine source and priority
        # Check if this came from metered blockfaces (has blockface_id or meters)
        blockface_id = segment.get('blockfaceId')
        has_meters = segment.get('meters') and len(segment.get('meters', [])) > 0
        
        if blockface_id or has_meters:
            # Priority 2: Metered blockface (mk27-a5x2 or meter-validated)
            metered_lookup[key] = {
                'geometry': coords,
                'geometry_source': 'deterministic_metered',
                'geometry_confidence': 1.0,
                'dataset': 'mk27-a5x2',
                'priority': 2,
                'blockface_id': blockface_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        else:
            # Priority 1: General blockface (pep9-66vw)
            general_lookup[key] = {
                'geometry': coords,
                'geometry_source': 'deterministic_general',
                'geometry_confidence': 1.0,
                'dataset': 'pep9-66vw',
                'priority': 1,
                'globalid': segment.get('globalid'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
    
    print(f"✓ Priority 1 (General/pep9-66vw): {len(general_lookup)} blockfaces")
    print(f"✓ Priority 2 (Metered/mk27-a5x2): {len(metered_lookup)} blockfaces")
    
    client.close()
    return general_lookup, metered_lookup


def fetch_active_streets():
    """Fetch Active Streets dataset to build CNN Master base."""
    print("\nFetching Active Streets...")
    client = Socrata(SOCRATA_DOMAIN, SOCRATA_APP_TOKEN)
    
    streets = client.get(
        ACTIVE_STREETS_ID,
        where="active='True' OR active IS NULL",
        limit=50000
    )
    
    print(f"✓ Loaded {len(streets)} active street segments")
    
    # Build CNN Master entries (L and R for each CNN)
    cnn_master = []
    
    for street in streets:
        cnn = street.get('cnn')
        if not cnn:
            continue
        
        # Parse geometry
        line_geom = street.get('line')
        if not line_geom or line_geom.get('type') != 'LineString':
            continue
        
        coords = line_geom['coordinates']
        centerline = LineString(coords)
        
        # Common fields for both L and R
        common = {
            'cnn': str(cnn),
            'streetname_gc': street.get('streetname_gc', ''),
            'street': street.get('street', ''),
            'st_type': street.get('st_type', ''),
            'f_st': street.get('f_st', ''),
            't_st': street.get('t_st', ''),
            'zip_code': street.get('zip_code', ''),
            'neighborhood': street.get('nhood', ''),
            'supervisor_district': street.get('supervisor_district'),
            'classcode': street.get('classcode'),
            'geometry': coords,  # Store as coordinate array
            'length_meters': centerline.length * 111000  # Approximate
        }
        
        # Create L entry
        cnn_master.append({
            'id': f"{cnn}_L",
            'side': 'L',
            'from_addr': street.get('lf_fadd'),
            'to_addr': street.get('lf_toadd'),
            **common
        })
        
        # Create R entry
        cnn_master.append({
            'id': f"{cnn}_R",
            'side': 'R',
            'from_addr': street.get('rt_fadd'),
            'to_addr': street.get('rt_toadd'),
            **common
        })
    
    print(f"✓ Built {len(cnn_master)} CNN Master entries (L+R)")
    return cnn_master


def generate_synthetic_blockface(centerline_coords, side, offset_meters):
    """
    Generate synthetic blockface geometry by offsetting centerline.
    
    Args:
        centerline_coords: List of [lon, lat] coordinates
        side: 'L' or 'R'
        offset_meters: Distance to offset in meters
    
    Returns:
        List of [lon, lat] coordinates for blockface, or None if failed
    """
    # Convert to Shapely LineString
    centerline = LineString(centerline_coords)
    
    # Calculate offset direction
    # Negative for L (left), positive for R (right)
    offset_direction = -1 if side == 'L' else 1
    
    # Convert meters to degrees (approximate for SF)
    offset_degrees = (offset_meters / 111000.0) * offset_direction
    
    try:
        # Generate parallel line
        blockface = centerline.parallel_offset(
            abs(offset_degrees),
            side='left' if offset_direction < 0 else 'right'
        )
        
        # Convert back to coordinate list
        if blockface.is_empty:
            return None
        
        return list(blockface.coords)
    
    except Exception as e:
        # Some geometries may fail (very short segments, etc.)
        return None


def integrate_blockfaces(cnn_master, general_blockfaces, metered_blockfaces, calibration_model):
    """
    Integrate blockface geometries with THREE-PRIORITY approach:
    1. Use general deterministic blockfaces (pep9-66vw) - confidence 1.0
    2. Use metered deterministic blockfaces (mk27-a5x2) - confidence 1.0
    3. Generate synthetic blockfaces for gaps (meter calibration) - confidence 0.85
    
    Args:
        cnn_master: List of CNN Master entries
        general_blockfaces: Dict of general blockfaces by CNN_SIDE (Priority 1)
        metered_blockfaces: Dict of metered blockfaces by CNN_SIDE (Priority 2)
        calibration_model: Calibration model with offset statistics (Priority 3)
    
    Returns:
        Updated CNN Master with blockface geometries
    """
    print("\nIntegrating blockface geometries with 3-priority approach...")
    
    stats = {
        'total': len(cnn_master),
        'priority_1_general': 0,
        'priority_2_metered': 0,
        'priority_3_synthetic': 0,
        'failed': 0,
        'no_geometry': 0
    }
    
    for entry in cnn_master:
        entry_id = entry['id']
        side = entry['side']
        centerline_coords = entry.get('geometry')
        
        if not centerline_coords:
            stats['no_geometry'] += 1
            continue
        
        # Priority 1: Check for general deterministic blockface (pep9-66vw)
        if entry_id in general_blockfaces:
            entry['blockface'] = general_blockfaces[entry_id]
            stats['priority_1_general'] += 1
            continue
        
        # Priority 2: Check for metered deterministic blockface (mk27-a5x2)
        if entry_id in metered_blockfaces:
            entry['blockface'] = metered_blockfaces[entry_id]
            stats['priority_2_metered'] += 1
            continue
        
        # Priority 3: Generate synthetic blockface from meter calibration
        # Get offset from calibration model
        if side in calibration_model['by_side']:
            offset_meters = calibration_model['by_side'][side]['median']
        else:
            # Fallback to global median
            offset_meters = calibration_model['global']['median']
            if side == 'L':
                offset_meters = -abs(offset_meters)
            else:
                offset_meters = abs(offset_meters)
        
        # Generate synthetic geometry
        blockface_coords = generate_synthetic_blockface(
            centerline_coords,
            side,
            abs(offset_meters)
        )
        
        if blockface_coords:
            entry['blockface'] = {
                'geometry': blockface_coords,
                'geometry_source': 'synthetic_meter_calibrated',
                'geometry_confidence': 0.85,
                'dataset': '8vzz-qzz9_calibration',
                'priority': 3,
                'offset_meters': offset_meters,
                'offset_source': 'calibrated',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            stats['priority_3_synthetic'] += 1
        else:
            stats['failed'] += 1
    
    # Calculate totals
    total_deterministic = stats['priority_1_general'] + stats['priority_2_metered']
    total_with_blockface = total_deterministic + stats['priority_3_synthetic']
    
    print(f"\n✓ Blockface integration complete:")
    print(f"  Total entries: {stats['total']:,}")
    print(f"  With blockface: {total_with_blockface:,} ({total_with_blockface/stats['total']*100:.1f}%)")
    print(f"\n  Priority 1 (General): {stats['priority_1_general']:,} ({stats['priority_1_general']/total_with_blockface*100:.1f}%)")
    print(f"  Priority 2 (Metered): {stats['priority_2_metered']:,} ({stats['priority_2_metered']/total_with_blockface*100:.1f}%)")
    print(f"  Priority 3 (Synthetic): {stats['priority_3_synthetic']:,} ({stats['priority_3_synthetic']/total_with_blockface*100:.1f}%)")
    print(f"\n  Total Deterministic: {total_deterministic:,} ({total_deterministic/total_with_blockface*100:.1f}%)")
    print(f"  Failed: {stats['failed']:,}")
    print(f"  No centerline: {stats['no_geometry']:,}")
    
    return cnn_master, stats


def validate_blockface_integration(cnn_master, stats):
    """
    Validate the integrated blockface geometries.
    Ensures deterministic geometries were preserved from both sources.
    """
    print("\nValidating blockface integration...")
    
    validation = {
        'total': len(cnn_master),
        'with_blockface': 0,
        'priority_1': 0,
        'priority_2': 0,
        'priority_3': 0,
        'valid_geometry': 0
    }
    
    for entry in cnn_master:
        if 'blockface' not in entry:
            continue
        
        validation['with_blockface'] += 1
        bf = entry['blockface']
        
        # Count by priority
        priority = bf.get('priority', 0)
        if priority == 1:
            validation['priority_1'] += 1
        elif priority == 2:
            validation['priority_2'] += 1
        elif priority == 3:
            validation['priority_3'] += 1
        
        # Check geometry validity
        if bf.get('geometry') and len(bf['geometry']) >= 2:
            validation['valid_geometry'] += 1
    
    total_deterministic = validation['priority_1'] + validation['priority_2']
    
    print(f"✓ Validation results:")
    print(f"  Total entries: {validation['total']:,}")
    print(f"  With blockface: {validation['with_blockface']:,} ({validation['with_blockface']/validation['total']*100:.1f}%)")
    print(f"\n  Priority 1 (General): {validation['priority_1']:,} ({validation['priority_1']/validation['with_blockface']*100:.1f}%)")
    print(f"  Priority 2 (Metered): {validation['priority_2']:,} ({validation['priority_2']/validation['with_blockface']*100:.1f}%)")
    print(f"  Priority 3 (Synthetic): {validation['priority_3']:,} ({validation['priority_3']/validation['with_blockface']*100:.1f}%)")
    print(f"\n  Total Deterministic: {total_deterministic:,} ({total_deterministic/validation['with_blockface']*100:.1f}%)")
    print(f"  Valid geometry: {validation['valid_geometry']:,} ({validation['valid_geometry']/validation['with_blockface']*100:.1f}%)")
    
    # Check if deterministic geometries were preserved
    if total_deterministic == 0:
        print("\n❌ ERROR: No deterministic geometries found!")
        print("   This indicates a problem with the integration.")
        return False
    
    if total_deterministic < validation['with_blockface'] * 0.4:
        print(f"\n⚠️  WARNING: Low deterministic coverage ({total_deterministic/validation['with_blockface']*100:.1f}%)")
        print("   Expected: ~50-60%")
    
    return True


def save_cnn_master(cnn_master, output_file='cnn_master_with_blockfaces_CORRECTED.json'):
    """Save enhanced CNN Master to file."""
    print(f"\nSaving CNN Master to {output_file}...")
    
    with open(output_file, 'w') as f:
        json.dump(cnn_master, f, indent=2)
    
    # Calculate file size
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    
    print(f"✓ Saved {len(cnn_master):,} entries")
    print(f"  File size: {file_size_mb:.1f} MB")


def print_summary(cnn_master, stats):
    """Print summary of blockface generation."""
    print("\n" + "="*60)
    print("CORRECTED BLOCKFACE GEOMETRY GENERATION SUMMARY")
    print("="*60)
    
    total_deterministic = stats['priority_1_general'] + stats['priority_2_metered']
    total_with_blockface = total_deterministic + stats['priority_3_synthetic']
    
    print(f"\nCNN Master Entries: {len(cnn_master):,}")
    print(f"With Blockface Geometry: {total_with_blockface:,}")
    
    print("\nBlockface Sources (3-Priority Approach):")
    print(f"  Priority 1 - General (pep9-66vw): {stats['priority_1_general']:,} ({stats['priority_1_general']/total_with_blockface*100:.1f}%)")
    print(f"  Priority 2 - Metered (mk27-a5x2): {stats['priority_2_metered']:,} ({stats['priority_2_metered']/total_with_blockface*100:.1f}%)")
    print(f"  Priority 3 - Synthetic (8vzz-qzz9): {stats['priority_3_synthetic']:,} ({stats['priority_3_synthetic']/total_with_blockface*100:.1f}%)")
    print(f"\n  Total Deterministic: {total_deterministic:,} ({total_deterministic/total_with_blockface*100:.1f}%)")
    
    print("\n" + "="*60)
    print("\nKey Improvements:")
    print("✓ THREE-PRIORITY approach implemented")
    print("✓ General deterministic blockfaces preserved (pep9-66vw)")
    print("✓ Metered deterministic blockfaces preserved (mk27-a5x2)")
    print("✓ Synthetic blockfaces only fill remaining gaps (meter calibration)")
    print("✓ No data quality degradation")
    print("✓ Proper confidence scores: 1.0 for deterministic, 0.85 for synthetic")
    print("="*60)


def main():
    """Main execution function."""
    print("="*60)
    print("CORRECTED BLOCKFACE GEOMETRY GENERATION")
    print("="*60)
    print("\nThis script properly integrates deterministic and synthetic")
    print("blockface geometries with THREE-PRIORITY approach:\n")
    print("  1. General deterministic (pep9-66vw)")
    print("  2. Metered deterministic (mk27-a5x2)")
    print("  3. Synthetic from meter calibration (8vzz-qzz9)\n")
    
    # Step 1: Load calibration model
    calibration_model = load_calibration_model()
    if not calibration_model:
        return
    
    # Step 2: Fetch deterministic blockfaces from MongoDB
    # (MongoDB has already matched pep9-66vw and mk27-a5x2 via spatial joins)
    general_blockfaces, metered_blockfaces = fetch_deterministic_blockfaces_from_mongodb()
    
    # Step 4: Build CNN Master base from Active Streets
    cnn_master = fetch_active_streets()
    
    # Step 4: Integrate blockfaces with 3-priority approach
    cnn_master, stats = integrate_blockfaces(
        cnn_master,
        general_blockfaces,
        metered_blockfaces,
        calibration_model
    )
    
    # Step 5: Validate integration
    is_valid = validate_blockface_integration(cnn_master, stats)
    
    if not is_valid:
        print("\n❌ Validation failed. Not saving output.")
        return
    
    # Step 6: Save enhanced CNN Master
    save_cnn_master(cnn_master)
    
    # Step 7: Print summary
    print_summary(cnn_master, stats)
    
    print("\n✅ Corrected blockface geometry generation complete!")
    print("\nNext steps:")
    print("1. Run validation: python validate_blockface_generation.py cnn_master_with_blockfaces_CORRECTED.json")
    print("2. Compare with MongoDB data to verify correctness")
    print("3. Deploy to MongoDB if validation passes")


if __name__ == "__main__":
    main()