#!/usr/bin/env python3
"""
Analyze multiple parking regulations at the same location using shape field.
Fetch data from Socrata and identify regulations with overlapping geometries.
"""

import requests
import json
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import os

# Get API token from environment
SFMTA_APP_TOKEN = os.getenv('SFMTA_APP_TOKEN', 'ApbiUQbkvnyKHOVCHUw1Dh4ic')

def fetch_sample_regulations(limit: int = 1000) -> List[Dict[str, Any]]:
    """Fetch sample regulations from Socrata API."""
    
    url = "https://data.sfgov.org/resource/hi6h-neyh.json"
    
    headers = {}
    if SFMTA_APP_TOKEN:
        headers['X-App-Token'] = SFMTA_APP_TOKEN
    
    try:
        response = requests.get(
            url,
            params={"$limit": limit},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying Socrata: {e}")
        return []

def extract_shape_key(reg: Dict[str, Any]) -> str:
    """Extract a hashable key from shape field for grouping."""
    
    shape = reg.get('shape')
    if not shape or not isinstance(shape, dict):
        return None
    
    # Use the shape's coordinates or a hash of the geometry
    coords = shape.get('coordinates', [])
    if not coords:
        return None
    
    # Convert to string for hashing
    return json.dumps(coords, sort_keys=True)

def analyze_overlapping_regulations(regulations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Group regulations by overlapping shapes."""
    
    print(f"\nAnalyzing {len(regulations)} regulations for shape overlaps...")
    
    # Group by shape
    by_shape = defaultdict(list)
    no_shape = []
    
    for reg in regulations:
        shape_key = extract_shape_key(reg)
        if shape_key:
            by_shape[shape_key].append(reg)
        else:
            no_shape.append(reg)
    
    print(f"  Unique shapes: {len(by_shape)}")
    print(f"  Regulations without shape: {len(no_shape)}")
    
    # Find groups with multiple regulations
    multi_reg_groups = {key: regs for key, regs in by_shape.items() if len(regs) > 1}
    print(f"  Shapes with multiple regulations: {len(multi_reg_groups)}")
    
    if len(by_shape) > 0:
        percentage = len(multi_reg_groups) / len(by_shape) * 100
        print(f"  Percentage: {percentage:.1f}%")
    
    # Distribution
    reg_counts = Counter(len(regs) for regs in by_shape.values())
    
    print(f"\n  Distribution of regulations per shape:")
    for count in sorted(reg_counts.keys()):
        print(f"    {count} regulation(s): {reg_counts[count]} shapes")
    
    return {
        'total_regulations': len(regulations),
        'unique_shapes': len(by_shape),
        'multi_reg_shapes': len(multi_reg_groups),
        'no_shape': len(no_shape),
        'groups': multi_reg_groups,
        'distribution': dict(reg_counts)
    }

def analyze_regulation_conflicts(regs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze if regulations are complementary or conflicting."""
    
    # Extract key fields
    types = [r.get('regulationtype', 'Unknown') for r in regs]
    time_limits = [r.get('timelimit') for r in regs if r.get('timelimit')]
    days = [r.get('daysofweek') for r in regs if r.get('daysofweek')]
    start_times = [r.get('starttime') for r in regs if r.get('starttime')]
    end_times = [r.get('endtime') for r in regs if r.get('endtime')]
    
    # Check for temporal restrictions
    has_time_restrictions = len(days) + len(start_times) + len(end_times)
    
    # Check for conflicting types
    unique_types = set(types)
    conflicting = False
    
    # Simple conflict detection
    if 'NO PARKING' in types or 'NO STOPPING' in types:
        if any('PARKING' in str(t) and 'NO' not in str(t) for t in types):
            conflicting = True
    
    return {
        'types': types,
        'unique_types': list(unique_types),
        'time_limits': time_limits,
        'days': days,
        'start_times': start_times,
        'end_times': end_times,
        'has_time_restrictions': has_time_restrictions > 0,
        'conflicting': conflicting,
        'complementary': has_time_restrictions > 0 and not conflicting
    }

def main():
    print("=" * 80)
    print("INVESTIGATING MULTIPLE PARKING REGULATIONS AT SAME LOCATION")
    print("Using Shape Field Overlap Analysis")
    print("=" * 80)
    
    # Fetch regulations
    print("\nFetching regulations from Socrata API...")
    regulations = fetch_sample_regulations(limit=5000)
    
    if not regulations:
        print("No regulations found!")
        return
    
    print(f"Retrieved {len(regulations)} regulations")
    
    # Show sample fields
    if regulations:
        print("\nSample regulation fields:")
        sample = regulations[0]
        for key in sorted(sample.keys())[:15]:
            value = sample[key]
            if isinstance(value, dict):
                print(f"  {key}: {type(value).__name__}")
            elif isinstance(value, list):
                print(f"  {key}: {type(value).__name__} ({len(value)} items)")
            else:
                val_str = str(value)[:50]
                print(f"  {key}: {val_str}")
    
    # Analyze overlaps
    analysis = analyze_overlapping_regulations(regulations)
    
    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES OF OVERLAPPING REGULATIONS")
    print("=" * 80)
    
    groups = analysis['groups']
    if not groups:
        print("\nNo overlapping regulations found!")
        print("This suggests that each regulation has a unique geometry.")
    else:
        # Sort by number of regulations (most first)
        sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
        examples = sorted_groups[:5]
        
        for i, (shape_key, regs) in enumerate(examples, 1):
            print(f"\nExample {i}: {len(regs)} regulations at same location")
            print("-" * 80)
            
            # Parse shape for display
            try:
                coords = json.loads(shape_key)
                if isinstance(coords, list) and len(coords) >= 2:
                    print(f"Geometry: LineString with {len(coords)} points")
                    print(f"  Start: {coords[0]}")
                    print(f"  End: {coords[-1]}")
            except:
                print(f"Geometry: (complex)")
            
            # Show each regulation
            for j, reg in enumerate(regs, 1):
                print(f"\n  Regulation {j}:")
                print(f"    Street: {reg.get('streetname', 'N/A')}")
                print(f"    Side: {reg.get('streetside', 'N/A')}")
                print(f"    Type: {reg.get('regulationtype', 'N/A')}")
                if reg.get('timelimit'):
                    print(f"    Time Limit: {reg.get('timelimit')}")
                if reg.get('daysofweek'):
                    print(f"    Days: {reg.get('daysofweek')}")
                if reg.get('starttime') or reg.get('endtime'):
                    print(f"    Hours: {reg.get('starttime', 'N/A')} - {reg.get('endtime', 'N/A')}")
            
            # Analyze conflicts
            conflict_analysis = analyze_regulation_conflicts(regs)
            print(f"\n  Analysis:")
            print(f"    Regulation types: {', '.join(conflict_analysis['unique_types'])}")
            
            if conflict_analysis['conflicting']:
                print(f"    ⚠️  CONFLICTING regulations detected!")
            elif conflict_analysis['complementary']:
                print(f"    ✓ Complementary regulations (different time periods)")
            else:
                print(f"    ℹ️  Similar regulations, may be redundant or data quality issue")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY AND RECOMMENDATIONS")
    print("=" * 80)
    
    total_shapes = analysis['unique_shapes']
    multi_shapes = analysis['multi_reg_shapes']
    
    if multi_shapes > 0 and total_shapes > 0:
        percentage = multi_shapes / total_shapes * 100
        print(f"\n✓ Multiple regulations at same location IS COMMON")
        print(f"  - {multi_shapes} out of {total_shapes} shapes have multiple regulations ({percentage:.1f}%)")
        print(f"  - This appears to be NORMAL/EXPECTED behavior")
        print(f"\nReasons for multiple regulations at same location:")
        print(f"  1. Different time periods (e.g., 2hr parking 9am-6pm, no parking 6pm-9am)")
        print(f"  2. Different days (e.g., street cleaning on Tuesdays, regular parking other days)")
        print(f"  3. Layered restrictions (e.g., RPP + time limit + metered parking)")
        print(f"  4. Seasonal or event-based variations")
        
        # Show distribution
        print(f"\nDistribution details:")
        dist = analysis['distribution']
        for count in sorted(dist.keys(), reverse=True)[:5]:
            print(f"  {count} regulations: {dist[count]} locations")
    else:
        print(f"\n✗ Multiple regulations at same location are RARE or NON-EXISTENT")
        print(f"  - Only {multi_shapes} out of {total_shapes} shapes have multiple regulations")
        print(f"  - This could indicate:")
        print(f"    1. Each regulation is spatially distinct")
        print(f"    2. Regulations are well-separated and don't overlap")
        print(f"    3. Dataset design: one regulation per geometry")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()