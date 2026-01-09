#!/usr/bin/env python3
"""
Analyze BlockfaceID suffix pattern using SF datasets.

Datasets:
1. Blockfaces (pep9-66vw) - has SFPARK_ID (which becomes blockface_id in meters)
2. Blockfaces with Meters (mk27-a5x2) - has blockface_id and street_seg_orientation

HYPOTHESIS: 
- BlockfaceID ending in 1 = L (Left) side
- BlockfaceID ending in 2 = R (Right) side
"""

import requests
import json
from collections import defaultdict

def analyze_blockfaces_dataset():
    """Query blockfaces dataset (pep9-66vw) for SFPARK_ID pattern"""
    
    print("=" * 80)
    print("ANALYZING: Blockfaces Dataset (pep9-66vw)")
    print("=" * 80)
    
    url = "https://data.sfgov.org/resource/pep9-66vw.json"
    
    all_records = []
    limit = 50000
    
    print(f"\nFetching blockface records...")
    
    try:
        params = {"$limit": limit}
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        records = response.json()
        all_records.extend(records)
        print(f"Retrieved {len(records)} records")
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    
    print(f"Total blockface records: {len(all_records)}")
    
    # Analyze SFPARK_ID patterns
    sfpark_ids = []
    for record in all_records[:20]:  # Show sample
        sfpark_id = record.get('sfparkid') or record.get('sfpark_id') or record.get('SFPARK_ID')
        cnn = record.get('cnn')
        street = record.get('street_name', 'N/A')
        
        if sfpark_id:
            sfpark_ids.append((sfpark_id, cnn, street))
    
    print("\n--- Sample SFPARK_IDs ---")
    for sfpark_id, cnn, street in sfpark_ids[:10]:
        last_digit = str(sfpark_id)[-1]
        print(f"SFPARK_ID: {sfpark_id} (ends in {last_digit}), CNN: {cnn}, Street: {street}")
    
    return all_records

