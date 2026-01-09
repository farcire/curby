#!/usr/bin/env python3
"""
Analyze street cleaning dataset for missing schedules on one side.

This identifies TRUE data gaps where one side of a street has cleaning
schedules but the opposite side has NO cleaning schedules at all.
"""

import json
from collections import defaultdict

def analyze_missing_side_cleaning():
    """Find segments where one side has cleaning but the other side doesn't"""
    
    # Load the data
    with open('segments_with_sweeping_rules.json', 'r') as f:
        segments = json.load(f)
    
    print(f"Loaded {len(segments)} segments with sweeping rules")
    
    # Group by CNN to find which CNNs have both sides
    cnn_sides = defaultdict(set)
    cnn_data = {}
    
    for segment in segments:
        cnn = segment.get('cnn')
        side = segment.get('side')
        if cnn and side:
            cnn_sides[cnn].add(side)
            cnn_data[f"{cnn}_{side}"] = segment
    
    # Find CNNs with only one side having cleaning
    missing_side_cases = []
    
    for cnn, sides in cnn_sides.items():
        if len(sides) == 1:
            # Only one side has cleaning - this is a potential data gap
            present_side = list(sides)[0]
            missing_side = 'R' if present_side == 'L' else 'L'
            
            segment_data = cnn_data[f"{cnn}_{present_side}"]
            
            missing_side_cases.append({
                'cnn': cnn,
                'street_name': segment_data.get('displayName', '').split('(')[0].strip(),
                'present_side': present_side,
                'present_side_display': segment_data.get('displayName', ''),
                'missing_side': missing_side,
                'cleaning_schedule': segment_data.get('sample_rule', {}),
                'sweeping_count': segment_data.get('sweeping_count', 0)
            })
    
    # Sort by street name for easier review
    missing_side_cases.sort(key=lambda x: x['street_name'])
    
    # Generate report
    print("\n" + "="*80)
    print("MISSING STREET CLEANING ANALYSIS")
    print("="*80)
    print("\nIdentifying segments where ONE side has cleaning but the OTHER side is MISSING")
    print("(This excludes normal asymmetry where both sides have different schedules)")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total segments with cleaning: {len(segments)}")
    print(f"   Unique CNN segments: {len(cnn_sides)}")
    print(f"   CNNs with BOTH sides having cleaning: {sum(1 for sides in cnn_sides.values() if len(sides) == 2)}")
    print(f"   CNNs with ONLY ONE side having cleaning: {len(missing_side_cases)}")
    
    if missing_side_cases:
        print("\n" + "-"*80)
        print(f"⚠️  FOUND {len(missing_side_cases)} CASES WITH MISSING CLEANING ON ONE SIDE")
        print("-"*80)
        
        print("\nThese are potential data quality issues where street cleaning may be missing:")
        
        # Show all cases (they're important for data quality)
        for i, case in enumerate(missing_side_cases, 1):
            print(f"\n{i}. {case['street_name']} (CNN: {case['cnn']})")
            print(f"   ✓ {case['present_side']} side HAS cleaning: {case['present_side_display']}")
            print(f"   ✗ {case['missing_side']} side MISSING cleaning")
            
            # Show the schedule that exists
            schedule = case['cleaning_schedule']
            if schedule:
                day = schedule.get('day', 'Unknown')
                start = schedule.get('startTime', '?')
                end = schedule.get('endTime', '?')
                print(f"   Existing schedule: {day} {start}:00-{end}:00")
    else:
        print("\n✅ NO MISSING SIDES FOUND")
        print("   All CNN segments that have cleaning have it on BOTH sides.")
    
    # Save detailed results
    output_file = 'missing_side_cleaning_report.json'
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_segments': len(segments),
                'unique_cnns': len(cnn_sides),
                'cnns_with_both_sides': sum(1 for sides in cnn_sides.values() if len(sides) == 2),
                'cnns_with_one_side_only': len(missing_side_cases),
                'data_quality_issue': len(missing_side_cases) > 0
            },
            'missing_side_cases': missing_side_cases
        }, f, indent=2)
    
    print(f"\n\n📄 Detailed results saved to: {output_file}")
    
    # Analysis insights
    print("\n" + "="*80)
    print("ANALYSIS INSIGHTS:")
    print("="*80)
    
    if missing_side_cases:
        print("\n⚠️  DATA QUALITY ISSUE DETECTED")
        print(f"\n   {len(missing_side_cases)} CNN segments have cleaning on only ONE side.")
        print("   This likely indicates:")
        print("   • Missing data in the source dataset")
        print("   • Data entry errors or omissions")
        print("   • Incomplete data collection")
        
        print("\n📋 RECOMMENDED ACTIONS:")
        print("   1. Review each case manually to verify if cleaning exists on missing side")
        print("   2. Check physical street signs for actual cleaning schedules")
        print("   3. Report missing data to SFMTA for correction")
        print("   4. Consider adding manual overrides for verified cases")
        print("   5. Add user feedback mechanism to report missing schedules")
        
        # Check if this matches known issue
        known_issue_cnn = '961000'
        if any(case['cnn'] == known_issue_cnn for case in missing_side_cases):
            print(f"\n   ℹ️  CNN {known_issue_cnn} is a KNOWN ISSUE (see DATA_QUALITY_ISSUES.md)")
    else:
        print("\n✅ DATA QUALITY LOOKS GOOD")
        print("   All segments with cleaning have schedules on both sides.")
        print("   Normal day/time differences between sides are expected and intentional.")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    analyze_missing_side_cleaning()