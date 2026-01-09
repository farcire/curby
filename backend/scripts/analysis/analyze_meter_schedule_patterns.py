#!/usr/bin/env python3
"""
Comprehensive analysis of Meter Operating Schedules:
1. All unique cap_color values (including WHITE for passenger loading)
2. All unique days_applied patterns (beyond standard day-of-week)
3. ALTERNATE schedule patterns with cap colors
"""

import os
from sodapy import Socrata
from dotenv import load_dotenv
from collections import Counter
import json

# Load environment variables
load_dotenv()

def analyze_meter_schedule_patterns():
    """
    Analyze all patterns in Meter Operating Schedules dataset.
    """
    # Initialize Socrata client
    client = Socrata(
        "data.sfgov.org",
        os.getenv("SFMTA_APP_TOKEN"),
        timeout=30
    )
    
    print("=" * 80)
    print("METER OPERATING SCHEDULES - COMPREHENSIVE PATTERN ANALYSIS")
    print("=" * 80)
    print()
    
    # Fetch all meter schedules
    print("Fetching Meter Operating Schedules (6cqg-dxku)...")
    try:
        schedules = client.get("6cqg-dxku", limit=100000)
        print(f"✓ Fetched {len(schedules)} schedule records")
        print()
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # ========================================
    # ANALYSIS 1: CAP COLORS
    # ========================================
    print("=" * 80)
    print("ANALYSIS 1: CAP COLOR PATTERNS")
    print("=" * 80)
    print()
    
    cap_colors = Counter()
    cap_color_by_schedule_type = {}
    
    for sched in schedules:
        cap_color = sched.get('cap_color', 'NULL')
        schedule_type = sched.get('schedule_type', 'NULL')
        
        cap_colors[cap_color] += 1
        
        if schedule_type not in cap_color_by_schedule_type:
            cap_color_by_schedule_type[schedule_type] = Counter()
        cap_color_by_schedule_type[schedule_type][cap_color] += 1
    
    print("All unique cap_color values:")
    for color, count in cap_colors.most_common():
        percentage = (count / len(schedules)) * 100
        print(f"  {color}: {count:,} ({percentage:.1f}%)")
    print()
    
    print("Cap colors by schedule type:")
    for stype in sorted(cap_color_by_schedule_type.keys()):
        print(f"\n  {stype}:")
        for color, count in cap_color_by_schedule_type[stype].most_common():
            print(f"    {color}: {count:,}")
    print()
    
    # Focus on ALTERNATE schedules with cap colors
    print("ALTERNATE schedules by cap color:")
    alternate_schedules = [s for s in schedules if s.get('schedule_type') == 'ALTERNATE']
    alternate_cap_colors = Counter([s.get('cap_color', 'NULL') for s in alternate_schedules])
    
    for color, count in alternate_cap_colors.most_common():
        percentage = (count / len(alternate_schedules)) * 100 if alternate_schedules else 0
        print(f"  {color}: {count} ({percentage:.1f}%)")
    print()
    
    # ========================================
    # ANALYSIS 2: DAYS APPLIED PATTERNS
    # ========================================
    print("=" * 80)
    print("ANALYSIS 2: DAYS_APPLIED PATTERNS")
    print("=" * 80)
    print()
    
    days_applied = Counter()
    days_by_schedule_type = {}
    
    for sched in schedules:
        days = sched.get('days_applied', 'NULL')
        schedule_type = sched.get('schedule_type', 'NULL')
        
        days_applied[days] += 1
        
        if schedule_type not in days_by_schedule_type:
            days_by_schedule_type[schedule_type] = Counter()
        days_by_schedule_type[schedule_type][days] += 1
    
    print(f"Total unique days_applied patterns: {len(days_applied)}")
    print()
    print("Top 20 most common days_applied patterns:")
    for days, count in days_applied.most_common(20):
        percentage = (count / len(schedules)) * 100
        print(f"  '{days}': {count:,} ({percentage:.1f}%)")
    print()
    
    # Identify non-standard patterns
    standard_patterns = {
        'Mon-Sat', 'Mon-Sun', 'Mon-Fri', 'Su', 'Sa', 
        'Mon', 'Tue', 'Wed', 'Thu', 'Fri',
        'Mon-Thu', 'Fri-Sat', 'Sat-Sun'
    }
    
    non_standard = {days: count for days, count in days_applied.items() 
                   if days not in standard_patterns and days != 'NULL'}
    
    if non_standard:
        print(f"Non-standard days_applied patterns ({len(non_standard)} unique):")
        for days, count in sorted(non_standard.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  '{days}': {count}")
        print()
    
    # ========================================
    # ANALYSIS 3: WHITE CAP COLOR DETAILS
    # ========================================
    print("=" * 80)
    print("ANALYSIS 3: WHITE CAP COLOR (PASSENGER LOADING)")
    print("=" * 80)
    print()
    
    white_schedules = [s for s in schedules if str(s.get('cap_color', '')).upper() == 'WHITE']
    
    if white_schedules:
        print(f"Total WHITE cap color schedules: {len(white_schedules)}")
        print()
        
        # Breakdown by schedule type
        white_by_type = Counter([s.get('schedule_type') for s in white_schedules])
        print("WHITE schedules by type:")
        for stype, count in white_by_type.most_common():
            print(f"  {stype}: {count}")
        print()
        
        # Sample WHITE schedules
        print("Sample WHITE cap color schedules:")
        for i, sched in enumerate(white_schedules[:5], 1):
            print(f"\n  #{i}:")
            print(f"    Post ID: {sched.get('postid', 'N/A')}")
            print(f"    Schedule Type: {sched.get('schedule_type', 'N/A')}")
            print(f"    Days Applied: {sched.get('days_applied', 'N/A')}")
            print(f"    Time: {sched.get('from_time', 'N/A')} - {sched.get('to_time', 'N/A')}")
            print(f"    Rate: ${sched.get('rate', 'N/A')}")
            print(f"    Time Limit: {sched.get('time_limit_minutes', 'N/A')} min")
    else:
        print("✓ NO WHITE cap color schedules found")
    print()
    
    # ========================================
    # ANALYSIS 4: ALTERNATE SCHEDULE DEEP DIVE
    # ========================================
    print("=" * 80)
    print("ANALYSIS 4: ALTERNATE SCHEDULE PATTERNS")
    print("=" * 80)
    print()
    
    print(f"Total ALTERNATE schedules: {len(alternate_schedules)}")
    print()
    
    # Days applied for ALTERNATE
    alternate_days = Counter([s.get('days_applied') for s in alternate_schedules])
    print("ALTERNATE schedules by days_applied:")
    for days, count in alternate_days.most_common(15):
        percentage = (count / len(alternate_schedules)) * 100 if alternate_schedules else 0
        print(f"  '{days}': {count} ({percentage:.1f}%)")
    print()
    
    # Sample ALTERNATE schedules with different cap colors
    print("Sample ALTERNATE schedules by cap color:")
    for color in ['WHITE', 'YELLOW', 'RED', 'GREEN', 'BLACK', 'GREY']:
        color_alts = [s for s in alternate_schedules if str(s.get('cap_color', '')).upper() == color]
        if color_alts:
            print(f"\n  {color} ({len(color_alts)} schedules):")
            sample = color_alts[0]
            print(f"    Post ID: {sample.get('postid', 'N/A')}")
            print(f"    Days: {sample.get('days_applied', 'N/A')}")
            print(f"    Time: {sample.get('from_time', 'N/A')} - {sample.get('to_time', 'N/A')}")
            print(f"    Rate: ${sample.get('rate', 'N/A')}")
    print()
    
    # ========================================
    # SAVE RESULTS
    # ========================================
    output = {
        'summary': {
            'total_schedules': len(schedules),
            'unique_cap_colors': len(cap_colors),
            'unique_days_patterns': len(days_applied),
            'alternate_schedules': len(alternate_schedules),
            'white_schedules': len(white_schedules)
        },
        'cap_colors': dict(cap_colors),
        'cap_colors_by_schedule_type': {k: dict(v) for k, v in cap_color_by_schedule_type.items()},
        'days_applied_patterns': dict(days_applied.most_common(50)),
        'non_standard_days': dict(sorted(non_standard.items(), key=lambda x: x[1], reverse=True)[:30]),
        'white_schedules_sample': white_schedules[:10],
        'alternate_schedules_sample': alternate_schedules[:10]
    }
    
    output_file = "meter_schedule_patterns_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Detailed results saved to: {output_file}")
    print()
    
    # ========================================
    # RECOMMENDATIONS
    # ========================================
    print("=" * 80)
    print("RECOMMENDATIONS FOR REGULATION NORMALIZER")
    print("=" * 80)
    print()
    
    print("Cap Color Rules to Implement:")
    print()
    for color in cap_colors.keys():
        if color == 'NULL':
            continue
        color_upper = str(color).upper()
        
        if color_upper == 'WHITE':
            print(f"  {color}:")
            print(f"    - Restriction: Passenger Loading Only")
            print(f"    - User Eligible: NO (not for parking)")
            print(f"    - Display: 'Passenger Loading Zone'")
            print(f"    - Severity: 3 (TOW + VIOLATION if parked)")
        elif color_upper in ['YELLOW', 'RED']:
            print(f"  {color}:")
            print(f"    - Restriction: Commercial Vehicles Only")
            print(f"    - User Eligible: NO (standard users)")
            print(f"    - Display: 'Commercial Vehicles'")
        elif color_upper in ['GREEN', 'BLACK', 'GREY']:
            print(f"  {color}:")
            print(f"    - Restriction: None")
            print(f"    - User Eligible: YES")
            print(f"    - Display: 'Standard parking'")
        else:
            print(f"  {color}:")
            print(f"    - Status: UNKNOWN - needs investigation")
    
    client.close()

if __name__ == "__main__":
    analyze_meter_schedule_patterns()