#!/usr/bin/env python3
"""
Analyze the holiday override pattern in street cleaning dataset using Socrata API.

This script identifies cases where:
1. A CNN+side has a day with holidays=1 (cleaning on holidays)
2. The same CNN+side has a separate "HOLIDAY" entry with holidays=0 (no cleaning)

This pattern appears to be SFMTA's way of overriding the holidays=1 setting.

Example: CNN 6113000R
- Monday: holidays=1 (cleaning on holidays)
- HOLIDAY: holidays=0 (no cleaning on holidays)
Result: The HOLIDAY entry overrides Monday, so NO cleaning on holidays
"""

from sodapy import Socrata
from collections import defaultdict
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Socrata API setup
DOMAIN = "data.sfgov.org"
DATASET_ID = "yhqp-riqs"  # Street Cleaning Schedules
APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

def analyze_holiday_override_pattern():
    """Find CNNs with holiday override pattern."""
    
    print("Analyzing holiday override pattern in street cleaning dataset...")
    print("Fetching data from Socrata API (yhqp-riqs)...")
    print("=" * 80)
    
    # Connect to Socrata with app token
    client = Socrata(DOMAIN, APP_TOKEN)
    
    # Fetch all records (no limit)
    print("Fetching all records...")
    all_records = client.get(DATASET_ID, limit=50000)
    
    print(f"\nTotal records fetched: {len(all_records):,}")
    
    # Group by CNN + corridor_side
    cnn_side_groups = defaultdict(list)
    for record in all_records:
        cnn = record.get("cnn")
        corridor_side = record.get("corridor_side", "")
        key = f"{cnn}_{corridor_side}"
        cnn_side_groups[key].append(record)
    
    print(f"Total CNN+side combinations: {len(cnn_side_groups):,}")
    
    # Find override patterns
    override_cases = []
    
    for key, records in cnn_side_groups.items():
        # Check if this CNN+side has both:
        # 1. A day with holidays=1
        # 2. A HOLIDAY entry with holidays=0
        
        has_holiday_cleaning = False
        has_holiday_override = False
        days_with_holiday_cleaning = []
        
        for record in records:
            full_name = record.get("fullname", "")
            holidays = str(record.get("holidays", "0"))
            
            if full_name == "HOLIDAY" and holidays == "0":
                has_holiday_override = True
            elif full_name != "HOLIDAY" and holidays == "1":
                has_holiday_cleaning = True
                days_with_holiday_cleaning.append(full_name)
        
        # If both conditions met, this is an override case
        if has_holiday_cleaning and has_holiday_override:
            cnn, side = key.split("_")
            override_cases.append({
                "cnn": cnn,
                "side": side,
                "days_with_holidays_1": days_with_holiday_cleaning,
                "has_holiday_override": True,
                "record_count": len(records)
            })
    
    print(f"\n{'=' * 80}")
    print(f"HOLIDAY OVERRIDE PATTERN ANALYSIS")
    print(f"{'=' * 80}")
    print(f"\nCNN+sides with holiday override pattern: {len(override_cases):,}")
    
    if override_cases:
        print(f"Percentage of all CNN+sides: {len(override_cases) / len(cnn_side_groups) * 100:.2f}%")
        
        # Show first 20 examples
        print(f"\nFirst 20 examples:")
        print(f"{'CNN':<10} {'Side':<6} {'Days with holidays=1':<40} {'Records':<8}")
        print("-" * 90)
        for case in override_cases[:20]:
            days_str = ", ".join(case["days_with_holidays_1"])
            if len(days_str) > 38:
                days_str = days_str[:35] + "..."
            print(f"{case['cnn']:<10} {case['side']:<6} {days_str:<40} {case['record_count']:<8}")
        
        # Analyze patterns
        print(f"\n{'=' * 80}")
        print(f"PATTERN ANALYSIS")
        print(f"{'=' * 80}")
        
        # Count by number of days with holidays=1
        days_count = defaultdict(int)
        for case in override_cases:
            count = len(case["days_with_holidays_1"])
            days_count[count] += 1
        
        print(f"\nDistribution by number of days with holidays=1:")
        for count in sorted(days_count.keys()):
            pct = days_count[count] / len(override_cases) * 100
            print(f"  {count} day(s): {days_count[count]:,} cases ({pct:.1f}%)")
        
        # Most common day combinations
        day_combos = defaultdict(int)
        for case in override_cases:
            combo = ", ".join(sorted(case["days_with_holidays_1"]))
            day_combos[combo] += 1
        
        print(f"\nMost common day combinations with holidays=1:")
        sorted_combos = sorted(day_combos.items(), key=lambda x: x[1], reverse=True)
        for combo, count in sorted_combos[:10]:
            pct = count / len(override_cases) * 100
            print(f"  {combo}: {count:,} cases ({pct:.1f}%)")
        
        # Check CNN 6113000 specifically
        print(f"\n{'=' * 80}")
        print(f"CNN 6113000 ANALYSIS (from screenshot)")
        print(f"{'=' * 80}")
        cnn_6113000_cases = [c for c in override_cases if c["cnn"] == "6113000"]
        if cnn_6113000_cases:
            for case in cnn_6113000_cases:
                print(f"\nCNN {case['cnn']} Side {case['side']}:")
                print(f"  Days with holidays=1: {', '.join(case['days_with_holidays_1'])}")
                print(f"  Has HOLIDAY override: Yes")
                print(f"  Total records: {case['record_count']}")
        else:
            print("\nCNN 6113000 not found in override cases")
    else:
        print("\nNo holiday override patterns found in dataset")
    
    # Save results
    output = {
        "total_records": len(all_records),
        "total_cnn_sides": len(cnn_side_groups),
        "override_cases_count": len(override_cases),
        "override_percentage": len(override_cases) / len(cnn_side_groups) * 100 if cnn_side_groups else 0,
        "override_cases": override_cases[:100]  # Save first 100
    }
    
    with open("holiday_override_analysis.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"Results saved to: holiday_override_analysis.json")
    print(f"{'=' * 80}")
    
    return override_cases

if __name__ == "__main__":
    analyze_holiday_override_pattern()