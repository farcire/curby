#!/usr/bin/env python3
"""
Quick analysis of BlockID suffix pattern in local data.
Validates: BlockfaceID ending in 1 = L side, ending in 2 = R side
"""

import json
from collections import defaultdict

def analyze_local_segments():
    """Analyze segments_with_sweeping_rules.json for CNN suffix pattern"""
    
    with open('segments_with_sweeping_rules.json', 'r') as f:
        segments = json.load(f)
    
    print(f"Total segments: {len(segments)}")
    
    # Track CNN suffix vs side
    suffix_1_sides = defaultdict(int)  # CNNs ending in 1
    suffix_2_sides = defaultdict(int)  # CNNs ending in 2
    suffix_other_sides = defaultdict(int)  # CNNs ending in other digits
    
    pattern_matches = 0
    pattern_violations = 0
    
    examples_1L = []
    examples_2R = []
    violations = []
    
    for seg in segments:
        cnn = seg.get('cnn', '')
        side = seg.get('side', '')
        display = seg.get('display_name', 'N/A')
        
        if not cnn or not side:
            continue
        
        last_digit = cnn[-1]
        
        # Track distribution
        if last_digit == '1':
            suffix_1_sides[side] += 1
            if side == 'L':
                pattern_matches += 1
                if len(examples_1L) < 5:
                    examples_1L.append((cnn, display))
            else:
                pattern_violations += 1
                if len(violations) < 10:
                    violations.append((cnn, side, display, "Expected L, got R"))
        
        elif last_digit == '2':
            suffix_2_sides[side] += 1
            if side == 'R':
                pattern_matches += 1
                if len(examples_2R) < 5:
                    examples_2R.append((cnn, display))
            else:
                pattern_violations += 1
                if len(violations) < 10:
                    violations.append((cnn, side, display, "Expected R, got L"))
        
        else:
            suffix_other_sides[side] += 1
    
    # Print results
    print("\n" + "="*80)
    print("BLOCKFACE ID SUFFIX PATTERN ANALYSIS")
    print("="*80)
    
    print("\n--- CNNs Ending in 1 ---")
    print(f"L side: {suffix_1_sides['L']:,}")
    print(f"R side: {suffix_1_sides['R']:,}")
    
    print("\n--- CNNs Ending in 2 ---")
    print(f"L side: {suffix_2_sides['L']:,}")
    print(f"R side: {suffix_2_sides['R']:,}")
    
    print("\n--- CNNs Ending in Other Digits (0, 3-9) ---")
    print(f"L side: {suffix_other_sides['L']:,}")
    print(f"R side: {suffix_other_sides['R']:,}")
    
    print("\n--- Pattern Validation ---")
    total_checked = pattern_matches + pattern_violations
    if total_checked > 0:
        match_rate = (pattern_matches / total_checked) * 100
        print(f"Pattern Matches (1=L, 2=R): {pattern_matches:,}")
        print(f"Pattern Violations: {pattern_violations:,}")
        print(f"Match Rate: {match_rate:.2f}%")
    
    print("\n--- Examples of Pattern Matches ---")
    print("\nCNNs ending in 1 with L side:")
    for cnn, display in examples_1L:
        print(f"  ✓ {cnn} (L): {display}")
    
    print("\nCNNs ending in 2 with R side:")
    for cnn, display in examples_2R:
        print(f"  ✓ {cnn} (R): {display}")
    
    if violations:
        print("\n--- Pattern Violations (First 10) ---")
        for cnn, side, display, reason in violations:
            print(f"  ✗ {cnn} ({side}): {reason}")
            print(f"     {display}")
    
    # Write detailed report
    report = {
        "summary": {
            "total_segments": len(segments),
            "pattern_matches": pattern_matches,
            "pattern_violations": pattern_violations,
            "match_rate_percent": round(match_rate, 2) if total_checked > 0 else 0
        },
        "suffix_1_distribution": dict(suffix_1_sides),
        "suffix_2_distribution": dict(suffix_2_sides),
        "suffix_other_distribution": dict(suffix_other_sides),
        "conclusion": ""
    }
    
    if match_rate > 95:
        report["conclusion"] = "CONFIRMED: BlockfaceID ending in 1 = L side, ending in 2 = R side"
    elif match_rate > 50:
        report["conclusion"] = "PARTIAL: Pattern holds for majority but has significant exceptions"
    else:
        report["conclusion"] = "REJECTED: Pattern does not hold in this dataset"
    
    with open('blockid_pattern_analysis.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print(report["conclusion"])
    print("\nDetailed report saved to: blockid_pattern_analysis.json")

if __name__ == "__main__":
    analyze_local_segments()