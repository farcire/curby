#!/usr/bin/env python3
"""
Analyze street cleaning dataset for asymmetric patterns.

Asymmetric street cleaning occurs when:
1. One side of a street has cleaning schedules but the other doesn't
2. Both sides have cleaning but on different days/times
3. One side has multiple cleaning days while the other has fewer

This can indicate data quality issues or legitimate policy differences.
"""

import json
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from pymongo import MongoClient

def connect_db():
    """Connect to MongoDB"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['curby']
    return db

def extract_cleaning_schedule(rules: List[Dict]) -> List[Dict]:
    """Extract street cleaning schedules from rules"""
    cleaning_schedules = []
    for rule in rules:
        if rule.get('type') == 'street-sweeping':
            source_fields = rule.get('source_fields', {})
            cleaning_schedules.append({
                'days': source_fields.get('days', ''),
                'hours': source_fields.get('hours', ''),
                'from_time': source_fields.get('from_time', ''),
                'to_time': source_fields.get('to_time', ''),
                'source_text': rule.get('source_text', '')
            })
    return cleaning_schedules

def normalize_days(days_str: str) -> Set[str]:
    """Normalize day strings to a set of day names"""
    if not days_str:
        return set()
    
    # Common day abbreviations
    day_map = {
        'MON': 'Monday', 'MONDAY': 'Monday',
        'TUE': 'Tuesday', 'TUES': 'Tuesday', 'TUESDAY': 'Tuesday',
        'WED': 'Wednesday', 'WEDNESDAY': 'Wednesday',
        'THU': 'Thursday', 'THUR': 'Thursday', 'THURS': 'Thursday', 'THURSDAY': 'Thursday',
        'FRI': 'Friday', 'FRIDAY': 'Friday',
        'SAT': 'Saturday', 'SATURDAY': 'Saturday',
        'SUN': 'Sunday', 'SUNDAY': 'Sunday'
    }
    
    days_upper = days_str.upper()
    found_days = set()
    
    for abbr, full_name in day_map.items():
        if abbr in days_upper:
            found_days.add(full_name)
    
    return found_days

def analyze_asymmetric_cleaning():
    """Main analysis function"""
    db = connect_db()
    segments = db.street_segments
    
    # Group segments by CNN
    cnn_groups = defaultdict(list)
    
    print("Loading street segments...")
    for segment in segments.find({}):
        cnn = segment.get('cnn')
        if cnn:
            cnn_groups[cnn].append(segment)
    
    print(f"Found {len(cnn_groups)} unique CNN segments")
    
    # Analyze asymmetry patterns
    asymmetric_cases = {
        'one_side_only': [],           # Only one side has cleaning
        'different_days': [],           # Both sides but different days
        'different_frequency': [],      # Different number of cleaning days
        'different_times': [],          # Same days but different times
        'missing_schedule_data': []     # Has cleaning rule but missing schedule details
    }
    
    symmetric_count = 0
    no_cleaning_count = 0
    
    for cnn, segments_list in cnn_groups.items():
        if len(segments_list) != 2:
            continue  # Skip if not exactly 2 sides
        
        # Sort by side to ensure consistent ordering
        segments_list.sort(key=lambda x: x.get('side', ''))
        left_seg = segments_list[0] if segments_list[0].get('side') == 'L' else segments_list[1]
        right_seg = segments_list[1] if segments_list[1].get('side') == 'R' else segments_list[0]
        
        left_cleaning = extract_cleaning_schedule(left_seg.get('rules', []))
        right_cleaning = extract_cleaning_schedule(right_seg.get('rules', []))
        
        # Case 1: No cleaning on either side
        if not left_cleaning and not right_cleaning:
            no_cleaning_count += 1
            continue
        
        # Case 2: One side only
        if bool(left_cleaning) != bool(right_cleaning):
            asymmetric_cases['one_side_only'].append({
                'cnn': cnn,
                'street_name': left_seg.get('streetName', 'Unknown'),
                'side_with_cleaning': 'L' if left_cleaning else 'R',
                'side_without_cleaning': 'R' if left_cleaning else 'L',
                'cleaning_schedule': left_cleaning if left_cleaning else right_cleaning,
                'from_street': left_seg.get('fromStreet'),
                'to_street': left_seg.get('toStreet')
            })
            continue
        
        # Case 3: Both sides have cleaning - analyze differences
        if left_cleaning and right_cleaning:
            # Extract days from all schedules
            left_days = set()
            right_days = set()
            left_times = []
            right_times = []
            
            for schedule in left_cleaning:
                left_days.update(normalize_days(schedule.get('days', '')))
                time_str = f"{schedule.get('from_time', '')}-{schedule.get('to_time', '')}"
                if time_str != '-':
                    left_times.append(time_str)
            
            for schedule in right_cleaning:
                right_days.update(normalize_days(schedule.get('days', '')))
                time_str = f"{schedule.get('from_time', '')}-{schedule.get('to_time', '')}"
                if time_str != '-':
                    right_times.append(time_str)
            
            # Check for missing schedule data
            if not left_days or not right_days:
                asymmetric_cases['missing_schedule_data'].append({
                    'cnn': cnn,
                    'street_name': left_seg.get('streetName', 'Unknown'),
                    'left_days': list(left_days),
                    'right_days': list(right_days),
                    'left_schedules': left_cleaning,
                    'right_schedules': right_cleaning
                })
                continue
            
            # Check if days are different
            if left_days != right_days:
                asymmetric_cases['different_days'].append({
                    'cnn': cnn,
                    'street_name': left_seg.get('streetName', 'Unknown'),
                    'left_days': sorted(list(left_days)),
                    'right_days': sorted(list(right_days)),
                    'left_only': sorted(list(left_days - right_days)),
                    'right_only': sorted(list(right_days - left_days)),
                    'from_street': left_seg.get('fromStreet'),
                    'to_street': left_seg.get('toStreet')
                })
                continue
            
            # Check if frequency is different
            if len(left_cleaning) != len(right_cleaning):
                asymmetric_cases['different_frequency'].append({
                    'cnn': cnn,
                    'street_name': left_seg.get('streetName', 'Unknown'),
                    'left_count': len(left_cleaning),
                    'right_count': len(right_cleaning),
                    'left_schedules': left_cleaning,
                    'right_schedules': right_cleaning
                })
                continue
            
            # Check if times are different (same days)
            if set(left_times) != set(right_times):
                asymmetric_cases['different_times'].append({
                    'cnn': cnn,
                    'street_name': left_seg.get('streetName', 'Unknown'),
                    'days': sorted(list(left_days)),
                    'left_times': left_times,
                    'right_times': right_times,
                    'from_street': left_seg.get('fromStreet'),
                    'to_street': left_seg.get('toStreet')
                })
                continue
            
            # If we get here, it's symmetric
            symmetric_count += 1
    
    # Generate report
    print("\n" + "="*80)
    print("ASYMMETRIC STREET CLEANING ANALYSIS")
    print("="*80)
    
    print(f"\nTotal CNN segments analyzed: {len(cnn_groups)}")
    print(f"Segments with no cleaning on either side: {no_cleaning_count}")
    print(f"Segments with symmetric cleaning: {symmetric_count}")
    
    print("\n" + "-"*80)
    print("ASYMMETRY PATTERNS FOUND:")
    print("-"*80)
    
    for pattern_type, cases in asymmetric_cases.items():
        print(f"\n{pattern_type.upper().replace('_', ' ')}: {len(cases)} cases")
        
        if cases:
            print(f"\nTop 10 examples:")
            for i, case in enumerate(cases[:10], 1):
                print(f"\n  {i}. {case.get('street_name', 'Unknown')} (CNN: {case.get('cnn')})")
                
                if pattern_type == 'one_side_only':
                    print(f"     Side with cleaning: {case['side_with_cleaning']}")
                    print(f"     Side without cleaning: {case['side_without_cleaning']}")
                    if case.get('from_street') and case.get('to_street'):
                        print(f"     Between: {case['from_street']} and {case['to_street']}")
                
                elif pattern_type == 'different_days':
                    print(f"     Left side: {', '.join(case['left_days'])}")
                    print(f"     Right side: {', '.join(case['right_days'])}")
                    if case.get('left_only'):
                        print(f"     Left only: {', '.join(case['left_only'])}")
                    if case.get('right_only'):
                        print(f"     Right only: {', '.join(case['right_only'])}")
                
                elif pattern_type == 'different_frequency':
                    print(f"     Left side: {case['left_count']} schedules")
                    print(f"     Right side: {case['right_count']} schedules")
                
                elif pattern_type == 'different_times':
                    print(f"     Days: {', '.join(case['days'])}")
                    print(f"     Left times: {', '.join(case['left_times'])}")
                    print(f"     Right times: {', '.join(case['right_times'])}")
                
                elif pattern_type == 'missing_schedule_data':
                    print(f"     Left days: {case['left_days']}")
                    print(f"     Right days: {case['right_days']}")
    
    # Save detailed results to JSON
    output_file = 'backend/asymmetric_street_cleaning_report.json'
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_cnn_segments': len(cnn_groups),
                'no_cleaning': no_cleaning_count,
                'symmetric': symmetric_count,
                'asymmetric_total': sum(len(cases) for cases in asymmetric_cases.values())
            },
            'asymmetric_cases': asymmetric_cases
        }, f, indent=2)
    
    print(f"\n\nDetailed results saved to: {output_file}")
    
    # Generate summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    total_asymmetric = sum(len(cases) for cases in asymmetric_cases.values())
    total_with_cleaning = symmetric_count + total_asymmetric
    
    if total_with_cleaning > 0:
        print(f"\nOf segments with street cleaning:")
        print(f"  Symmetric: {symmetric_count} ({symmetric_count/total_with_cleaning*100:.1f}%)")
        print(f"  Asymmetric: {total_asymmetric} ({total_asymmetric/total_with_cleaning*100:.1f}%)")
        
        print(f"\nAsymmetry breakdown:")
        for pattern_type, cases in asymmetric_cases.items():
            if total_asymmetric > 0:
                pct = len(cases) / total_asymmetric * 100
                print(f"  {pattern_type.replace('_', ' ').title()}: {len(cases)} ({pct:.1f}%)")

if __name__ == '__main__':
    analyze_asymmetric_cleaning()