def analyze_blockface_meters():
    """Query blockfaces with meters dataset (mk27-a5x2)"""
    
    print("\n" + "=" * 80)
    print("ANALYZING: Blockfaces with Meters Dataset (mk27-a5x2)")
    print("=" * 80)
    
    url = "https://data.sfgov.org/resource/mk27-a5x2.json"
    
    all_records = []
    limit = 50000
    
    print(f"\nFetching records...")
    
    try:
        params = {"$limit": limit}
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        records = response.json()
        all_records.extend(records)
        print(f"Retrieved {len(records)} records")
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    
    print(f"Total records: {len(all_records)}")
    
    # Analyze blockface_id suffix vs street_seg_orientation
    suffix_1_sides = defaultdict(int)
    suffix_2_sides = defaultdict(int)
    suffix_other_sides = defaultdict(int)
    
    pattern_matches = 0
    pattern_violations = 0
    
    examples_1L = []
    examples_2R = []
    violations = []
    
    missing_blockface_id = 0
    missing_orientation = 0
    
    for record in all_records:
        blockface_id = record.get('blockface_id', '')
        orientation = record.get('street_seg_orientation', '')
        street = record.get('street_name', 'N/A')
        
        if not blockface_id:
            missing_blockface_id += 1
            continue
        
        if not orientation:
            missing_orientation += 1
            continue
        
        # Get last digit of blockface_id
        last_digit = str(blockface_id)[-1]
        
        # Track distribution
        if last_digit == '1':
            suffix_1_sides[orientation] += 1
            if orientation == 'L':
                pattern_matches += 1
                if len(examples_1L) < 10:
                    examples_1L.append((blockface_id, street, orientation))
            else:
                pattern_violations += 1
                if len(violations) < 10:
                    violations.append((blockface_id, street, orientation, "Expected L, got R"))
        
        elif last_digit == '2':
            suffix_2_sides[orientation] += 1
            if orientation == 'R':
                pattern_matches += 1
                if len(examples_2R) < 10:
                    examples_2R.append((blockface_id, street, orientation))
            else:
                pattern_violations += 1
                if len(violations) < 10:
                    violations.append((blockface_id, street, orientation, "Expected R, got L"))
        
        else:
            suffix_other_sides[orientation] += 1
    
    # Print results
    print("\n" + "=" * 80)
    print("BLOCKFACE_ID SUFFIX ANALYSIS")
    print("=" * 80)
    
    print(f"\nRecords with missing blockface_id: {missing_blockface_id}")
    print(f"Records with missing orientation: {missing_orientation}")
    
    print("\n--- BlockfaceIDs Ending in 1 ---")
    total_1 = sum(suffix_1_sides.values())
    print(f"Total: {total_1:,}")
    for orientation, count in sorted(suffix_1_sides.items()):
        pct = (count / total_1 * 100) if total_1 > 0 else 0
        print(f"  {orientation} side: {count:,} ({pct:.1f}%)")
    
    print("\n--- BlockfaceIDs Ending in 2 ---")
    total_2 = sum(suffix_2_sides.values())
    print(f"Total: {total_2:,}")
    for orientation, count in sorted(suffix_2_sides.items()):
        pct = (count / total_2 * 100) if total_2 > 0 else 0
        print(f"  {orientation} side: {count:,} ({pct:.1f}%)")
    
    print("\n--- BlockfaceIDs Ending in Other Digits (0, 3-9) ---")
    total_other = sum(suffix_other_sides.values())
    print(f"Total: {total_other:,}")
    for orientation, count in sorted(suffix_other_sides.items()):
        pct = (count / total_other * 100) if total_other > 0 else 0
        print(f"  {orientation} side: {count:,} ({pct:.1f}%)")
    
    # Pattern validation
    print("\n" + "=" * 80)
    print("PATTERN VALIDATION")
    print("=" * 80)
    
    total_checked = pattern_matches + pattern_violations
    if total_checked > 0:
        match_rate = (pattern_matches / total_checked) * 100
        print(f"\nPattern Matches (1=L, 2=R): {pattern_matches:,}")
        print(f"Pattern Violations: {pattern_violations:,}")
        print(f"Match Rate: {match_rate:.2f}%")
        
        if match_rate >= 99:
            conclusion = "✓ CONFIRMED: BlockfaceID ending in 1 = L, ending in 2 = R"
        elif match_rate >= 95:
            conclusion = "~ MOSTLY TRUE: Pattern holds for 95%+ of cases"
        elif match_rate >= 80:
            conclusion = "⚠ PARTIAL: Pattern holds for majority but has exceptions"
        else:
            conclusion = "✗ REJECTED: Pattern does not reliably hold"
        
        print(f"\nConclusion: {conclusion}")
    else:
        match_rate = 0
        conclusion = "Insufficient data"
    
    # Show examples
    if examples_1L:
        print("\n--- Examples: BlockfaceIDs Ending in 1 with L Orientation ---")
        for blockface_id, street, orientation in examples_1L[:10]:
            print(f"  ✓ {blockface_id} ({orientation}): {street}")
    
    if examples_2R:
        print("\n--- Examples: BlockfaceIDs Ending in 2 with R Orientation ---")
        for blockface_id, street, orientation in examples_2R[:10]:
            print(f"  ✓ {blockface_id} ({orientation}): {street}")
    
    if violations:
        print("\n--- Pattern Violations ---")
        for blockface_id, street, orientation, reason in violations:
            print(f"  ✗ {blockface_id} ({orientation}): {street}")
            print(f"     {reason}")
    
    # Save report
    report = {
        "dataset": "Blockfaces with Meters (mk27-a5x2)",
        "total_records": len(all_records),
        "missing_blockface_id": missing_blockface_id,
        "missing_orientation": missing_orientation,
        "suffix_1_distribution": dict(suffix_1_sides),
        "suffix_2_distribution": dict(suffix_2_sides),
        "suffix_other_distribution": dict(suffix_other_sides),
        "pattern_validation": {
            "matches": pattern_matches,
            "violations": pattern_violations,
            "match_rate_percent": round(match_rate, 2) if total_checked > 0 else 0
        },
        "conclusion": conclusion
    }
    
    with open('blockface_id_pattern_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Report saved to: blockface_id_pattern_report.json")
    print("=" * 80)
    
    return report

def main():
    print("\n" + "=" * 80)
    print("BLOCKFACE ID SUFFIX PATTERN VALIDATION")
    print("Hypothesis: BlockfaceID ending in 1 = L side, ending in 2 = R side")
    print("=" * 80)
    
    # Analyze blockfaces dataset
    blockfaces = analyze_blockfaces_dataset()
    
    # Analyze blockfaces with meters (has orientation field)
    report = analyze_blockface_meters()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()