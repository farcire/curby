#!/usr/bin/env python3
"""
Analyze the holiday override pattern in street cleaning dataset.

This script identifies cases where:
1. A CNN+side has a day with holidays=1 (cleaning on holidays)
2. The same CNN+side has a separate "HOLIDAY" entry with holidays=0 (no cleaning)

This pattern appears to be SFMTA's way of overriding the holidays=1 setting.

Example: CNN 6113000R
- Monday: holidays=1 (cleaning on holidays)
- HOLIDAY: holidays=0 (no cleaning on holidays)
Result: The HOLIDAY entry overrides Monday, so NO cleaning on holidays
"""

import os
from pymongo import MongoClient
from collections import defaultdict
import json

# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["curby"]
collection = db["street_cleaning_schedules"]

def analyze_holiday_override_pattern():
    """Find CNNs with holiday override pattern."""
    
    print("Analyzing holiday override pattern in street cleaning dataset...")
    print("=" * 80)
    
    # Get all records
    all_records = list(collection.find({}))
    print(f"\nTotal records: {len(all_records):,}")
    
    # Group by CNN + side
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
        print(f"{'CNN':<10} {'Side':<6} {'Days with holidays=1':<30} {'Records':<8}")
        print("-" * 80)
        for case in override_cases[:20]:
            days_str = ", ".join(case["days_with_holidays_1"])
            print(f"{case['cnn']:<10} {case['side']:<6} {days_str:<30} {case['record_count']:<8}")
        
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
    
    # Save results
    output = {
        "total_records": len(all_records),
        "total_cnn_sides": len(cnn_side_groups),
        "override_cases_count": len(override_cases),
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