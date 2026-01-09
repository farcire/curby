#!/usr/bin/env python3
"""
Generate proper display format for ALTERNATE schedules with their base Operating Schedules.
Format:
  Line 1: Passenger Loading Zone on [interpretation]
  Line 2: All other days [duration] [day range] ($[rate]/hr)
"""

import os
from sodapy import Socrata
from dotenv import load_dotenv
import json
import re

load_dotenv()

def generate_display_formats():
    """
    Generate display formats for all non-DOW ALTERNATE schedules.
    """
    client = Socrata(
        "data.sfgov.org",
        os.getenv("SFMTA_APP_TOKEN"),
        timeout=30
    )
    
    print("=" * 80)
    print("ALTERNATE SCHEDULE DISPLAY FORMAT GENERATION")
    print("=" * 80)
    print()
    
    # Fetch all schedules
    print("Fetching Meter Operating Schedules...")
    schedules = client.get("6cqg-dxku", limit=100000)
    print(f"✓ Fetched {len(schedules)} schedules")
    print()
    
    # Group schedules by post_id
    schedules_by_meter = {}
    for sched in schedules:
        post_id = sched.get('post_id')
        if post_id:
            if post_id not in schedules_by_meter:
                schedules_by_meter[post_id] = []
            schedules_by_meter[post_id].append(sched)
    
    # Non-DOW patterns
    non_dow_patterns = [
        'School Days', 'Giants Day', 'Giants Night', 'Performance',
        'Posted Events', 'Posted Services', 'Business Hours'
    ]
    
    # Find meters with non-DOW ALTERNATE schedules
    meters_with_alternates = {}
    
    for post_id, meter_schedules in schedules_by_meter.items():
        for sched in meter_schedules:
            if (sched.get('schedule_type') == 'Alternate' and 
                sched.get('days_applied') in non_dow_patterns):
                
                if post_id not in meters_with_alternates:
                    meters_with_alternates[post_id] = {
                        'alternate': None,
                        'operating': []
                    }
                
                meters_with_alternates[post_id]['alternate'] = sched
                
                # Find base Operating Schedule
                for other_sched in meter_schedules:
                    if other_sched.get('schedule_type') == 'Operating Schedule':
                        meters_with_alternates[post_id]['operating'].append(other_sched)
    
    print(f"Found {len(meters_with_alternates)} meters with non-DOW ALTERNATE schedules")
    print()
    
    # Generate display formats
    print("=" * 80)
    print("DISPLAY FORMATS BY PATTERN")
    print("=" * 80)
    print()
    
    # Group by days_applied pattern
    by_pattern = {}
    for post_id, data in meters_with_alternates.items():
        pattern = data['alternate'].get('days_applied')
        if pattern not in by_pattern:
            by_pattern[pattern] = []
        by_pattern[pattern].append((post_id, data))
    
    # Generate formats for each pattern
    display_formats = {}
    
    for pattern in sorted(by_pattern.keys()):
        print(f"\n{'='*80}")
        print(f"Pattern: {pattern} ({len(by_pattern[pattern])} meters)")
        print('='*80)
        
        # Get sample meter
        sample_post_id, sample_data = by_pattern[pattern][0]
        alternate = sample_data['alternate']
        operating = sample_data['operating']
        
        print(f"\nSample Meter: {sample_post_id}")
        print(f"Street: {alternate.get('street_and_block')}")
        print()
        
        # Line 1: ALTERNATE schedule
        line1 = generate_line1(alternate)
        print(f"Line 1: {line1}")
        
        # Line 2: Base Operating Schedule
        if operating:
            line2 = generate_line2(operating[0])
            print(f"Line 2: {line2}")
        else:
            print("Line 2: [NO BASE OPERATING SCHEDULE FOUND]")
        
        print()
        print("Full Schedule Details:")
        print(f"  ALTERNATE:")
        print(f"    Days Applied: {alternate.get('days_applied')}")
        print(f"    Time: {alternate.get('from_time')} - {alternate.get('to_time')}")
        print(f"    Applied Color Rule: {alternate.get('applied_color_rule')}")
        print(f"    Time Limit: {alternate.get('time_limit')}")
        
        if operating:
            print(f"  OPERATING SCHEDULE:")
            for i, op in enumerate(operating, 1):
                print(f"    Schedule #{i}:")
                print(f"      Days Applied: {op.get('days_applied')}")
                print(f"      Time: {op.get('from_time')} - {op.get('to_time')}")
                print(f"      Time Limit: {op.get('time_limit')}")
                print(f"      Rate: ${op.get('rate', 'N/A')}")
                print(f"      Cap Color: {op.get('cap_color')}")
        
        # Store format
        display_formats[pattern] = {
            'line1': line1,
            'line2': line2 if operating else None,
            'sample_post_id': sample_post_id,
            'sample_street': alternate.get('street_and_block'),
            'meter_count': len(by_pattern[pattern])
        }
    
    # Save results
    output = {
        'summary': {
            'total_meters': len(meters_with_alternates),
            'patterns': len(by_pattern)
        },
        'display_formats': display_formats,
        'detailed_samples': {
            pattern: [
                {
                    'post_id': post_id,
                    'street': data['alternate'].get('street_and_block'),
                    'alternate': data['alternate'],
                    'operating': data['operating']
                }
                for post_id, data in by_pattern[pattern][:5]
            ]
            for pattern in by_pattern.keys()
        }
    }
    
    output_file = "alternate_display_formats.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    client.close()

