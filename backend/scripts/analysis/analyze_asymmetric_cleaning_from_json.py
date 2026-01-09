z#!/usr/bin/env python3
"""
Analyze asymmetric street cleaning patterns from existing segments data.
This script identifies cases where street cleaning schedules differ between sides.
"""

import json
from collections import defaultdict
from typing import Dict, List, Set

def normalize_days(day_str: str) -> str:
    """Normalize day abbreviations"""
    day_map = {
        'Mon': 'Monday', 'Tues': 'Tuesday', 'Wed': 'Wednesday',
        'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday', 'Sun': 'Sunday'
    }
    return day_map.get(day_str, day_str)

def analyze_asymmetric_patterns():
    """Analyze street cleaning asymmetry from segments_with_sweeping_rules.json"""
    
    # Load the data
    with open('segments_with_sweeping_rules.json', 'r') as f:
        segments = json.load(f)
    
    print(f"Loaded {len(segments)} segments with sweeping rules")
    
    # Group by CNN
    cnn_groups = defaultdict(list)
    for segment in segments:
        cnn = segment.get('cnn')
        if cnn:
            cnn_groups[cnn].append(segment)
    
    print(f"Found {len(cnn_groups)} unique CNN segments")
    
    # Analyze patterns
    asymmetric_cases = {
        'different_days': [],
        'different_times': [],
        'different_frequency': [],
        'time_mismatch': []
    }
    
    symmetric_count = 0
    
    for cnn, segs in cnn_groups.items():
        if len(segs) != 2:
            continue
        
        # Sort by side
        segs.sort(key=lambda x: x.get('side', ''))
        left = segs[0] if segs[0].get('side') == 'L' else segs[1]
        right = segs[1] if segs[1].get('side') == 'R' else segs[0]
        
        left_rule = left.get('sample_rule', {})
        right_rule = right.get('sample_rule', {})
        
        left_day = normalize_days(left_rule.get('day', ''))
        right_day = normalize_days(right_rule.get('day', ''))
        
        left_time = f"{left_rule.get('startTime', '')}-{left_rule.get('endTime', '')}"
        right_time = f"{right_rule.get('startTime', '')}-{right_rule.get('endTime', '')}"
        
        left_count = left.get('sweeping_count', 0)
        right_count = right.get('sweeping_count', 0)
        
        # Check for different days
        if left_day != right_day:
            asymmetric_cases['different_days'].append({
                'cnn': cnn,
                'street': left.get('displayName', '').split('(')[0].strip(),
                'left_side': left.get('displayName', ''),
                'right_side': right.get('displayName', ''),
                'left_day': left_day,
                'right_day': right_day,
                'left_time': left_time,
                'right_time': right_time
            })
        # Check for different times (same day)
        elif left_time != right_time:
            asymmetric_cases['different_times'].append({
                'cnn': cnn,
                'street': left.get('displayName', '').split('(')[0].strip(),
                'left_side': left.get('displayName', ''),
                'right_side': right.get('displayName', ''),
                'day': left_day,
                'left_time': left_time,
                'right_time': right_time
            })
        # Check for different frequency
        elif left_count != right_count:
            asymmetric_cases['different_frequency'].append({
                'cnn': cnn,
                'street': left.get('displayName', '').split('(')[0].strip(),
                'left_side': left.get('displayName', ''),
                'right_side': right.get('displayName', ''),
                'left_count': left_count,
                'right_count': right_count
            })
        else:
            symmetric_count += 1
    
    # Generate report
    print("\n" + "="*80)
    print("ASYMMETRIC STREET CLEANING ANALYSIS")
    print("="*80)
    
    total_with_both_sides = len([cnn for cnn, segs in cnn_groups.items() if len(segs) == 2])
    total_asymmetric = sum(len(cases) for cases in asymmetric_cases.values())
    
    print(f"\nSegments with both L and R sides: {total_with_both_sides}")
    print(f"Symmetric cleaning: {symmetric_count} ({symmetric_count/total_with_both_sides*100:.1f}%)")
    print(f"Asymmetric cleaning: {total_asymmetric} ({total_asymmetric/total_with_both_sides*100:.1f}%)")
    
    print("\n" + "-"*80)
    print("ASYMMETRY BREAKDOWN:")
    print("-"*80)
    
    # Different days
    if asymmetric_cases['different_days']:
        print(f"\n1. DIFFERENT CLEANING DAYS: {len(asymmetric_cases['different_days'])} cases")
        print("   (Both sides cleaned but on different days of the week)")
        print("\n   Top 10 examples:")
        for i, case in enumerate(asymmetric_cases['different_days'][:10], 1):
            print(f"\n   {i}. {case['street']} (CNN: {case['cnn']})")
            print(f"      Left:  {case['left_day']} {case['left_time']}")
            print(f"      Right: {case['right_day']} {case['right_time']}")
    
    # Different times
    if asymmetric_cases['different_times']:
        print(f"\n2. DIFFERENT CLEANING TIMES: {len(asymmetric_cases['different_times'])} cases")
        print("   (Same day but different time windows)")
        print("\n   Top 10 examples:")
        for i, case in enumerate(asymmetric_cases['different_times'][:10], 1):
            print(f"\n   {i}. {case['street']} (CNN: {case['cnn']})")
            print(f"      Day: {case['day']}")
            print(f"      Left:  {case['left_time']}")
            print(f"      Right: {case['right_time']}")
    
    # Different frequency
    if asymmetric_cases['different_frequency']:
        print(f"\n3. DIFFERENT CLEANING FREQUENCY: {len(asymmetric_cases['different_frequency'])} cases")
        print("   (Different number of cleaning schedules per week)")
        print("\n   Top 10 examples:")
        for i, case in enumerate(asymmetric_cases['different_frequency'][:10], 1):
            print(f"\n   {i}. {case['street']} (CNN: {case['cnn']})")
            print(f"      Left:  {case['left_count']} schedule(s)")
            print(f"      Right: {case['right_count']} schedule(s)")
    
    # Save detailed results
    output_file = 'asymmetric_cleaning_analysis.json'
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_segments_with_both_sides': total_with_both_sides,
                'symmetric': symmetric_count,
                'asymmetric': total_asymmetric,
                'symmetric_percentage': round(symmetric_count/total_with_both_sides*100, 2),
                'asymmetric_percentage': round(total_asymmetric/total_with_both_sides*100, 2)
            },
            'patterns': asymmetric_cases
        }, f, indent=2)
    
    print(f"\n\nDetailed results saved to: {output_file}")
    
    # Analysis insights
    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    
    if total_asymmetric > 0:
        print("\n✓ Asymmetric street cleaning is COMMON in San Francisco")
        print("  This is typically intentional to:")
        print("  - Distribute cleaning across different days")
        print("  - Minimize parking disruption")
        print("  - Optimize street sweeper routes")
        
        if asymmetric_cases['different_days']:
            pct = len(asymmetric_cases['different_days']) / total_asymmetric * 100
            print(f"\n✓ Most common pattern: Different days ({pct:.1f}% of asymmetric cases)")
            print("  - Allows residents to park on one side while other is cleaned")
            print("  - Standard practice in most cities")
        
        if asymmetric_cases['different_frequency']:
            print(f"\n⚠ Different frequency detected: {len(asymmetric_cases['different_frequency'])} cases")
            print("  - May indicate data quality issues")
            print("  - Or legitimate policy differences (e.g., one side busier)")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    analyze_asymmetric_patterns()
