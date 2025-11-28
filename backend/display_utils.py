"""
Display Message Utilities

Provides normalization and formatting functions for user-friendly display
of parking information including street names, cardinal directions, days of week,
and address ranges.
"""

from typing import Optional, Dict
import re


# ============================================================================
# STREET NAME NORMALIZATION
# ============================================================================

def normalize_street_name(street_name: str) -> str:
    """
    Normalize street name to user-friendly format.
    
    Examples:
        "18TH ST" → "18th Street"
        "BRYANT ST" → "Bryant Street"
        "VAN NESS AVE" → "Van Ness Avenue"
        "MCALLISTER ST" → "McAllister Street"
    """
    if not street_name:
        return "Unknown Street"
    
    words = street_name.strip().split()
    formatted_words = []
    
    for i, word in enumerate(words):
        # Handle ordinal numbers (18TH → 18th)
        if word.upper().endswith(('ST', 'ND', 'RD', 'TH')) and len(word) > 2:
            prefix = word[:-2]
            if prefix.isdigit():
                formatted_words.append(prefix + word[-2:].lower())
                continue
        
        # Handle street type abbreviations (last word only)
        if i == len(words) - 1:
            word_upper = word.upper()
            street_types = {
                'ST': 'Street',
                'AVE': 'Avenue',
                'BLVD': 'Boulevard',
                'DR': 'Drive',
                'RD': 'Road',
                'LN': 'Lane',
                'CT': 'Court',
                'PL': 'Place',
                'WAY': 'Way',
                'TER': 'Terrace',
                'CIR': 'Circle',
                'PKWY': 'Parkway'
            }
            if word_upper in street_types:
                formatted_words.append(street_types[word_upper])
                continue
        
        # Handle special capitalization
        word_lower = word.lower()
        if word_lower.startswith('mc') and len(word) > 2:
            formatted_words.append('Mc' + word[2:].capitalize())
        elif "'" in word:
            parts = word.split("'")
            formatted_words.append("'".join([p.capitalize() for p in parts]))
        else:
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)


# ============================================================================
# CARDINAL DIRECTION NORMALIZATION
# ============================================================================

def normalize_cardinal_direction(direction: Optional[str]) -> Optional[str]:
    """
    Normalize cardinal direction to full name.
    
    Examples:
        "N" → "North"
        "SE" → "Southeast"
        "NORTH" → "North"
    """
    if not direction:
        return None
    
    direction_map = {
        'N': 'North',
        'S': 'South',
        'E': 'East',
        'W': 'West',
        'NE': 'Northeast',
        'NW': 'Northwest',
        'SE': 'Southeast',
        'SW': 'Southwest',
        'NORTH': 'North',
        'SOUTH': 'South',
        'EAST': 'East',
        'WEST': 'West',
        'NORTHEAST': 'Northeast',
        'NORTHWEST': 'Northwest',
        'SOUTHEAST': 'Southeast',
        'SOUTHWEST': 'Southwest'
    }
    
    direction_upper = direction.strip().upper()
    return direction_map.get(direction_upper, direction)


# ============================================================================
# DAY OF WEEK NORMALIZATION
# ============================================================================

def normalize_day_of_week(day: Optional[str]) -> Optional[str]:
    """
    Normalize day of week to full name.
    
    Examples:
        "Th" → "Thursday"
        "Thurs" → "Thursday"
        "Mon" → "Monday"
        "TUES" → "Tuesday"
    """
    if not day:
        return None
    
    day_clean = day.strip().upper()
    
    day_map = {
        # Monday
        'M': 'Monday',
        'MON': 'Monday',
        'MONDAY': 'Monday',
        
        # Tuesday
        'TU': 'Tuesday',
        'TUE': 'Tuesday',
        'TUES': 'Tuesday',
        'TUESDAY': 'Tuesday',
        
        # Wednesday
        'W': 'Wednesday',
        'WED': 'Wednesday',
        'WEDNESDAY': 'Wednesday',
        
        # Thursday
        'TH': 'Thursday',
        'THU': 'Thursday',
        'THUR': 'Thursday',
        'THURS': 'Thursday',
        'THURSDAY': 'Thursday',
        
        # Friday
        'F': 'Friday',
        'FRI': 'Friday',
        'FRIDAY': 'Friday',
        
        # Saturday
        'SA': 'Saturday',
        'SAT': 'Saturday',
        'SATURDAY': 'Saturday',
        
        # Sunday
        'SU': 'Sunday',
        'SUN': 'Sunday',
        'SUNDAY': 'Sunday'
    }
    
    return day_map.get(day_clean, day)


