"""
Display Message Utilities

Provides normalization and formatting functions for user-friendly display
of parking information including street names, cardinal directions, and address ranges.

IMPORTANT: Day/time normalization has been moved to regulation_normalizer.py
For all day/time parsing and formatting, use the regulation_normalizer module instead.
"""

from typing import Optional, Dict


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
    
    # Handle non-string values (e.g., float/NaN from pandas)
    if not isinstance(direction, str):
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
# RESTRICTION FORMATTING (DEPRECATED - Use regulation_normalizer.py)
# ============================================================================

def format_restriction_description(
    restriction_type: str,
    display_days: Optional[str] = None,
    display_time: Optional[str] = None,
    time_limit: Optional[int] = None,
    permit_area: Optional[str] = None
) -> str:
    """
    Format a parking restriction for user-friendly display.
    
    DEPRECATED: This function now expects pre-formatted display strings from regulation_normalizer.
    Use regulation_normalizer.normalize_regulation() to get display_days and display_time.
    
    Examples:
        ("street-sweeping", "Thursday", "8:00 AM-10:00 AM") 
            → "Street Cleaning Thursday 8:00 AM-10:00 AM"
        
        ("time-limit", None, "9:00 AM-6:00 PM", 120) 
            → "2 Hour Limit 9:00 AM-6:00 PM"
        
        ("rpp-zone", None, None, None, "W") 
            → "Permit Required (Area W)"
    """
    # Format based on restriction type
    if restriction_type == "street-sweeping":
        day_str = display_days or "Unknown Day"
        time_str = display_time or ""
        return f"Street Cleaning {day_str} {time_str}".strip()
    
    elif restriction_type == "time-limit":
        # DEPRECATED: This manual formatting should not be used.
        # Duration display strings should be pre-computed by regulation_normalizer
        # and passed in as displayDuration or displayDurationLong fields.
        # This code is kept for backward compatibility only.
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
        
        time_str = display_time or ""
        return f"{limit_str} {time_str}".strip()
    
    elif restriction_type == "rpp-zone" or restriction_type == "permit":
        if permit_area:
            return f"Permit Required (Area {permit_area})"
        return "Permit Required"
    
    elif restriction_type == "no-parking":
        time_str = display_time or ""
        day_str = display_days or ""
        return f"No Parking {day_str} {time_str}".strip()
    
    elif restriction_type == "tow-away":
        time_str = display_time or ""
        return f"Tow-Away Zone {time_str}".strip()
    
    else:
        return restriction_type.replace('-', ' ').title()