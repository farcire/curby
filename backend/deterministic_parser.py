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
    """
    Parse day string into list of integers (0=Mon, 1=Tue... 6=Sun).
    Standardizing on Python weekday() convention for consistency.
    """
    if not day_str:
        return []
        
    day_str = day_str.strip().upper()
    
    if day_str in ["DAILY", "EVERY DAY", "7 DAYS"]:
        return [0, 1, 2, 3, 4, 5, 6]
        
    if "SCHOOL" in day_str:
        return [0, 1, 2, 3, 4]  # Mon-Fri
        
    # Python weekday mapping: 0=Mon, 6=Sun
    day_map = {
        'MO': 0, 'MON': 0, 'MONDAY': 0,
        'TU': 1, 'TUE': 1, 'TUES': 1, 'TUESDAY': 1,
        'WE': 2, 'WED': 2, 'WEDNES': 2, 'WEDNESDAY': 2,
        'TH': 3, 'THU': 3, 'THUR': 3, 'THURS': 3, 'THURSDAY': 3,
        'FR': 4, 'FRI': 4, 'FRIDAY': 4,
        'SA': 5, 'SAT': 5, 'SATURDAY': 5,
        'SU': 6, 'SUN': 6, 'SUNDAY': 6
    }
    
    # Check for range (e.g., "Mon-Fri")
    for separator in ['-', ' THRU ', ' THROUGH ']:
        if separator in day_str:
            parts = day_str.split(separator)
            if len(parts) == 2:
                start_day = _get_day_val(parts[0], day_map)
                end_day = _get_day_val(parts[1], day_map)
                
                if start_day is not None and end_day is not None:
                    if start_day <= end_day:
                        return list(range(start_day, end_day + 1))
                    else:
                        # Wrap around (e.g., Fri-Mon)
                        return list(range(start_day, 7)) + list(range(0, end_day + 1))
    
    # Check for list (e.g., "Mon,Wed,Fri")
    parts = re.split(r'[,&/]', day_str)
    result = set()
    for part in parts:
        val = _get_day_val(part, day_map)
        if val is not None:
            result.add(val)
            
    return sorted(list(result))

def _get_day_val(d: str, mapping: dict) -> Optional[int]:
    """Helper to get integer value for a single day string."""
    clean_d = d.strip().upper()
    if clean_d in mapping:
        return mapping[clean_d]
    for key, val in mapping.items():
        if clean_d.startswith(key):
            return val
    return None

def _parse_time(time_str: str) -> str:
    """Parse time string into HH:MM 24h format."""
    # This helper returns string format, but we might want minutes int as well.
    # For now keeping signature but implementing logic.
    if not time_str:
        return "00:00"
    
    minutes = parse_time_to_minutes(time_str)
    if minutes is None:
        return "00:00"
        
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def parse_time_to_minutes(time_str: Optional[str]) -> Optional[int]:
    """
    Convert time string to minutes from midnight (0-1439).
    """
    if not time_str:
        return None
        
    time_str = str(time_str).strip().upper()
    if not time_str:
        return None
        
    try:
        # Simple integer check (e.g. "900")
        if time_str.isdigit():
            val = int(time_str)
            if val < 24: return val * 60
            if val >= 100:
                hours = val // 100
                minutes = val % 100
                return hours * 60 + minutes
            return val * 60

        # Standard parsing
        clean_str = re.sub(r'[^\d:]', '', time_str)
        is_pm = "PM" in time_str
        is_am = "AM" in time_str
        
        if ':' in clean_str:
            parts = clean_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
        elif len(clean_str) >= 3:
            val = int(clean_str)
            hours = val // 100
            minutes = val % 100
        else:
            hours = int(clean_str)
            minutes = 0
            
        if is_pm and hours < 12: hours += 12
        elif is_am and hours == 12: hours = 0
            
        return hours * 60 + minutes
    except Exception:
        return None

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