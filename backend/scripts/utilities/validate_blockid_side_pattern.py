#!/usr/bin/env python3
"""
Validate the BlockID/BlockfaceID suffix pattern across all SF datasets.

HYPOTHESIS: 
- When streetside is L (Left), the blockfaceID ends in 1
- When streetside is R (Right), the blockfaceID ends in 2

This script validates this pattern across:
1. Street Sweeping Schedule dataset
2. Parking Regulations dataset  
3. On-Street Parking Meters dataset
4. Any other datasets with blockface/CNN identifiers
"""

import json
import requests
from collections import defaultdict

def analyze_street_sweeping():
    """Analyze Street Sweeping Schedule dataset"""
    print("=" * 80)
    print("ANALYZING: Street Sweeping Schedule Dataset")
    print("=" * 80)
    
    url = "https://data.sfgov.org/resource/yhqp-riqs.json"
    params = {"$limit": 10000}
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"\nTotal records retrieved: {len(data)}")
        
        # Analyze CNN patterns
        cnn_patterns = defaultdict(lambda: {"L": [], "R": [], "unknown": []})
        
        for record in data:
            cnn = record.get('cnn', '')
            blockside = record.get('blockside', '')
            
            if not cnn:
                continue
            
            # Determine side from blockside
            side = None
            if blockside in ['NorthEast', 'SouthEast', 'East']:
                side = 'L'  # Typically left side
            elif blockside in ['NorthWest', 'SouthWest', 'West']:
                side = 'R'  # Typically right side
            elif blockside in ['North', 'South']:
                side = 'unknown'
            
            if side:
                cnn_patterns[cnn][side].append(blockside)
        
        # Check if CNNs ending in 1 are L and ending in 2 are R
        pattern_matches = 0
        pattern_violations = 0
        
        print("\n--- CNN Suffix Pattern Analysis ---")
        print("Checking if CNN ending in 1 = L side, CNN ending in 2 = R side\n")
        
        for cnn, sides in list(cnn_patterns.items())[:20]:  # Sample first 20
            last_digit = cnn[-1] if cnn else None
            
            if last_digit == '1' and sides['L']:
                pattern_matches += 1
                print(f"✓ CNN {cnn} ends in 1, has L side: {sides['L'][0]}")
            elif last_digit == '2' and sides['R']:
                pattern_matches += 1
                print(f"✓ CNN {cnn} ends in 2, has R side: {sides['R'][0]}")
            elif last_digit in ['1', '2']:
                pattern_violations += 1
                print(f"✗ CNN {cnn} ends in {last_digit}, sides: L={len(sides['L'])}, R={len(sides['R'])}")
        
        print(f"\nPattern Matches: {pattern_matches}")
        print(f"Pattern Violations: {pattern_violations}")
        
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def analyze_parking_regulations():
    """Analyze Parking Regulations dataset"""
    print("\n" + "=" * 80)
    print("ANALYZING: Parking Regulations Dataset")
    print("=" * 80)
    
    url = "https://data.sfgov.org/resource/cqh6-am8x.json"
    params = {"$limit": 10000}
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"\nTotal records retrieved: {len(data)}")
        
        # Check for blockface ID patterns
        blockface_patterns = defaultdict(int)
        
        for record in data:
            # Check various possible field names
            blockface_id = (record.get('blockfaceid') or 
                          record.get('blockface_id') or 
                          record.get('cnn') or '')
            
            if blockface_id:
                last_digit = str(blockface_id)[-1]
                blockface_patterns[last_digit] += 1
        
        print("\n--- BlockfaceID Last Digit Distribution ---")
        for digit, count in sorted(blockface_patterns.items()):
            print(f"Ending in {digit}: {count} records")
        
        # Sample some records
        print("\n--- Sample Records ---")
        for record in data[:10]:
            blockface_id = (record.get('blockfaceid') or 
                          record.get('blockface_id') or 
                          record.get('cnn') or 'N/A')
            street = record.get('street_name', 'N/A')
            print(f"BlockfaceID: {blockface_id}, Street: {street}")
        
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def analyze_meters():
    """Analyze On-Street Parking Meters dataset"""
    print("\n" + "=" * 80)
    print("ANALYZING: On-Street Parking Meters Dataset")
    print("=" * 80)
    
    url = "https://data.sfgov.org/resource/8vzz-qzz9.json"
    params = {"$limit": 10000}
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"\nTotal records retrieved: {len(data)}")
        
        # Check for CNN patterns
        cnn_patterns = defaultdict(int)
        
        for record in data:
            cnn = record.get('cnn_id', '') or record.get('cnn', '')
            
            if cnn:
                last_digit = str(cnn)[-1]
                cnn_patterns[last_digit] += 1
        
        print("\n--- CNN Last Digit Distribution ---")
        for digit, count in sorted(cnn_patterns.items()):
            print(f"Ending in {digit}: {count} records")
        
        # Sample some records
        print("\n--- Sample Records ---")
        for record in data[:10]:
            cnn = record.get('cnn_id', '') or record.get('cnn', 'N/A')
            street = record.get('street_name', 'N/A')
            post_id = record.get('post_id', 'N/A')
            print(f"CNN: {cnn}, Street: {street}, Post ID: {post_id}")
        
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def analyze_local_data():
    """Analyze our local segments_with_sweeping_rules.json"""
    print("\n" + "=" * 80)
    print("ANALYZING: Local Database (segments_with_sweeping_rules.json)")
    print("=" * 80)
    
    try:
        with open('segments_with_sweeping_rules.json', 'r') as f:
            segments = json.load(f)
        
        print(f"\nTotal segments: {len(segments)}")
        
        # Analyze CNN suffix vs side
        pattern_matches = 0
        pattern_violations = 0
        
        cnn_side_map = defaultdict(lambda: {"L": 0, "R": 0})
        
        for seg in segments:
            cnn = seg.get('cnn', '')
            side = seg.get('side', '')
            
            if cnn and side:
                cnn_side_map[cnn][side] += 1
                
                last_digit = cnn[-1]
                
                # Check pattern
                if (last_digit == '1' and side == 'L') or (last_digit == '2' and side == 'R'):
                    pattern_matches += 1
                elif last_digit in ['1', '2']:
                    pattern_violations += 1
        
        print(f"\n--- CNN Suffix vs Side Pattern ---")
        print(f"Pattern Matches (1=L, 2=R): {pattern_matches}")
        print(f"Pattern Violations: {pattern_violations}")
        print(f"Match Rate: {pattern_matches / (pattern_matches + pattern_violations) * 100:.1f}%")
        
        # Show some examples
        print("\n--- Sample CNNs with Both Sides ---")
        count = 0
        for cnn, sides in cnn_side_map.items():
            if sides['L'] > 0 and sides['R'] > 0 and count < 10:
                print(f"CNN {cnn}: L={sides['L']}, R={sides['R']}")
                count += 1
        
        return segments
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print("\n" + "=" * 80)
    print("BLOCKFACE ID SUFFIX PATTERN VALIDATION")
    print("Hypothesis: BlockfaceID ending in 1 = L side, ending in 2 = R side")
    print("=" * 80)
    
    # Analyze each dataset
    sweeping_data = analyze_street_sweeping()
    parking_data = analyze_parking_regulations()
    meter_data = analyze_meters()
    local_data = analyze_local_data()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print("\nThe pattern analysis reveals:")
    print("1. Street Sweeping: Uses CNN with blockside (NE/SE/NW/SW)")
    print("2. Parking Regulations: Uses blockfaceID")
    print("3. Meters: Uses CNN")
    print("4. Local Data: Uses CNN with explicit L/R side designation")
    print("\nPattern validation shows whether the '1=L, 2=R' rule holds across datasets.")

if __name__ == "__main__":
    main()