def normalize_day_range(day_range: Optional[str]) -> Optional[str]:
    """
    Normalize day ranges like "Mon-Fri" to "Monday-Friday".
    
    Examples:
        "Mon-Fri" → "Monday-Friday"
        "Th-Sat" → "Thursday-Saturday"
        "M-F" → "Monday-Friday"
    """
    if not day_range:
        return None
    
    # Handle various dash types
    for dash in ['-', '–', '—']:
        if dash in day_range:
            parts = day_range.split(dash)
            if len(parts) == 2:
                start_day = normalize_day_of_week(parts[0])
                end_day = normalize_day_of_week(parts[1])
                if start_day and end_day:
                    return f"{start_day}-{end_day}"
    
    # Single day
    return normalize_day_of_week(day_range)


def normalize_day_list(day_list: Optional[str]) -> Optional[str]:
    """
    Normalize comma-separated day lists.
    
    Examples:
        "Mon, Wed, Fri" → "Monday, Wednesday, Friday"
        "Th, Sat" → "Thursday, Saturday"
    """
    if not day_list:
        return None
    
    days = [d.strip() for d in day_list.split(',')]
    normalized_days = [normalize_day_of_week(d) for d in days if d]
    normalized_days = [d for d in normalized_days if d]
    
    if normalized_days:
        return ', '.join(normalized_days)
    
    return day_list


# ============================================================================
# ADDRESS RANGE FORMATTING
# ============================================================================

def format_address_range(
    from_address: Optional[str],
    to_address: Optional[str],
    side_code: Optional[str] = None
) -> str:
    """
    Format address range for display.
    
    Examples:
        ("3401", "3449", "L") → "3401-3449"
        ("3400", "3448", "R") → "3400-3448"
        (None, None, "L") → ""
    """
    if not from_address or not to_address:
        return ""
    
    try:
        int(from_address)
        int(to_address)
        return f"{from_address}-{to_address}"
    except (ValueError, TypeError):
        return ""


# ============================================================================
# DISPLAY MESSAGE GENERATION
# ============================================================================

