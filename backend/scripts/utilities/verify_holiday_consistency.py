#!/usr/bin/env python3
"""
Verify holiday consistency hypothesis:
- HOLIDAY entry with holidays=1 should have corresponding days with holidays=1
- HOLIDAY entry with holidays=0 should either:
  a) Have all days with holidays=0 (consistent)
  b) Have some days with holidays=1 (override case - the 172 we found)
"""

from sodapy import Socrata
from collections import defaultdict
import json
import os
from dotenv import load_dotenv

load_dotenv()

DOMAIN = "data.sfgov.org"
DATASET_ID = "yhqp-riqs"
APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

def verify_holiday_consistency():
    print("Verifying Holiday Consistency Hypothesis")
    print("=" * 80)
    
    client = Socrata(DOMAIN, APP_TOKEN)
    all_records = client.get(DATASET_ID, limit=50000)
    print(f"Total records: {len(all_records):,}\n")
    
    # Group by CNN+side
    cnn_side_groups = defaultdict(list)
    for record in all_records:
        cnn = record.get("cnn")
        side = record.get("corridor_side", "")
        key = f"{cnn}_{side}"
        cnn_side_groups[key].append(record)
    
    print(f"Total CNN+sides: {len(cnn_side_groups):,}\n")
    
    # Analyze patterns
    patterns = {
        "no_holiday_entry": 0,
        "holiday_1_consistent": 0,  # HOLIDAY=1 and all days=1
        "holiday_0_consistent": 0,  # HOLIDAY=0 and all days=0
        "holiday_0_override": 0,    # HOLIDAY=0 but some days=1 (THE OVERRIDE CASE)
        "holiday_1_inconsistent": 0  # HOLIDAY=1 but some days=0 (should be rare/none)
    }
    
    examples = defaultdict(list)
    
    for key, records in cnn_side_groups.items():
        # Find HOLIDAY entry
        holiday_entry = None
        day_records = []
        
        for r in records:
            if r.get("fullname") == "HOLIDAY":
                holiday_entry = r
            else:
                day_records.append(r)
        
        if not holiday_entry:
            patterns["no_holiday_entry"] += 1
            continue
        
        holiday_val = str(holiday_entry.get("holidays", ""))
        day_holidays = [str(r.get("holidays", "")) for r in day_records]
        
        if holiday_val == "1":
            # HOLIDAY=1: Check if all days also =1
            if all(h == "1" for h in day_holidays):
                patterns["holiday_1_consistent"] += 1
                if len(examples["holiday_1_consistent"]) < 5:
                    examples["holiday_1_consistent"].append({
                        "cnn_side": key,
                        "holiday_entry": holiday_val,
                        "day_values": day_holidays
                    })
            else:
                patterns["holiday_1_inconsistent"] += 1
                if len(examples["holiday_1_inconsistent"]) < 5:
                    examples["holiday_1_inconsistent"].append({
                        "cnn_side": key,
                        "holiday_entry": holiday_val,
                        "day_values": day_holidays
                    })
        
        elif holiday_val == "0":
            # HOLIDAY=0: Check if consistent or override
            if all(h == "0" for h in day_holidays):
                patterns["holiday_0_consistent"] += 1
                if len(examples["holiday_0_consistent"]) < 5:
                    examples["holiday_0_consistent"].append({
                        "cnn_side": key,
                        "holiday_entry": holiday_val,
                        "day_values": day_holidays
                    })
            elif any(h == "1" for h in day_holidays):
                patterns["holiday_0_override"] += 1
                if len(examples["holiday_0_override"]) < 5:
                    examples["holiday_0_override"].append({
                        "cnn_side": key,
                        "holiday_entry": holiday_val,
                        "day_values": day_holidays,
                        "days_with_1": [i for i, h in enumerate(day_holidays) if h == "1"]
                    })
    
    # Print results
    print("PATTERN ANALYSIS")
    print("=" * 80)
    print(f"\nNo HOLIDAY entry: {patterns['no_holiday_entry']:,} ({patterns['no_holiday_entry']/len(cnn_side_groups)*100:.1f}%)")
    print(f"\nWith HOLIDAY entry: {len(cnn_side_groups) - patterns['no_holiday_entry']:,}")
    print(f"  - HOLIDAY=1 consistent (all days=1): {patterns['holiday_1_consistent']:,}")
    print(f"  - HOLIDAY=1 inconsistent (some days=0): {patterns['holiday_1_inconsistent']:,}")
    print(f"  - HOLIDAY=0 consistent (all days=0): {patterns['holiday_0_consistent']:,}")
    print(f"  - HOLIDAY=0 override (some days=1): {patterns['holiday_0_override']:,} ← THE OVERRIDE CASE")
    
    print(f"\n{'=' * 80}")
    print("HYPOTHESIS VERIFICATION")
    print("=" * 80)
    
    if patterns['holiday_1_inconsistent'] == 0:
        print("✅ CONFIRMED: When HOLIDAY=1, all days also have holidays=1 (consistent)")
    else:
        print(f"❌ VIOLATION: {patterns['holiday_1_inconsistent']} cases where HOLIDAY=1 but days have holidays=0")
    
    if patterns['holiday_0_override'] == 172:
        print(f"✅ CONFIRMED: Exactly 172 override cases (HOLIDAY=0 with days=1)")
    else:
        print(f"⚠️  Found {patterns['holiday_0_override']} override cases (expected 172)")
    
    print(f"\n{'=' * 80}")
    print("SIMPLIFIED LOGIC")
    print("=" * 80)
    print("""
The HOLIDAY entry is only special when it CONTRADICTS a day's holidays=1:
- If day holidays=1 AND HOLIDAY holidays=0 → Override to "except holidays"
- Otherwise → Use the consistent holidays value (0 or 1)
- If NO HOLIDAY entry → Use day's holidays field directly
    """)
    
    # Save results
    output = {
        "patterns": patterns,
        "examples": examples,
        "hypothesis_confirmed": patterns['holiday_1_inconsistent'] == 0
    }
    
    with open("holiday_consistency_verification.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: holiday_consistency_verification.json")

if __name__ == "__main__":
    verify_holiday_consistency()