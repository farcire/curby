#!/usr/bin/env python3
"""
Verify the holiday pattern hypothesis:
- Whenever a CNN+side has a FullName="HOLIDAY" with holidays=0
- It ALSO has at least one entry for the same CNN+side with holidays=1

This would confirm that HOLIDAY entries are specifically used to override holidays=1 settings.
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

def verify_holiday_pattern():
    """Verify the holiday override pattern hypothesis."""
    
    print("Verifying Holiday Pattern Hypothesis")
    print("=" * 80)
    print("Hypothesis: Whenever CNN+side has HOLIDAY entry (holidays=0),")
    print("            it ALSO has at least one entry with holidays=1")
    print("=" * 80)
    
    # Connect to Socrata with app token
    client = Socrata(DOMAIN, APP_TOKEN)
    
    # Fetch all records
    print("\nFetching all records from Socrata API...")
    all_records = client.get(DATASET_ID, limit=50000)
    print(f"Total records fetched: {len(all_records):,}")
    
    # Group by CNN + corridor_side
    cnn_side_groups = defaultdict(list)
    for record in all_records:
        cnn = record.get("cnn")
        corridor_side = record.get("corridor_side", "")
        key = f"{cnn}_{corridor_side}"
        cnn_side_groups[key].append(record)
    
    print(f"Total CNN+side combinations: {len(cnn_side_groups):,}")
    
    # Find CNN+sides with HOLIDAY entries
    holiday_entry_cases = []
    
    for key, records in cnn_side_groups.items():
        has_holiday_entry = False
        has_holidays_1 = False
        holiday_entry_details = None
        holidays_1_days = []
        
        for record in records:
            full_name = record.get("fullname", "")
            holidays = str(record.get("holidays", "0"))
            
            if full_name == "HOLIDAY":
                has_holiday_entry = True
                holiday_entry_details = {
                    "holidays": holidays,
                    "weekday": record.get("weekday", ""),
                    "fromhour": record.get("fromhour", ""),
                    "tohour": record.get("tohour", "")
                }
            
            if holidays == "1":
                has_holidays_1 = True
                holidays_1_days.append(full_name)
        
        if has_holiday_entry:
            cnn, side = key.split("_")
            holiday_entry_cases.append({
                "cnn": cnn,
                "side": side,
                "has_holiday_entry": True,
                "holiday_entry_holidays_value": holiday_entry_details["holidays"],
                "has_holidays_1": has_holidays_1,
                "holidays_1_days": holidays_1_days,
                "total_records": len(records)
            })
    
    print(f"\n{'=' * 80}")
    print(f"RESULTS")
    print(f"{'=' * 80}")
    print(f"\nCNN+sides with HOLIDAY entry: {len(holiday_entry_cases):,}")
    
    # Test hypothesis
    hypothesis_confirmed = 0
    hypothesis_violated = 0
    holiday_0_count = 0
    holiday_1_count = 0
    
    for case in holiday_entry_cases:
        if case["holiday_entry_holidays_value"] == "0":
            holiday_0_count += 1
            if case["has_holidays_1"]:
                hypothesis_confirmed += 1
            else:
                hypothesis_violated += 1
        elif case["holiday_entry_holidays_value"] == "1":
            holiday_1_count += 1
    
    print(f"\nHOLIDAY entries with holidays=0: {holiday_0_count:,}")
    print(f"HOLIDAY entries with holidays=1: {holiday_1_count:,}")
    
    print(f"\n{'=' * 80}")
    print(f"HYPOTHESIS TEST")
    print(f"{'=' * 80}")
    print(f"\nCases where HOLIDAY entry has holidays=0: {holiday_0_count:,}")
    print(f"  ✅ Also has holidays=1 entry: {hypothesis_confirmed:,} ({hypothesis_confirmed/holiday_0_count*100:.1f}%)")
    print(f"  ❌ Does NOT have holidays=1 entry: {hypothesis_violated:,} ({hypothesis_violated/holiday_0_count*100:.1f}%)")
    
    if hypothesis_violated == 0:
        print(f"\n🎉 HYPOTHESIS CONFIRMED 100%!")
        print(f"   Every CNN+side with HOLIDAY entry (holidays=0) ALSO has at least one holidays=1 entry")
    else:
        print(f"\n⚠️  HYPOTHESIS PARTIALLY CONFIRMED")
        print(f"   {hypothesis_violated} cases violate the pattern")
    
    # Show examples
    print(f"\n{'=' * 80}")
    print(f"EXAMPLES (First 10)")
    print(f"{'=' * 80}")
    print(f"{'CNN':<10} {'Side':<6} {'HOLIDAY':<8} {'Has holidays=1':<16} {'Days with holidays=1':<40}")
    print("-" * 100)
    
    for case in holiday_entry_cases[:10]:
        days_str = ", ".join(case["holidays_1_days"][:5])  # Show first 5 days
        if len(case["holidays_1_days"]) > 5:
            days_str += "..."
        print(f"{case['cnn']:<10} {case['side']:<6} {case['holiday_entry_holidays_value']:<8} "
              f"{'Yes' if case['has_holidays_1'] else 'No':<16} {days_str:<40}")
    
    # Check CNN 6113000 specifically
    print(f"\n{'=' * 80}")
    print(f"CNN 6113000 VERIFICATION")
    print(f"{'=' * 80}")
    cnn_6113000_cases = [c for c in holiday_entry_cases if c["cnn"] == "6113000"]
    if cnn_6113000_cases:
        for case in cnn_6113000_cases:
            print(f"\nCNN {case['cnn']} Side {case['side']}:")
            print(f"  HOLIDAY entry holidays value: {case['holiday_entry_holidays_value']}")
            print(f"  Has holidays=1 entries: {'Yes' if case['has_holidays_1'] else 'No'}")
            if case['has_holidays_1']:
                print(f"  Days with holidays=1: {', '.join(case['holidays_1_days'])}")
    else:
        print("\nCNN 6113000 not found in HOLIDAY entry cases")
    
    # Save results
    output = {
        "total_cnn_sides_with_holiday_entry": len(holiday_entry_cases),
        "holiday_0_count": holiday_0_count,
        "holiday_1_count": holiday_1_count,
        "hypothesis_confirmed_count": hypothesis_confirmed,
        "hypothesis_violated_count": hypothesis_violated,
        "hypothesis_confirmed_percentage": hypothesis_confirmed/holiday_0_count*100 if holiday_0_count > 0 else 0,
        "examples": holiday_entry_cases[:50]
    }
    
    with open("holiday_pattern_verification.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"Results saved to: holiday_pattern_verification.json")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    verify_holiday_pattern()