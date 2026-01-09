#!/usr/bin/env python3
"""
Generate complete list of all non-day-of-week entries in days_applied field
from Meter Operating Schedules dataset.
"""

import os
from sodapy import Socrata
from dotenv import load_dotenv
from collections import Counter
import json
import csv

load_dotenv()

def list_all_non_dow_patterns():
    """
    Find and list ALL non-day-of-week patterns in days_applied field.
    """
    client = Socrata(
        "data.sfgov.org",
        os.getenv("SFMTA_APP_TOKEN"),
        timeout=30
    )
    
    print("=" * 80)
    print("ALL NON-DAY-OF-WEEK PATTERNS IN days_applied")
    print("=" * 80)
    print()
    
    # Fetch all schedules
    print("Fetching all Meter Operating Schedules (6cqg-dxku)...")
    try:
        schedules = client.get("6cqg-dxku", limit=100000)
        print(f"✓ Fetched {len(schedules)} schedule records")
        print()
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Define standard day-of-week patterns
    standard_dow = {
        'mo', 'tu', 'we', 'th', 'fr', 'sa', 'su',
        'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
    }
    
    def is_day_of_week_pattern(days_applied):
        """Check if days_applied is a standard day-of-week pattern."""
        if not days_applied:
            return False
        
        days_lower = str(days_applied).lower().strip()
        
        # Remove common separators and split
        parts = days_lower.replace(',', ' ').replace('-', ' ').replace('/', ' ').split()
        
        # Check if all parts are standard day abbreviations
        return all(part in standard_dow for part in parts if part)
    
    # Collect all unique days_applied values
    all_days_applied = Counter([s.get('days_applied') for s in schedules])
    
    print(f"Total unique days_applied patterns: {len(all_days_applied)}")
    print()
    
    # Separate into DOW and non-DOW
    dow_patterns = {}
    non_dow_patterns = {}
    
    for pattern, count in all_days_applied.items():
        if is_day_of_week_pattern(pattern):
            dow_patterns[pattern] = count
        else:
            non_dow_patterns[pattern] = count
    
    print(f"Day-of-week patterns: {len(dow_patterns)}")
    print(f"Non-day-of-week patterns: {len(non_dow_patterns)}")
    print()
    
    # Display all non-DOW patterns
    print("=" * 80)
    print("ALL NON-DAY-OF-WEEK PATTERNS")
    print("=" * 80)
    print()
    
    print(f"Total: {len(non_dow_patterns)} unique patterns")
    print()
    
    # Sort by count (most common first)
    sorted_patterns = sorted(non_dow_patterns.items(), key=lambda x: x[1], reverse=True)
    
    print("Pattern | Count | % of Total")
    print("-" * 80)
    for pattern, count in sorted_patterns:
        percentage = (count / len(schedules)) * 100
        print(f"{pattern!r:50} | {count:6} | {percentage:5.2f}%")
    
    print()
    
    # Get sample records for each non-DOW pattern
    print("=" * 80)
    print("SAMPLE RECORDS FOR EACH NON-DOW PATTERN")
    print("=" * 80)
    print()
    
    pattern_samples = {}
    for pattern in non_dow_patterns.keys():
        samples = [s for s in schedules if s.get('days_applied') == pattern][:3]
        pattern_samples[pattern] = samples
    
    for pattern, samples in pattern_samples.items():
        print(f"\nPattern: {pattern!r} ({non_dow_patterns[pattern]} schedules)")
        print("-" * 80)
        
        for i, sample in enumerate(samples, 1):
            print(f"\n  Sample #{i}:")
            print(f"    Post ID: {sample.get('post_id')}")
            print(f"    Street: {sample.get('street_and_block')}")
            print(f"    Schedule Type: {sample.get('schedule_type')}")
            print(f"    Cap Color: {sample.get('cap_color')}")
            print(f"    Applied Color Rule: {sample.get('applied_color_rule', 'N/A')}")
            print(f"    Time: {sample.get('from_time')} - {sample.get('to_time')}")
            print(f"    Time Limit: {sample.get('time_limit')}")
            print(f"    Active Status: {sample.get('active_meter_status')}")
            print(f"    Priority: {sample.get('priority')}")
    
    # Save to files
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    print()
    
    # JSON output
    output_json = {
        'summary': {
            'total_schedules': len(schedules),
            'total_unique_patterns': len(all_days_applied),
            'dow_patterns': len(dow_patterns),
            'non_dow_patterns': len(non_dow_patterns)
        },
        'non_dow_patterns': {
            pattern: {
                'count': count,
                'percentage': (count / len(schedules)) * 100,
                'samples': pattern_samples.get(pattern, [])[:3]
            }
            for pattern, count in sorted_patterns
        }
    }
    
    json_file = "non_dow_days_applied_patterns.json"
    with open(json_file, 'w') as f:
        json.dump(output_json, f, indent=2)
    print(f"✓ JSON saved to: {json_file}")
    
    # CSV output for easy analysis
    csv_file = "non_dow_days_applied_patterns.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Pattern', 'Count', 'Percentage', 'Sample_PostID', 'Sample_Street', 'Sample_Schedule_Type', 'Sample_Applied_Color_Rule'])
        
        for pattern, count in sorted_patterns:
            percentage = (count / len(schedules)) * 100
            samples = pattern_samples.get(pattern, [])
            if samples:
                sample = samples[0]
                writer.writerow([
                    pattern,
                    count,
                    f"{percentage:.2f}%",
                    sample.get('post_id', ''),
                    sample.get('street_and_block', ''),
                    sample.get('schedule_type', ''),
                    sample.get('applied_color_rule', '')
                ])
            else:
                writer.writerow([pattern, count, f"{percentage:.2f}%", '', '', '', ''])
    
    print(f"✓ CSV saved to: {csv_file}")
    print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"Total schedules analyzed: {len(schedules):,}")
    print(f"Unique days_applied patterns: {len(all_days_applied)}")
    print(f"  - Day-of-week patterns: {len(dow_patterns)}")
    print(f"  - Non-day-of-week patterns: {len(non_dow_patterns)}")
    print()
    print(f"Schedules with non-DOW patterns: {sum(non_dow_patterns.values()):,}")
    print(f"Percentage of total: {(sum(non_dow_patterns.values()) / len(schedules)) * 100:.2f}%")
    
    client.close()

if __name__ == "__main__":
    list_all_non_dow_patterns()