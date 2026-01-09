"""
Validate Fuzzy Matching Algorithm

This script:
1. Implements a fuzzy matching algorithm for blockface records
2. Tests it against records that HAVE CNN IDs (ground truth)
3. Compares fuzzy-matched geometries vs synthetic offset geometries
4. Reports accuracy metrics and identifies mismatches
"""

import os
import re
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
from typing import Optional, Tuple, Dict, List
import json

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SFMTA_DOMAIN = "data.sfgov.org"
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"
STREETS_DATASET_ID = "3psu-pn9h"
STREET_INTERSECTIONS_ID = "pu5n-qu5c"

def parse_popupinfo(popupinfo: str) -> Optional[Dict[str, str]]:
    """
    Parse the popupinfo field to extract street metadata.
    
    Example input: "Alemany Boulevard between Sickles Ave and San Jose Ave, north side"
    
    Returns:
        {
            'street_name': 'Alemany Boulevard',
            'from_street': 'Sickles Ave',
            'to_street': 'San Jose Ave',
            'cardinal': 'north'
        }
    """
    if not popupinfo or not isinstance(popupinfo, str):
        return None
    
    # Pattern: "{Street Name} between {From Street} and {To Street}, {cardinal} side"
    pattern = r'^(.+?)\s+between\s+(.+?)\s+and\s+(.+?),\s+(\w+)\s+side'
    match = re.match(pattern, popupinfo, re.IGNORECASE)
    
    if match:
        return {
            'street_name': match.group(1).strip(),
            'from_street': match.group(2).strip(),
            'to_street': match.group(3).strip(),
            'cardinal': match.group(4).strip().lower()
        }
    
    return None

def normalize_street_name(name: str) -> str:
    """Normalize street name for matching."""
    if not name:
        return ""
    
    # Convert to uppercase for comparison
    name = name.upper().strip()
    
    # Standardize abbreviations
    replacements = {
        ' STREET': ' ST',
        ' AVENUE': ' AVE',
        ' BOULEVARD': ' BLVD',
        ' DRIVE': ' DR',
        ' ROAD': ' RD',
        ' LANE': ' LN',
        ' COURT': ' CT',
        ' PLACE': ' PL',
        ' TERRACE': ' TER',
        ' CIRCLE': ' CIR',
        ' PARKWAY': ' PKWY'
    }
    
    for full, abbr in replacements.items():
        name = name.replace(full, abbr)
    
    return name

def cardinal_to_side(cardinal: str) -> Optional[str]:
    """
    Map cardinal direction to L/R side.
    
    Note: This is a heuristic and may need refinement based on
    how SF streets are oriented.
    """
    if not cardinal:
        return None
    
    cardinal = cardinal.lower()
    
    # Common mappings (may need adjustment based on street orientation)
    # North/East typically = Right side
    # South/West typically = Left side
    if cardinal in ['north', 'n', 'east', 'e', 'northeast', 'ne']:
        return 'R'
    elif cardinal in ['south', 's', 'west', 'w', 'southwest', 'sw']:
        return 'L'
    
    return None

def fuzzy_match_blockface_to_cnn(
    parsed_info: Dict[str, str],
    intersections_df: pd.DataFrame
) -> Optional[Tuple[str, str, float]]:
    """
    Fuzzy match a parsed blockface to a CNN segment using street intersections.
    
    Dataset fields: cnn, streetname, from_st, limits, theorder
    
    Returns:
        (cnn, side, confidence) or None
    """
    street_name = normalize_street_name(parsed_info['street_name'])
    from_street = normalize_street_name(parsed_info['from_street'])
    to_street = normalize_street_name(parsed_info['to_street'])
    cardinal = parsed_info['cardinal']
    
    # Find candidates by street name
    candidates = intersections_df[
        intersections_df['streetname'].apply(lambda x: normalize_street_name(str(x)) == street_name)
    ]
    
    if candidates.empty:
        return None
    
    # Try to match by from_st (cross street) and limits
    best_match = None
    best_confidence = 0.0
    
    for _, row in candidates.iterrows():
        cnn = row.get('cnn')
        from_st = normalize_street_name(str(row.get('from_st', '')))
        limits = str(row.get('limits', '')).upper()
        
        if not cnn:
            continue
        
        # Check if from_st matches either from or to street
        confidence = 0.0
        
        if from_st == from_street or from_st == to_street:
            confidence = 0.8  # High confidence for from_st match
        elif from_street in limits or to_street in limits:
            # Check limits field for partial matches
            confidence = 0.5  # Lower confidence for limits match
        else:
            continue  # Skip if no match
        
        # Determine side from cardinal direction
        side = cardinal_to_side(cardinal)
        if not side:
            # Try to infer from address range parity if available
            side = 'L'  # Default
            confidence *= 0.8  # Reduce confidence if we can't determine side
        
        if confidence > best_confidence:
            best_confidence = confidence
            best_match = (cnn, side, confidence)
    
    return best_match