def generate_display_messages(
    street_name: str,
    side_code: str,
    cardinal_direction: Optional[str],
    from_address: Optional[str],
    to_address: Optional[str],
    address_parity: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate all display message variants for a street segment side.
    
    Args:
        street_name: Raw street name from dataset (e.g., "18TH ST")
        side_code: "L" or "R"
        cardinal_direction: Cardinal direction if available (e.g., "N", "North")
        from_address: Starting address (e.g., "3401")
        to_address: Ending address (e.g., "3449")
    
    Returns:
        Dictionary with display message variants:
        {
            'display_name': "18th Street (North side, 3401-3449)",
            'display_name_short': "18th Street (North side)",
            'display_address_range': "3401-3449",
            'display_cardinal': "North side"
        }
    """
    # Normalize components
    formatted_street = normalize_street_name(street_name)
    normalized_cardinal = normalize_cardinal_direction(cardinal_direction)
    address_display = format_address_range(from_address, to_address, side_code)
    
    # Determine cardinal display
    if normalized_cardinal:
        cardinal_display = f"{normalized_cardinal} side"
    elif address_parity:
        # If no cardinal but we know even/odd, show that
        cardinal_display = f"{side_code} side ({address_parity} numbers)"
    else:
        cardinal_display = f"{side_code} side"
    
    # Generate full display name
    if normalized_cardinal and address_display:
        display_name = f"{formatted_street} ({cardinal_display}, {address_display})"
    elif normalized_cardinal:
        display_name = f"{formatted_street} ({cardinal_display})"
    elif address_display:
        display_name = f"{formatted_street} ({side_code} side, {address_display})"
    else:
        display_name = f"{formatted_street} ({side_code} side)"
    
    # Generate short display name
    display_name_short = f"{formatted_street} ({cardinal_display})"
    
    return {
        'display_name': display_name,
        'display_name_short': display_name_short,
        'display_address_range': address_display or '',
        'display_cardinal': cardinal_display
    }


# ============================================================================
# TIME FORMATTING
# ============================================================================

def convert_24hr_to_12hr(time_str: Optional[str]) -> Optional[str]:
    """
    Convert 24-hour time format to 12-hour format with AM/PM.
    
    Examples:
        "0" → "12:00 AM"
        "6" → "6:00 AM"
        "12" → "12:00 PM"
        "18" → "6:00 PM"
        "0-6" → "12:00 AM-6:00 AM"
        "8:00 AM" → "8:00 AM" (already formatted)
    """
    if not time_str:
        return None
    
    # If it already contains AM/PM, return as is
    if 'AM' in time_str.upper() or 'PM' in time_str.upper():
        return time_str
    
    # Handle range (e.g., "0-6")
    if '-' in time_str:
        parts = time_str.split('-')
        if len(parts) == 2:
            start = convert_24hr_to_12hr(parts[0].strip())
            end = convert_24hr_to_12hr(parts[1].strip())
            if start and end:
                return f"{start}-{end}"
    
    # Parse the time
    try:
        # Remove any non-digit characters except colon
        clean_time = re.sub(r'[^\d:]', '', time_str)
        
        # Handle formats like "0", "6", "18"
        if ':' not in clean_time:
            hour = int(clean_time)
            minute = 0
        else:
            # Handle formats like "08:30", "18:45"
            parts = clean_time.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        
        # Convert to 12-hour format
        if hour == 0:
            hour_12 = 12
            period = 'AM'
        elif hour < 12:
            hour_12 = hour
            period = 'AM'
        elif hour == 12:
            hour_12 = 12
            period = 'PM'
        else:
            hour_12 = hour - 12
            period = 'PM'
        
        # Format with minutes
        if minute == 0:
            return f"{hour_12}:00 {period}"
        else:
            return f"{hour_12}:{minute:02d} {period}"
            
    except (ValueError, IndexError):
        # If parsing fails, return original
        return time_str


# ============================================================================
# RESTRICTION FORMATTING
# ============================================================================

def format_restriction_description(
    restriction_type: str,
    day: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    time_limit: Optional[int] = None,
    permit_area: Optional[str] = None
) -> str:
    """
    Format a parking restriction for user-friendly display.
    
    Examples:
        ("street-sweeping", "Th", "8:00 AM", "10:00 AM") 
            → "Street Cleaning Thursday 8:00 AM-10:00 AM"
        
        ("time-limit", None, "9:00 AM", "6:00 PM", 120) 
            → "2 Hour Limit 9:00 AM-6:00 PM"
        
        ("rpp-zone", None, None, None, None, "W") 
            → "Permit Required (Area W)"
    """
    # Normalize day if provided
    normalized_day = normalize_day_of_week(day) if day else None
    
    # Format based on restriction type
    if restriction_type == "street-sweeping":
        day_str = normalized_day or "Unknown Day"
        # Convert times to 12-hour format
        if start_time and end_time:
            start_12hr = convert_24hr_to_12hr(start_time)
            end_12hr = convert_24hr_to_12hr(end_time)
            time_str = f"{start_12hr}-{end_12hr}"
        else:
            time_str = ""
        return f"Street Cleaning {day_str} {time_str}".strip()
    
    elif restriction_type == "time-limit":
        if time_limit:
            hours = time_limit // 60
            minutes = time_limit % 60
            if hours > 0 and minutes > 0:
                limit_str = f"{hours} Hour {minutes} Minute Limit"
            elif hours > 0:
                limit_str = f"{hours} Hour Limit"
            else:
                limit_str = f"{minutes} Minute Limit"
        else:
            limit_str = "Time Limit"
        
        # Convert times to 12-hour format
        if start_time and end_time:
            start_12hr = convert_24hr_to_12hr(start_time)
            end_12hr = convert_24hr_to_12hr(end_time)
            time_str = f"{start_12hr}-{end_12hr}"
        else:
            time_str = ""
        return f"{limit_str} {time_str}".strip()
    
    elif restriction_type == "rpp-zone" or restriction_type == "permit":
        if permit_area:
            return f"Permit Required (Area {permit_area})"
        return "Permit Required"
    
    elif restriction_type == "no-parking":
        # Convert times to 12-hour format
        if start_time and end_time:
            start_12hr = convert_24hr_to_12hr(start_time)
            end_12hr = convert_24hr_to_12hr(end_time)
            time_str = f"{start_12hr}-{end_12hr}"
        else:
            time_str = ""
        day_str = normalized_day or ""
        return f"No Parking {day_str} {time_str}".strip()
    
    elif restriction_type == "tow-away":
        # Convert times to 12-hour format
        if start_time and end_time:
            start_12hr = convert_24hr_to_12hr(start_time)
            end_12hr = convert_24hr_to_12hr(end_time)
            time_str = f"{start_12hr}-{end_12hr}"
        else:
            time_str = ""
        return f"Tow-Away Zone {time_str}".strip()
    
    else:
        return restriction_type.replace('-', ' ').title()