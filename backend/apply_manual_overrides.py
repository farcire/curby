"""
Apply manual data overrides to augment missing or incorrect SFMTA data.
This module loads overrides from manual_data_overrides.json and applies them to segments.
"""
import json
import os
import re
from typing import List, Dict, Any, Optional
from deterministic_parser import _parse_days, parse_time_to_minutes
from display_utils import format_restriction_description

def load_manual_overrides(filepath: str = None) -> Dict:
    """Load manual data overrides from JSON file"""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), 'manual_data_overrides.json')
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Manual overrides file not found at {filepath}")
        return {"overrides": []}
    except json.JSONDecodeError as e:
        print(f"Error parsing manual overrides JSON: {e}")
        return {"overrides": []}

def match_segment_to_override(segment: Dict, override: Dict) -> bool:
    """
    Check if a segment matches the criteria for an override.
    
    Args:
        segment: Street segment dict with cnn, side, streetName, fromAddress, toAddress
        override: Override dict with match_criteria
    
    Returns:
        True if segment matches override criteria
    """
    criteria = override.get('match_criteria', {})
    
    # Match street name (regex)
    street_regex = criteria.get('street_name_regex')
    if street_regex:
        if not re.search(street_regex, segment.get('streetName', ''), re.IGNORECASE):
            return False
    
    # Match side
    if criteria.get('side') and segment.get('side') != criteria.get('side'):
        return False
    
    # Match CNN (if specified)
    if criteria.get('cnn') and segment.get('cnn') != criteria.get('cnn'):
        return False
    
    # Match address range
    from_addr = criteria.get('from_address')
    to_addr = criteria.get('to_address')
    
    if from_addr or to_addr:
        seg_from = str(segment.get('fromAddress', '')).strip()
        seg_to = str(segment.get('toAddress', '')).strip()
        
        if from_addr and seg_from != from_addr:
            return False
        if to_addr and seg_to != to_addr:
            return False
    
    return True

def apply_street_sweeping_override(segment: Dict, override: Dict) -> bool:
    """
    Apply a street sweeping override to a segment.
    
    Args:
        segment: Street segment to modify
        override: Override data to apply
    
    Returns:
        True if override was applied
    """
    data = override.get('data', {})
    
    # Pre-calculate fields
    active_days = _parse_days(data.get('weekday'))
    start_min = parse_time_to_minutes(data.get('fromhour'))
    end_min = parse_time_to_minutes(data.get('tohour'))
    
    description = format_restriction_description(
        "street-sweeping",
        day=data.get('weekday'),
        start_time=data.get('fromhour'),
        end_time=data.get('tohour')
    )
    
    # Create rule
    rule = {
        "type": data.get('type', 'street-sweeping'),
        "day": data.get('day'),
        "startTime": data.get('startTime'),
        "endTime": data.get('endTime'),
        "activeDays": active_days,
        "startTimeMin": start_min,
        "endTimeMin": end_min,
        "description": description,
        "blockside": data.get('blockside'),
        "side": data.get('cnnrightleft'),
        "limits": data.get('limits'),
        "source": "manual_override",
        "override_id": override.get('id'),
        "verified_date": override.get('verified_date')
    }
    
    # Add rule to segment
    segment["rules"].append(rule)
    
    # Update cardinal direction if not set
    if not segment.get("cardinalDirection") and data.get('blockside'):
        segment["cardinalDirection"] = data.get('blockside')
    
    return True

def apply_manual_overrides_to_segments(segments: List[Dict], overrides_file: str = None) -> Dict[str, int]:
    """
    Apply all manual overrides to the list of segments.
    
    Args:
        segments: List of street segments to potentially modify
        overrides_file: Optional path to overrides JSON file
    
    Returns:
        Dict with statistics about applied overrides
    """
    overrides_data = load_manual_overrides(overrides_file)
    overrides = overrides_data.get('overrides', [])
    
    stats = {
        'total_overrides': len(overrides),
        'applied': 0,
        'not_matched': 0,
        'by_type': {}
    }
    
    if not overrides:
        print("No manual overrides to apply")
        return stats
    
    print(f"\n=== Applying {len(overrides)} Manual Data Overrides ===")
    
    for override in overrides:
        override_id = override.get('id', 'unknown')
        override_type = override.get('type', 'unknown')
        
        # Track by type
        if override_type not in stats['by_type']:
            stats['by_type'][override_type] = 0
        
        # Find matching segment(s)
        matched = False
        for segment in segments:
            if match_segment_to_override(segment, override):
                # Apply override based on type
                if override_type == 'street_sweeping':
                    if apply_street_sweeping_override(segment, override):
                        stats['applied'] += 1
                        stats['by_type'][override_type] += 1
                        matched = True
                        print(f"  ✓ Applied override '{override_id}' to {segment.get('streetName')} {segment.get('side')} {segment.get('fromAddress')}-{segment.get('toAddress')}")
                        break  # Only apply to first match
        
        if not matched:
            stats['not_matched'] += 1
            print(f"  ⚠ Override '{override_id}' did not match any segments")
    
    print(f"\n✓ Applied {stats['applied']} overrides ({stats['not_matched']} not matched)")
    return stats

# For testing
if __name__ == "__main__":
    # Test loading
    overrides = load_manual_overrides()
    print(f"Loaded {len(overrides.get('overrides', []))} overrides")
    for override in overrides.get('overrides', []):
        print(f"  - {override.get('id')}: {override.get('type')}")