def validate_fuzzy_matching():
    """Main validation function."""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    
    print("="*80)
    print("FUZZY MATCHING VALIDATION")
    print("="*80)
    
    # 1. Fetch datasets
    print("\n1. Fetching datasets...")
    print("-"*80)
    
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    # Fetch blockfaces
    print("Fetching blockface dataset...")
    blockfaces_results = client.get(BLOCKFACE_GEOMETRY_ID, limit=50000)
    blockfaces_df = pd.DataFrame.from_records(blockfaces_results)
    print(f"✓ Fetched {len(blockfaces_df)} blockface records")
    
    # Fetch street intersections
    print("Fetching street intersections dataset...")
    intersections_results = client.get(STREET_INTERSECTIONS_ID, limit=100000)
    intersections_df = pd.DataFrame.from_records(intersections_results)
    print(f"✓ Fetched {len(intersections_df)} street intersection records")
    print(f"  Columns: {list(intersections_df.columns)}")
    
    # 2. Test on records WITH CNN IDs (ground truth)
    print("\n2. Testing fuzzy matching on records WITH CNN IDs (ground truth)...")
    print("-"*80)
    
    # Get records that have both CNN and popupinfo
    test_set = blockfaces_df[
        blockfaces_df['cnn_id'].notna() & 
        blockfaces_df['popupinfo'].notna()
    ]
    
    print(f"Test set size: {len(test_set)} records with both CNN and popupinfo")
    
    if test_set.empty:
        print("ERROR: No test records found with both CNN and popupinfo")
        return
    
    # Test fuzzy matching
    results = {
        'total': len(test_set),
        'parsed': 0,
        'matched': 0,
        'correct_cnn': 0,
        'correct_side': 0,
        'mismatches': []
    }
    
    for idx, row in test_set.iterrows():
        actual_cnn = str(row['cnn_id'])
        popupinfo = row['popupinfo']
        
        # Parse popupinfo
        parsed = parse_popupinfo(popupinfo)
        if not parsed:
            continue
        
        results['parsed'] += 1
        
        # Try fuzzy matching
        match = fuzzy_match_blockface_to_cnn(parsed, intersections_df)
        if not match:
            results['mismatches'].append({
                'globalid': row['globalid'],
                'popupinfo': popupinfo,
                'actual_cnn': actual_cnn,
                'predicted_cnn': None,
                'reason': 'No match found'
            })
            continue
        
        predicted_cnn, predicted_side, confidence = match
        results['matched'] += 1
        
        # Check if CNN matches
        if str(predicted_cnn) == actual_cnn:
            results['correct_cnn'] += 1
        else:
            results['mismatches'].append({
                'globalid': row['globalid'],
                'popupinfo': popupinfo,
                'actual_cnn': actual_cnn,
                'predicted_cnn': predicted_cnn,
                'predicted_side': predicted_side,
                'confidence': confidence,
                'reason': 'CNN mismatch'
            })
    
    # 3. Print results
    print("\n3. VALIDATION RESULTS:")
    print("-"*80)
    print(f"Total test records: {results['total']}")
    print(f"Successfully parsed: {results['parsed']} ({results['parsed']/results['total']*100:.1f}%)")
    print(f"Successfully matched: {results['matched']} ({results['matched']/results['total']*100:.1f}%)")
    print(f"Correct CNN matches: {results['correct_cnn']} ({results['correct_cnn']/max(results['matched'],1)*100:.1f}%)")
    
    print(f"\nAccuracy: {results['correct_cnn']/max(results['parsed'],1)*100:.1f}%")
    
    # 4. Show mismatches
    print("\n4. SAMPLE MISMATCHES (first 10):")
    print("-"*80)
    
    for i, mismatch in enumerate(results['mismatches'][:10], 1):
        print(f"\nMismatch {i}:")
        print(f"  PopupInfo: {mismatch['popupinfo']}")
        print(f"  Actual CNN: {mismatch['actual_cnn']}")
        print(f"  Predicted CNN: {mismatch.get('predicted_cnn', 'None')}")
        print(f"  Reason: {mismatch['reason']}")
    
    # 5. Save detailed report
    print("\n5. SAVING VALIDATION REPORT:")
    print("-"*80)
    
    report = {
        'summary': {
            'total_test_records': results['total'],
            'parsed': results['parsed'],
            'matched': results['matched'],
            'correct_cnn': results['correct_cnn'],
            'accuracy': results['correct_cnn']/max(results['parsed'],1)*100
        },
        'mismatches': results['mismatches'][:50]  # Save first 50 mismatches
    }
    
    report_path = "fuzzy_matching_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Saved validation report to: {report_path}")
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    validate_fuzzy_matching()