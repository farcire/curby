"""
Deterministic Parser for Parking Restrictions

Handles parsing of standard, deterministic patterns for:
1. Parking Meters (using priority logic)
2. Street Sweeping Schedules
"""

from typing import Dict, Any, List, Optional
import re

def parse_meter(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a parking meter record into a structured ParkingRule.
    
    Args:
        record: The raw meter schedule record.
        
    Returns:
        Structured ParkingRule dictionary.
    """
    # Extract priority - higher is more important
    # Dataset 6cqg-dxku has 'priority' field
    priority_val = 0
    if record.get("priority"):
        try:
            priority_val = int(record.get("priority"))
        except (ValueError, TypeError):
            priority_val = 0
            
    # Parse days applied
    days_applied = record.get("days_applied", "Mo-Su")
    parsed_days = _parse_days(days_applied)
    
    # Parse time
    from_time = record.get("from_time", "00:00")
    to_time = record.get("to_time", "23:59")
    parsed_start = _parse_time(from_time)
    parsed_end = _parse_time(to_time)
    
    # Check if this is a tow-away override (often indicated by high priority or schedule type)
    # For now, treat as meter rule unless specific flags found
    rule_type = "meter"
    severity = "low"
    
    # If priority is high or description implies towing/no parking
    if priority_val > 10:  # Heuristic threshold, refine based on data
        rule_type = "no-parking"
        severity = "high"
    
    return {
        "type": rule_type,
        "logic": {
            "time_ranges": [{
                "days": parsed_days,
                "start": parsed_start,
                "end": parsed_end
            }],
            "duration_minutes": _parse_duration(record.get("time_limit")),
            "priority": priority_val
        },
        "conditions": {},
        "display": {
            "summary": f"{record.get('cap_color', 'Meter')} Parking",
            "details": f"{record.get('time_limit', 'No limit')} limit. {days_applied} {from_time}-{to_time}",
            "severity": severity,
            "icon": "meter"
        }
    }

def parse_cleaning(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a street cleaning record into a structured ParkingRule.
    
    Args:
        record: The raw street cleaning record.
        
    Returns:
        Structured ParkingRule dictionary.
    """
    # yhqp-riqs fields: weekday, fromhour, tohour, week1ofmon, etc.
    
    # Parse days
    day_str = record.get("weekday", "")
    parsed_days = _parse_days(day_str)
    
    # Parse time
    # Format typically "0900" or "9" or "9:00"
    from_time = str(record.get("fromhour", "00:00"))
    to_time = str(record.get("tohour", "00:00"))
    
    parsed_start = _parse_time(from_time)
    parsed_end = _parse_time(to_time)
    
    # Weeks of month logic could be added here
    
    return {
        "type": "street-sweeping",
        "logic": {
            "time_ranges": [{
                "days": parsed_days,
                "start": parsed_start,
                "end": parsed_end
            }]
        },
        "conditions": {},
        "display": {
            "summary": "Street Cleaning",
            "details": f"No parking {day_str} {from_time}-{to_time} for street cleaning.",
            "severity": "medium",
            "icon": "street-cleaning"
        }
    }

def _parse_days(day_str: str) -> List[int]:
    """Parse day string into list of integers (0=Sun, 1=Mon... 6=Sat)."""
    # Simple mapping
    # This needs to be robust for "Mo-Fr", "Mon,Tue", etc.
    # Placeholder implementation
    if not day_str:
        return [0, 1, 2, 3, 4, 5, 6]
    
    # TODO: Implement robust day parsing
    # Returning default M-F for now to prevent errors
    return [1, 2, 3, 4, 5]

def _parse_time(time_str: str) -> str:
    """Parse time string into HH:MM 24h format."""
    # Placeholder
    return "09:00"

def _parse_duration(limit_str: Optional[str]) -> int:
    """Parse duration string (e.g. '60 minutes') into int minutes."""
    if not limit_str:
        return 0
    try:
        # Extract number
        match = re.search(r'\d+', str(limit_str))
        if match:
            return int(match.group(0))
    except:
        pass
    return 0