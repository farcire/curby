#!/usr/bin/env python3
"""
Validation Check for Blockface Generation

Prevents accidental overwriting of deterministic blockface geometries
with synthetic ones. Run this before deploying any blockface data.

Usage:
    python validate_blockface_generation.py <file_to_validate.json>
"""

import json
import sys
from pathlib import Path


def validate_blockface_file(filepath):
    """
    Validate that a blockface file preserves deterministic geometries.
    
    Returns:
        tuple: (is_valid, error_messages, stats)
    """
    print(f"Validating: {filepath}")
    print("=" * 60)
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"Failed to load file: {e}"], {}
    
    errors = []
    warnings = []
    stats = {
        'total_entries': len(data),
        'with_blockface': 0,
        'deterministic': 0,
        'synthetic': 0,
        'meter_calibrated': 0,
        'unknown_source': 0
    }
    
    # Analyze each entry
    for entry in data:
        if 'blockface' not in entry:
            continue
        
        stats['with_blockface'] += 1
        blockface = entry['blockface']
        
        # Check geometry source
        source = blockface.get('geometry_source', 'unknown')
        
        if source == 'deterministic' or source == 'pep9_blockface':
            stats['deterministic'] += 1
        elif source == 'synthetic' or source == 'meter_calibrated':
            stats['synthetic'] += 1
            if source == 'meter_calibrated':
                stats['meter_calibrated'] += 1
        else:
            stats['unknown_source'] += 1
            warnings.append(f"Entry {entry.get('id')} has unknown source: {source}")
    
    # Validation rules
    print("\nValidation Results:")
    print("-" * 60)
    
    # Rule 1: Must have some deterministic geometries
    deterministic_pct = (stats['deterministic'] / stats['with_blockface'] * 100) if stats['with_blockface'] > 0 else 0
    
    if stats['deterministic'] == 0 and stats['with_blockface'] > 0:
        errors.append(
            "❌ CRITICAL: No deterministic blockface geometries found!\n"
            "   Expected: ~50-60% deterministic from pep9-66vw dataset\n"
            "   Found: 0% deterministic\n"
            "   This indicates deterministic geometries were overwritten."
        )
    elif deterministic_pct < 40:
        warnings.append(
            f"⚠️  WARNING: Low deterministic geometry coverage: {deterministic_pct:.1f}%\n"
            f"   Expected: ~50-60%\n"
            f"   This may indicate missing deterministic data."
        )
    else:
        print(f"✓ Deterministic coverage: {deterministic_pct:.1f}% (Good)")
    
    # Rule 2: Check if ALL geometries are synthetic (red flag)
    if stats['meter_calibrated'] == stats['with_blockface'] and stats['with_blockface'] > 0:
        errors.append(
            "❌ CRITICAL: ALL blockface geometries are synthetic (meter_calibrated)!\n"
            "   This file was generated without checking for deterministic geometries.\n"
            "   DO NOT DEPLOY - This will overwrite high-quality data."
        )
    
    # Print statistics
    print(f"\nStatistics:")
    print(f"  Total entries: {stats['total_entries']:,}")
    print(f"  With blockface: {stats['with_blockface']:,}")
    print(f"  Deterministic: {stats['deterministic']:,} ({deterministic_pct:.1f}%)")
    print(f"  Synthetic: {stats['synthetic']:,} ({stats['synthetic']/stats['with_blockface']*100:.1f}%)")
    
    # Print errors and warnings
    if errors:
        print("\n" + "=" * 60)
        print("ERRORS:")
        print("=" * 60)
        for error in errors:
            print(error)
    
    if warnings:
        print("\n" + "=" * 60)
        print("WARNINGS:")
        print("=" * 60)
        for warning in warnings:
            print(warning)
    
    # Final verdict
    print("\n" + "=" * 60)
    is_valid = len(errors) == 0
    
    if is_valid:
        print("✅ VALIDATION PASSED")
        print("This file appears to preserve deterministic geometries.")
    else:
        print("❌ VALIDATION FAILED")
        print("DO NOT DEPLOY THIS FILE - It will corrupt the database.")
    
    print("=" * 60)
    
    return is_valid, errors, stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_blockface_generation.py <file_to_validate.json>")
        print("\nExample:")
        print("  python validate_blockface_generation.py cnn_master_with_blockfaces.json")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not Path(filepath).exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    is_valid, errors, stats = validate_blockface_file(filepath)
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()