def generate_line1(alternate_schedule):
    """Generate Line 1 display text for ALTERNATE schedule."""
    days_applied = alternate_schedule.get('days_applied')
    
    # Interpretation overrides mapping
    interpretation_map = {
        'School Days': 'School Days',
        'Giants Day': 'Giants Day Games',
        'Giants Night': 'Giants Night Games',
        'Performance': 'Special Event Periods',
        'Posted Events': 'Special Event Periods',
        'Posted Services': 'Service Periods',
        'Business Hours': 'Business Hours'
    }
    
    # Get the interpretation text
    interpretation = interpretation_map.get(days_applied, days_applied)
    
    # Format: "Passenger Loading Zone on [interpretation]"
    return f"Passenger Loading Zone on {interpretation}"

def generate_line2(operating_schedule):
    """Generate Line 2 display text for base Operating Schedule."""
    days = operating_schedule.get('days_applied', '')
    time_limit = operating_schedule.get('time_limit', '')
    rate = operating_schedule.get('rate', '')
    
    # Parse time limit
    duration_text = parse_time_limit(time_limit)
    
    # Parse days
    days_text = format_days(days)
    
    # Parse rate
    rate_text = f"${rate}/hr" if rate else "Free"
    
    return f"All other days {duration_text} {days_text} ({rate_text})"

def parse_time_limit(time_limit_str):
    """Parse time limit string to display format."""
    if not time_limit_str:
        return "No limit"
    
    time_limit_str = str(time_limit_str).lower()
    
    if 'minute' in time_limit_str:
        # Extract number
        match = re.search(r'(\d+)', time_limit_str)
        if match:
            minutes = int(match.group(1))
            if minutes == 0:
                return "No parking"
            elif minutes < 60:
                return f"{minutes}min limit"
            else:
                hours = minutes / 60
                if hours == int(hours):
                    return f"{int(hours)}hr limit"
                else:
                    return f"{hours}hr limit"
    
    return time_limit_str

def format_days(days_str):
    """Format days_applied string for display."""
    if not days_str:
        return ""
    
    days_str = str(days_str)
    
    # Common patterns
    if days_str == 'Mo,Tu,We,Th,Fr':
        return "M-F"
    elif days_str == 'Mo,Tu,We,Th,Fr,Sa':
        return "M-Sa"
    elif days_str == 'Mo,Tu,We,Th,Fr,Sa,Su':
        return "Daily"
    elif days_str == 'Sa,Su':
        return "Sa-Su"
    else:
        return days_str

if __name__ == "__main__":
    generate_display_formats()