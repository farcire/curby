"""
Regulation Normalizer - Single Source of Truth
===============================================

Centralizes ALL day, time, and duration parsing and formatting logic.
This is the ONLY place where temporal data normalization exists.

All other modules must import from here.

Usage:
    from regulation_normalizer import normalize_regulation, format_day_display
    
    # At ingestion
    normalized = normalize_regulation(raw_record, dataset_type='street_cleaning')
    
    # For display
    display_text = format_day_display(normalized['canonical']['days'])

Dataset Day Format Reference:
-----------------------------
- Street Cleaning (yhqp-riqs): 'weekday' field
  Examples: "Th", "Mon", "TUES", "Friday"
  
- Parking Regulations (hi6h-neyh): 'days' field
  Examples: "MON-FRI", "DAILY", "Mon,Wed,Fri", "SCHOOL DAYS"
  
- Meter Schedules (6cqg-dxku): 'days_applied' field
  Examples: "Mo-Su", "Mo-Fr", "Sa,Su"
  
- Manual Overrides (manual_data_overrides.json): 'weekday' field
  Examples: "Thursday", "Monday-Friday"

Canonical Format:
-----------------
Days: Array of integers [0-6] where 0=Monday, 6=Sunday
Times: Integer minutes from midnight (0-1439)
Duration: Integer minutes

Display Format:
---------------
Days: Minimal abbreviations (M, Tu, W, Th, F, Sa, Su)
Smart overrides: "Daily", "Weekdays", "Weekends", "School Days"
"""

from typing import Optional, Dict, List, Any
import re


# ============================================================================
# PART 1: DAY PARSING (Any Format → Canonical [0-6] Array)
# ============================================================================

class DayParser:
    """
    Parse ANY day format from SFMTA datasets to canonical [0-6] array.
    
    Canonical format uses Python weekday convention:
    0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
    """
    
    # Complete abbreviation mapping
    DAY_ABBREVIATIONS = {
        # Monday
        'M': 0, 'MO': 0, 'MON': 0, 'MONDAY': 0,
        
        # Tuesday
        'TU': 1, 'TUE': 1, 'TUES': 1, 'TUESDAY': 1,
        
        # Wednesday
        'W': 2, 'WE': 2, 'WED': 2, 'WEDNESDAY': 2,
        
        # Thursday
        'TH': 3, 'THU': 3, 'THUR': 3, 'THURS': 3, 'THURSDAY': 3,
        
        # Friday
        'F': 4, 'FR': 4, 'FRI': 4, 'FRIDAY': 4,
        
        # Saturday
        'SA': 5, 'SAT': 5, 'SATURDAY': 5,
        
        # Sunday
        'SU': 6, 'SUN': 6, 'SUNDAY': 6
    }
    
    # Special pattern recognition
    EVERY_DAY_PATTERNS = {
        'DAILY', 'EVERY DAY', 'EVERYDAY', '7 DAYS', 'ALL DAYS',
        'ALL WEEK', 'MO-SU', 'MON-SUN', 'MONDAY-SUNDAY',
        'M-SU', 'M-S', '7 DAYS A WEEK', 'SEVEN DAYS'
    }
    
    WEEKDAY_PATTERNS = {'WEEKDAYS', 'WEEKDAY'}
    WEEKEND_PATTERNS = {'WEEKENDS', 'WEEKEND'}
    SCHOOL_DAY_PATTERNS = {'SCHOOL DAYS', 'SCHOOL DAY', 'SCHOOLDAYS'}
    
    @classmethod
    def parse(cls, day_input: Any) -> List[int]:
        """
        Parse any day format to canonical [0-6] array.
        
        Args:
            day_input: Day string from any SFMTA dataset
        
        Returns:
            List of integers [0-6] representing active days
        
        Examples:
            "DAILY" → [0,1,2,3,4,5,6]
            "MON-FRI" → [0,1,2,3,4]
            "Th" → [3]
            "Mon,Wed,Fri" → [0,2,4]
        """
        if not day_input:
            return []
        
        # Handle non-string types (int, float, NaN)
        if not isinstance(day_input, str):
            return []
        
        day_str = str(day_input).strip().upper()
        
        if not day_str or day_str in ('NAN', 'NONE', 'NULL', ''):
            return []
        
        # Pattern 1: Every day variations → [0,1,2,3,4,5,6]
        if day_str in cls.EVERY_DAY_PATTERNS:
            return [0, 1, 2, 3, 4, 5, 6]
        
        # Pattern 2: Weekdays → [0,1,2,3,4]
        if day_str in cls.WEEKDAY_PATTERNS:
            return [0, 1, 2, 3, 4]
        
        # Pattern 3: Weekends → [5,6]
        if day_str in cls.WEEKEND_PATTERNS:
            return [5, 6]
        
        # Pattern 4: School Days → [0,1,2,3,4] (will be handled specially in display)
        if day_str in cls.SCHOOL_DAY_PATTERNS:
            return [0, 1, 2, 3, 4]
        
        # Pattern 5: Ranges (Mon-Fri, M-F, etc.)
        for separator in ['-', ' THRU ', ' THROUGH ', ' TO ']:
            if separator in day_str:
                return cls._parse_range(day_str, separator)
        
        # Pattern 6: Lists (Mon,Wed,Fri or Mon&Wed or Mon/Wed)
        if any(sep in day_str for sep in [',', '&', '/', ';']):
            return cls._parse_list(day_str)
        
        # Pattern 7: Single day
        return cls._parse_single(day_str)
    
    @classmethod
    def _parse_range(cls, day_str: str, separator: str) -> List[int]:
        """Parse day range like 'Mon-Fri' or 'M-F'"""
        parts = day_str.split(separator)
        if len(parts) != 2:
            return []
        
        start_day = cls._get_day_value(parts[0].strip())
        end_day = cls._get_day_value(parts[1].strip())
        
        if start_day is None or end_day is None:
            return []
        
        # Handle wrap-around (e.g., Fri-Mon)
        if start_day <= end_day:
            return list(range(start_day, end_day + 1))
        else:
            return list(range(start_day, 7)) + list(range(0, end_day + 1))
    
    @classmethod
    def _parse_list(cls, day_str: str) -> List[int]:
        """Parse day list like 'Mon,Wed,Fri'"""
        # Split by any separator
        parts = re.split(r'[,&/;]', day_str)
        result = set()
        
        for part in parts:
            day_val = cls._get_day_value(part.strip())
            if day_val is not None:
                result.add(day_val)
        
        return sorted(list(result))
    
    @classmethod
    def _parse_single(cls, day_str: str) -> List[int]:
        """Parse single day like 'Thursday' or 'Th'"""
        day_val = cls._get_day_value(day_str)
        return [day_val] if day_val is not None else []
    
    @classmethod
    def _get_day_value(cls, day_str: str) -> Optional[int]:
        """Get integer value for a single day string"""
        clean_str = day_str.strip().upper()
        
        # Direct match
        if clean_str in cls.DAY_ABBREVIATIONS:
            return cls.DAY_ABBREVIATIONS[clean_str]
        
        # Prefix match (for variations)
        for abbrev, value in cls.DAY_ABBREVIATIONS.items():
            if clean_str.startswith(abbrev):
                return value
        
        return None


# ============================================================================
# PART 2: DAY FORMATTING (Canonical → Human-Readable Display)
# ============================================================================

class DayFormatter:
    """
    Format canonical day arrays to human-readable strings.
    
    Uses minimal abbreviations: M, Tu, W, Th, F, Sa, Su
    Smart overrides: Daily, Weekdays, Weekends, School Days
    """
    
    # Minimal abbreviations (1-2 letters for clarity)
    MINIMAL_ABBREV = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']
    FULL_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    @classmethod
    def format_display(cls, days: List[int], context_text: str = None) -> str:
        """
        Format days for display with smart overrides and context awareness.
        
        Args:
            days: Canonical day array [0-6]
            context_text: Optional context (regulation text) to check for "school"
        
        Returns:
            Display string using minimal abbreviations or smart overrides
        
        Examples:
            [0,1,2,3,4,5,6] → "Daily"
            [0,1,2,3,4] → "Weekdays" (or "School Days" if context contains "school")
            [5,6] → "Weekends"
            [0,2,4] → "M, W, F"
            [1,2,3] → "Tu-Th"
        """
        if not days:
            return ""
        
        days_sorted = sorted(days)
        
        # Smart Override 1: All 7 days → "Daily"
        if days_sorted == [0, 1, 2, 3, 4, 5, 6]:
            return "Daily"
        
        # Smart Override 2: Mon-Fri with context check
        if days_sorted == [0, 1, 2, 3, 4]:
            # Check if "school" appears in context
            if context_text and 'SCHOOL' in str(context_text).upper():
                return "School Days"
            else:
                return "Weekdays"
        
        # Smart Override 3: Sat-Sun → "Weekends"
        if days_sorted == [5, 6]:
            return "Weekends"
        
        # All other patterns: Use minimal abbreviations
        if cls._is_continuous_range(days_sorted):
            return f"{cls.MINIMAL_ABBREV[days_sorted[0]]}-{cls.MINIMAL_ABBREV[days_sorted[-1]]}"
        
        return ", ".join(cls.MINIMAL_ABBREV[d] for d in days_sorted)
    
    @classmethod
    def format_full(cls, days: List[int]) -> str:
        """Format days with full names (for verbose display)"""
        if not days:
            return ""
        
        days_sorted = sorted(days)
        
        if days_sorted == [0, 1, 2, 3, 4, 5, 6]:
            return "Daily"
        
        if days_sorted == [0, 1, 2, 3, 4]:
            return "Weekdays"
        
        if days_sorted == [5, 6]:
            return "Weekends"
        
        if cls._is_continuous_range(days_sorted):
            return f"{cls.FULL_NAMES[days_sorted[0]]}-{cls.FULL_NAMES[days_sorted[-1]]}"
        
        return ", ".join(cls.FULL_NAMES[d] for d in days_sorted)
    
    @staticmethod
    def _is_continuous_range(days: List[int]) -> bool:
        """Check if days form a continuous sequence"""
        if len(days) < 2:
            return False
        
        for i in range(len(days) - 1):
            if days[i+1] - days[i] != 1:
                return False
        
        return True


# ============================================================================
# PART 3: TIME PARSING (Any Format → Minutes from Midnight)
# ============================================================================

class TimeParser:
    """
    Parse ANY time format from SFMTA datasets to minutes from midnight (0-1439).
    
    Handles formats:
    - Simple integers: "9", "18", 9, 18
    - Military time: "900", "1800", "0900"
    - Colon format: "9:00", "18:30", "09:00"
    - 12-hour format: "9:00 AM", "6:00 PM", "12:00 AM"
    - ISO time: "09:00:00", "18:30:00"
    """
    
    @classmethod
    def parse(cls, time_input: Any) -> Optional[int]:
        """
        Parse any time format to minutes from midnight.
        
        Args:
            time_input: Time value from any SFMTA dataset
        
        Returns:
            Integer minutes from midnight (0-1439), or None if invalid
        
        Examples:
            "9" → 540 (9:00 AM)
            "1800" → 1080 (6:00 PM)
            "9:00 AM" → 540
            "6:00 PM" → 1080
        """
        if not time_input:
            return None
        
        # Convert to string
        try:
            time_str = str(time_input).strip().upper()
        except:
            return None
        
        if not time_str or time_str in ('NAN', 'NONE', 'NULL', ''):
            return None
        
        # Try each parser in order of likelihood
        parsers = [
            cls._parse_12hour,
            cls._parse_24hour_colon,
            cls._parse_military,
            cls._parse_simple_int,
            cls._parse_iso_time
        ]
        
        for parser in parsers:
            result = parser(time_str)
            if result is not None:
                return result
        
        return None
    
    @classmethod
    def _parse_12hour(cls, time_str: str) -> Optional[int]:
        """Parse 12-hour format: '9:00 AM', '6:00 PM'"""
        if 'AM' not in time_str and 'PM' not in time_str:
            return None
        
        try:
            is_pm = 'PM' in time_str
            is_am = 'AM' in time_str
            
            # Remove AM/PM and clean
            clean_str = re.sub(r'[^\d:]', '', time_str)
            
            if ':' in clean_str:
                parts = clean_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
            else:
                hours = int(clean_str)
                minutes = 0
            
            # Convert to 24-hour
            if is_pm and hours < 12:
                hours += 12
            elif is_am and hours == 12:
                hours = 0
            
            return hours * 60 + minutes
        except:
            return None
    
    @classmethod
    def _parse_24hour_colon(cls, time_str: str) -> Optional[int]:
        """Parse 24-hour colon format: '08:00', '18:30'"""
        if ':' not in time_str:
            return None
        
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            
            if 0 <= hours < 24 and 0 <= minutes < 60:
                return hours * 60 + minutes
        except:
            pass
        
        return None
    
    @classmethod
    def _parse_military(cls, time_str: str) -> Optional[int]:
        """Parse military time: '0900', '1830'"""
        clean_str = re.sub(r'[^\d]', '', time_str)
        
        if len(clean_str) < 3:
            return None
        
        try:
            val = int(clean_str)
            hours = val // 100
            minutes = val % 100
            
            if 0 <= hours < 24 and 0 <= minutes < 60:
                return hours * 60 + minutes
        except:
            pass
        
        return None
    
    @classmethod
    def _parse_simple_int(cls, time_str: str) -> Optional[int]:
        """Parse simple integer: '9', '18'"""
        clean_str = re.sub(r'[^\d]', '', time_str)
        
        if not clean_str:
            return None
        
        try:
            val = int(clean_str)
            
            # If value is 0-23, treat as hours
            if 0 <= val < 24:
                return val * 60
        except:
            pass
        
        return None
    
    @classmethod
    def _parse_iso_time(cls, time_str: str) -> Optional[int]:
        """Parse ISO time format: '09:00:00'"""
        if time_str.count(':') != 2:
            return None
        
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            
            if 0 <= hours < 24 and 0 <= minutes < 60:
                return hours * 60 + minutes
        except:
            pass
        
        return None


# ============================================================================
# PART 4: TIME FORMATTING (Minutes → Human-Readable Display)
# ============================================================================

class TimeFormatter:
    """Format canonical time (minutes from midnight) to human-readable strings"""
    
    @classmethod
    def format_12hour(cls, minutes: Optional[int]) -> Optional[str]:
        """
        Format minutes to 12-hour format with AM/PM.
        
        Examples:
            0 → "12:00 AM"
            540 → "9:00 AM"
            720 → "12:00 PM"
            1080 → "6:00 PM"
        """
        if minutes is None:
            return None
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours == 0:
            hour_12 = 12
            period = 'AM'
        elif hours < 12:
            hour_12 = hours
            period = 'AM'
        elif hours == 12:
            hour_12 = 12
            period = 'PM'
        else:
            hour_12 = hours - 12
            period = 'PM'
        
        if mins == 0:
            return f"{hour_12}:00 {period}"
        else:
            return f"{hour_12}:{mins:02d} {period}"
    
    @classmethod
    def format_range(cls, start_minutes: Optional[int], end_minutes: Optional[int]) -> str:
        """
        Format time range.
        
        Example:
            (540, 1080) → "9:00 AM-6:00 PM"
        """
        if start_minutes is None or end_minutes is None:
            return ""
        
        start_str = cls.format_12hour(start_minutes)
        end_str = cls.format_12hour(end_minutes)
        
        return f"{start_str}-{end_str}"


# ============================================================================
# PART 5: DURATION PARSING (Any Format → Integer Minutes)
# ============================================================================

class DurationParser:
    """
    Parse ANY duration/time limit format from SFMTA datasets to integer minutes.
    
    Dataset Field Reference:
    - Parking Regulations (hi6h-neyh): hrlimit (hours as string or float)
    - Meter Schedules (6cqg-dxku): time_limit_minutes (integer minutes)
    - Meter Policies (qq7v-hds4): timelimitminutes (integer minutes)
    - Manual Overrides: hrlimit or time_limit_minutes
    
    Special Cases:
    - 72-hour RPP limit: Applies to permit holders only, should be filtered out
    - Non-permit users in RPP areas have 2hr limit (separate rule)
    """
    
    @classmethod
    def parse(cls, value: Any, unit_hint: str = None, permit_area: str = None) -> Optional[int]:
        """
        Parse any duration format to integer minutes.
        
        Args:
            value: Duration value (string, int, float)
            unit_hint: 'hours' or 'minutes' if known from dataset
            permit_area: RPP area code - if present with 72hr, returns None (filter out)
        
        Returns:
            Integer minutes, or None if no limit or should be filtered
        
        Examples:
            parse("2", "hours") → 120
            parse("120", "minutes") → 120
            parse(2.5, "hours") → 150
            parse("0") → None (no limit)
            parse(72, "hours", "W") → None (72hr RPP - filter out)
        """
        if not value or value in (0, "0", "0.0"):
            return None  # No limit
        
        try:
            # Convert to float first to handle decimals
            num_value = float(value)
            
            if num_value == 0:
                return None
            
            # Special case: 72-hour RPP limit
            # These rules apply to permit holders only and should NOT be displayed
            # Return None to filter them out
            if num_value == 72 and permit_area:
                return None  # Filter out 72hr RPP rules
            
            # Determine unit
            if unit_hint == "hours":
                return int(num_value * 60)
            elif unit_hint == "minutes":
                return int(num_value)
            else:
                # Auto-detect: if value > 24, assume minutes
                if num_value > 24:
                    return int(num_value)
                else:
                    # Assume hours for small values
                    return int(num_value * 60)
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def parse_parking_reg(cls, row: dict) -> Optional[int]:
        """
        Parse duration from Parking Regulations dataset (hi6h-neyh).
        
        Field: hrlimit (hours as string or float)
        Special: 72hr RPP rules are filtered out (return None)
        """
        hrlimit = row.get('hrlimit')
        permit_area = row.get('rpparea1') or row.get('rpparea2')
        
        return cls.parse(hrlimit, unit_hint='hours', permit_area=permit_area)
    
    @classmethod
    def parse_meter_schedule(cls, row: dict) -> Optional[int]:
        """
        Parse duration from Meter Schedules dataset (6cqg-dxku).
        
        Field: time_limit_minutes (integer minutes)
        """
        return cls.parse(row.get('time_limit_minutes'), unit_hint='minutes')
    
    @classmethod
    def parse_meter_policy(cls, row: dict) -> Optional[int]:
        """
        Parse duration from Meter Policies dataset (qq7v-hds4).
        
        Field: timelimitminutes (integer minutes)
        """
        return cls.parse(row.get('timelimitminutes'), unit_hint='minutes')


# ============================================================================
# PART 6: DURATION FORMATTING (Minutes → Human-Readable Display)
# ============================================================================

class DurationFormatter:
    """
    Format canonical duration (integer minutes) to human-readable strings.
    
    Display Rules:
    - ≥ 60 minutes: Show as hours with "hr" (e.g., "2hr", "3hr")
    - < 60 minutes: Show as minutes with "min" (e.g., "15min", "30min")
    - No limit: Show as "No"
    - No space between number and unit
    - Always singular unit (hr, min - not hrs, mins)
    """
    
    @classmethod
    def format_display(cls, minutes: Optional[int]) -> str:
        """
        Format duration for display.
        
        Rules:
        - ≥ 60 minutes → hours (e.g., 120 → "2hr")
        - < 60 minutes → minutes (e.g., 30 → "30min")
        - No limit → "No"
        - No space between number and unit
        - Singular unit always (hr, min)
        
        Examples:
            15 → "15min"
            30 → "30min"
            45 → "45min"
            60 → "1hr"
            90 → "1.5hr"
            120 → "2hr"
            240 → "4hr"
            None → "No"
        """
        if not minutes:
            return "No"
        
        if minutes < 60:
            # Display as minutes
            return f"{minutes}min"
        
        # Display as hours
        hours = minutes / 60
        
        # Show decimal only if not whole number
        if minutes % 60 == 0:
            return f"{int(hours)}hr"
        else:
            return f"{hours:.1f}hr"
    
    @classmethod
    def format_long(cls, minutes: Optional[int]) -> str:
        """
        Format duration for verbose display.
        
        Examples:
            15 → "15 minute limit"
            30 → "30 minute limit"
            60 → "1 hour limit"
            120 → "2 hour limit"
            None → "No time limit"
        """
        if not minutes:
            return "No time limit"
        
        if minutes < 60:
            # Always use singular "minute"
            return f"{minutes} minute limit"
        
        hours = minutes / 60
        
        if minutes % 60 == 0:
            hour_val = int(hours)
            # Always use singular "hour"
            return f"{hour_val} hour limit"
        else:
            return f"{hours:.1f} hour limit"


# ============================================================================
# PART 7: MAIN NORMALIZATION FUNCTION
# ============================================================================

def normalize_regulation(raw_data: Dict[str, Any], dataset_type: str) -> Dict[str, Any]:
    """
    Universal entry point for regulation data normalization.
    
    Args:
        raw_data: Raw record from any SFMTA dataset
        dataset_type: 'street_cleaning' | 'parking_reg' | 'meter' | 'manual'
    
    Returns:
        {
            "canonical": {
                "days": [0,1,2,3,4],
                "time_start": 480,
                "time_end": 1080,
                "duration_minutes": 120,
                "has_limit": true,
                "all_day": false,
                "all_week": false,
                "is_rpp_72hr": false
            },
            "display": {
                "days": "Weekdays",
                "time": "8:00 AM-6:00 PM",
                "duration": "2hr",
                "duration_long": "2 hour limit",
                "summary": "Weekdays 8:00 AM-6:00 PM"
            },
            "raw": {
                "days": "MON-FRI",
                "time_start": "8:00 AM",
                "time_end": "6:00 PM",
                "duration_value": "2",
                "duration_unit": "hours",
                "dataset": "parking_reg"
            }
        }
    """
    # Extract fields based on dataset type
    if dataset_type == 'street_cleaning':
        days_raw = raw_data.get('weekday')
        time_start_raw = raw_data.get('fromhour')
        time_end_raw = raw_data.get('tohour')
        context_text = ""
        duration_minutes = None
        duration_raw = None
        duration_unit = None
        is_rpp_72hr = False
    elif dataset_type == 'parking_reg':
        days_raw = raw_data.get('days')
        time_start_raw = raw_data.get('from_time')
        time_end_raw = raw_data.get('to_time')
        context_text = raw_data.get('regulation', '') or raw_data.get('regdetails', '')
        # Parse duration using dataset-specific adapter
        duration_raw = raw_data.get('hrlimit')
        permit_area = raw_data.get('rpparea1') or raw_data.get('rpparea2')
        # Check if this is the 72hr RPP case (will be filtered out)
        is_rpp_72hr = bool((str(duration_raw) == '72' or duration_raw == 72) and permit_area)
        duration_minutes = DurationParser.parse_parking_reg(raw_data)
        duration_unit = 'hours'
    elif dataset_type == 'meter':
        days_raw = raw_data.get('days_applied')
        time_start_raw = raw_data.get('beg_time_dt') or raw_data.get('from_time')
        time_end_raw = raw_data.get('end_time_dt') or raw_data.get('to_time')
        context_text = raw_data.get('schedule_type', '')
        # Try both meter schedule and meter policy fields
        duration_minutes = (DurationParser.parse_meter_schedule(raw_data) or
                          DurationParser.parse_meter_policy(raw_data))
        duration_raw = raw_data.get('time_limit_minutes') or raw_data.get('timelimitminutes')
        duration_unit = 'minutes'
        is_rpp_72hr = False
    elif dataset_type == 'manual':
        days_raw = raw_data.get('weekday')
        time_start_raw = raw_data.get('fromhour')
        time_end_raw = raw_data.get('tohour')
        context_text = raw_data.get('regulation', '')
        # Manual overrides may have duration in various formats
        duration_raw = raw_data.get('hrlimit') or raw_data.get('time_limit_minutes')
        if duration_raw:
            # Try to detect unit from field name or value
            if 'hrlimit' in raw_data:
                duration_minutes = DurationParser.parse(duration_raw, unit_hint='hours')
                duration_unit = 'hours'
            else:
                duration_minutes = DurationParser.parse(duration_raw, unit_hint='minutes')
                duration_unit = 'minutes'
        else:
            duration_minutes = None
            duration_unit = None
        is_rpp_72hr = False
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    # Parse to canonical format
    days_canonical = DayParser.parse(days_raw)
    time_start_minutes = TimeParser.parse(time_start_raw)
    time_end_minutes = TimeParser.parse(time_end_raw)
    
    # Generate display strings
    days_display = DayFormatter.format_display(days_canonical, context_text)
    time_display = TimeFormatter.format_range(time_start_minutes, time_end_minutes)
    duration_display = DurationFormatter.format_display(duration_minutes)
    duration_long = DurationFormatter.format_long(duration_minutes)
    
    # Build summary
    if days_display and time_display:
        summary = f"{days_display} {time_display}"
    elif days_display:
        summary = days_display
    elif time_display:
        summary = time_display
    else:
        summary = ""
    
    return {
        "canonical": {
            "days": days_canonical,
            "time_start": time_start_minutes,
            "time_end": time_end_minutes,
            "duration_minutes": duration_minutes,
            "has_limit": duration_minutes is not None,
            "all_day": time_start_minutes == 0 and time_end_minutes == 1439,
            "all_week": len(days_canonical) == 7,
            "is_rpp_72hr": is_rpp_72hr
        },
        "display": {
            "days": days_display,
            "time": time_display,
            "duration": duration_display,
            "duration_long": duration_long,
            "summary": summary
        },
        "raw": {
            "days": days_raw,
            "time_start": time_start_raw,
            "time_end": time_end_raw,
            "duration_value": duration_raw,
            "duration_unit": duration_unit,
            "dataset": dataset_type
        }
    }


# ============================================================================
# CONVENIENCE FUNCTIONS (For Direct Use)
# ============================================================================

def parse_days(day_input: Any) -> List[int]:
    """Convenience function to parse days directly"""
    return DayParser.parse(day_input)


def format_day_display(days: List[int], context: str = None) -> str:
    """Convenience function to format days for display"""
    return DayFormatter.format_display(days, context)


def parse_time_to_minutes(time_input: Any) -> Optional[int]:
    """Convenience function to parse time to minutes"""
    return TimeParser.parse(time_input)


def format_time_12hour(minutes: Optional[int]) -> Optional[str]:
    """Convenience function to format time in 12-hour format"""
    return TimeFormatter.format_12hour(minutes)

def parse_duration(value: Any, unit_hint: str = None, permit_area: str = None) -> Optional[int]:
    """
    Convenience function to parse duration to integer minutes.
    
    Args:
        value: Duration value (string, int, float)
        unit_hint: 'hours' or 'minutes' if known from dataset
        permit_area: RPP area code (72hr RPP rules will be filtered out)
    
    Returns:
        Integer minutes, or None if no limit or should be filtered
    
    Examples:
        parse_duration("2", "hours") → 120
        parse_duration(120, "minutes") → 120
        parse_duration(2.5, "hours") → 150
        parse_duration(72, "hours", "W") → None (filtered out)
    """
    return DurationParser.parse(value, unit_hint, permit_area)


def format_duration_display(minutes: Optional[int]) -> str:
    """
    Convenience function to format duration for display.
    
    Examples:
        format_duration_display(30) → "30min"
        format_duration_display(120) → "2hr"
        format_duration_display(None) → "No"
    """
    return DurationFormatter.format_display(minutes)


def format_duration_long(minutes: Optional[int]) -> str:
    """
    Convenience function to format duration for verbose display.
    
    Examples:
        format_duration_long(30) → "30 minute limit"
        format_duration_long(120) → "2 hour limit"
        format_duration_long(None) → "No time limit"
    """
    return DurationFormatter.format_long(minutes)


# ============================================================================
# PART 8: CAP COLOR NORMALIZATION (Meter Vehicle Restrictions)
# ============================================================================

class CapColorNormalizer:
    """
    Normalize meter cap colors to standardized vehicle restrictions.
    
    Complete Cap Color Legend (Revised Dec 31, 2024):
    - BLACK = Motorcycle only
    - BROWN = Tour Bus only
    - GREY = General parking (standard vehicles/cars)
    - PURPLE = Boat Trailer only
    - RED = Commercial Vehicles with 6+ wheels (same display as YELLOW)
    - YELLOW = Commercial Vehicle only
    - GREEN = General parking (standard vehicles/cars)
    
    For Curby Users (standard cars):
    - ELIGIBLE: GREY, GREEN only
    - INELIGIBLE: BLACK, BROWN, PURPLE, RED, YELLOW
    
    Default assumption: Curby users are in standard cars
    Blockface-level aggregation uses majority rule
    """
    
    # Standardized color classifications
    CAR_ELIGIBLE_COLORS = {'GREY', 'GRAY', 'GREEN', 'GRN'}
    MOTORCYCLE_COLORS = {'BLACK', 'BLK'}
    TOUR_BUS_COLORS = {'BROWN', 'BRN'}
    BOAT_TRAILER_COLORS = {'PURPLE', 'PRP', 'PURP'}
    COMMERCIAL_COLORS = {'YELLOW', 'YLW', 'RED'}  # RED = 6+ wheels, YELLOW = commercial
    
    @classmethod
    def normalize_cap_color(cls, cap_color: Any) -> Dict[str, Any]:
        """
        Normalize a single meter cap color to standardized format.
        
        Complete Cap Color Legend (Dec 31, 2024):
        - BLACK = Motorcycle only
        - BROWN = Tour Bus only
        - GREY = General parking (Curby users eligible)
        - GREEN = General parking (Curby users eligible)
        - PURPLE = Boat Trailer only
        - RED = Commercial Vehicles 6+ wheels
        - YELLOW = Commercial Vehicle
        
        For Curby Users (standard cars): Only GREY and GREEN are eligible
        
        Args:
            cap_color: Raw cap color value from meter dataset
        
        Returns:
            {
                'canonical': {
                    'color': str,
                    'restriction': str,
                    'is_restricted': bool,
                    'vehicle_type': str
                },
                'display': {
                    'restriction_text': str,
                    'user_eligible': bool
                }
            }
        """
        # Handle None, empty, or NaN - default to general parking
        if not cap_color or str(cap_color).upper().strip() in ('', 'NAN', 'NONE', 'NULL'):
            return {
                'canonical': {
                    'color': 'GREY',
                    'restriction': 'GENERAL',
                    'is_restricted': False,
                    'vehicle_type': 'Standard vehicles'
                },
                'display': {
                    'restriction_text': 'General parking',
                    'user_eligible': True
                }
            }
        
        cap_upper = str(cap_color).upper().strip()
        
        # GREY or GREEN = General parking (Curby eligible)
        if cap_upper in cls.CAR_ELIGIBLE_COLORS:
            return {
                'canonical': {
                    'color': cap_upper,
                    'restriction': 'GENERAL',
                    'is_restricted': False,
                    'vehicle_type': 'Standard vehicles'
                },
                'display': {
                    'restriction_text': 'General parking',
                    'user_eligible': True
                }
            }
        
        # BLACK = Motorcycle only
        if cap_upper in cls.MOTORCYCLE_COLORS:
            return {
                'canonical': {
                    'color': 'BLACK',
                    'restriction': 'MOTORCYCLE',
                    'is_restricted': True,
                    'vehicle_type': 'Motorcycle'
                },
                'display': {
                    'restriction_text': 'Motorcycle only',
                    'user_eligible': False
                }
            }
        
        # BROWN = Tour Bus only
        if cap_upper in cls.TOUR_BUS_COLORS:
            return {
                'canonical': {
                    'color': 'BROWN',
                    'restriction': 'TOUR_BUS',
                    'is_restricted': True,
                    'vehicle_type': 'Tour Bus'
                },
                'display': {
                    'restriction_text': 'Tour Bus only',
                    'user_eligible': False
                }
            }
        
        # PURPLE = Boat Trailer only
        if cap_upper in cls.BOAT_TRAILER_COLORS:
            return {
                'canonical': {
                    'color': 'PURPLE',
                    'restriction': 'BOAT_TRAILER',
                    'is_restricted': True,
                    'vehicle_type': 'Boat Trailer'
                },
                'display': {
                    'restriction_text': 'Boat Trailer only',
                    'user_eligible': False
                }
            }
        
        # YELLOW or RED = Commercial
        if cap_upper in cls.COMMERCIAL_COLORS:
            if cap_upper == 'RED':
                text = 'Commercial Vehicles 6+ wheels'
            else:
                text = 'Commercial Vehicle'
            
            return {
                'canonical': {
                    'color': cap_upper,
                    'restriction': 'COMMERCIAL',
                    'is_restricted': True,
                    'vehicle_type': 'Commercial'
                },
                'display': {
                    'restriction_text': text,
                    'user_eligible': False
                }
            }
        
        # Unknown - default to general but flag
        return {
            'canonical': {
                'color': cap_upper,
                'restriction': 'UNKNOWN',
                'is_restricted': False,
                'vehicle_type': 'Unknown'
            },
            'display': {
                'restriction_text': f'Unknown: {cap_upper}',
                'user_eligible': True
            }
        }
    
    @classmethod
    def aggregate_blockface_cap_colors(cls, meters: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate cap colors at blockface level using majority rule.
        
        For Curby users (standard cars):
        - ELIGIBLE: GREY, GREEN only
        - INELIGIBLE: BLACK, BROWN, PURPLE, RED, YELLOW
        
        Rules:
        - If ALL meters eligible → Block eligible
        - If MAJORITY eligible → Block eligible
        - If MAJORITY ineligible → Block ineligible
        
        Args:
            meters: List of meter objects with 'cap_color' field
        
        Returns:
            Aggregation with eligibility for Curby users (standard cars)
        """
        if not meters:
            return {
                'is_restricted': False,
                'restriction_type': 'NONE',
                'eligible_meter_count': 0,
                'ineligible_meter_count': 0,
                'meter_count': 0,
                'majority_rule': 'NONE',
                'eligible_for_curby_user': False,
                'display_text': 'No meters',
                'display_restriction': None
            }
        
        eligible_count = 0
        ineligible_count = 0
        restriction_types = {}
        
        for meter in meters:
            cap = meter.get('cap_color')
            normalized = cls.normalize_cap_color(cap)
            
            if normalized['display']['user_eligible']:
                eligible_count += 1
            else:
                ineligible_count += 1
                rtype = normalized['canonical']['restriction']
                restriction_types[rtype] = restriction_types.get(rtype, 0) + 1
        
        total = len(meters)
        
        # Determine eligibility
        if eligible_count == total:
            rule = 'ALL_ELIGIBLE'
            eligible = True
            text = f"All {total} meters: General parking"
            restriction = None
        elif eligible_count > ineligible_count:
            rule = 'MAJORITY_ELIGIBLE'
            eligible = True
            text = f"Majority ({eligible_count}/{total}) general parking"
            restriction = None
        elif ineligible_count == total:
            rule = 'ALL_INELIGIBLE'
            eligible = False
            main_type = max(restriction_types, key=restriction_types.get)
            text = f"All {total} meters: {main_type} only"
            restriction = main_type
        else:
            rule = 'MAJORITY_INELIGIBLE'
            eligible = False
            main_type = max(restriction_types, key=restriction_types.get)
            text = f"Majority ({ineligible_count}/{total}) restricted"
            restriction = main_type
        
        return {
            'is_restricted': ineligible_count > 0,
            'restriction_type': restriction or 'GENERAL',
            'eligible_meter_count': eligible_count,
            'ineligible_meter_count': ineligible_count,
            'meter_count': total,
            'majority_rule': rule,
            'eligible_for_curby_user': eligible,
            'restriction_breakdown': restriction_types,
            'display_text': text,
            'display_restriction': restriction
        }


# ============================================================================
# PART 9: METER SCHEDULE PRIORITY AND SELECTION
# ============================================================================

class MeterScheduleSelector:
    """
    Select effective meter schedule based on priority hierarchy and time.
    
    Implementation Note:
    - Schedules are pre-sorted by priority during ingestion (prioritize_meter_schedules)
    - Stored in meter['schedules'] array with highest priority first
    - Runtime selection uses first matching schedule for given day/time
    
    Priority Hierarchy (Revised Dec 31, 2024):
    1. Tow (highest) - No parking at meter during this time
    2. Alternate - Different rules on certain days (special events, etc.)
    3. Operating Schedule (OP) - Standard paid operation
    4. Pre - Prepay allowed (same priority as Free, treated as Free for display)
    5. Free (lowest) - No payment required (same priority as Pre)
    
    Note: Schedule type values in database use title case ('Tow', 'Alternate', 'Operating Schedule')
    not uppercase ('TOW', 'ALTERNATE', 'OP') as originally documented.
    
    TOW Schedule Rules (Blockface-Level):
    - If ALL meters have TOW schedules → Check for overlap with user duration
    - If ANY TOW overlaps user duration → Block INELIGIBLE
    - If MAJORITY have TOW → Use majority rule
    - If MIXED → Use majority rule (most common condition)
    """
    
    SCHEDULE_PRIORITY = {
        'Tow': 1,                    # Database uses title case
        'TOW': 1,                    # Legacy support
        'Alternate': 2,
        'ALTERNATE': 2,              # Legacy support
        'Operating Schedule': 3,     # Database uses full name
        'OP': 3,                     # Legacy support
        'Pre': 4,                    # Same priority as Free
        'PRE': 4,                    # Legacy support
        'Free': 4,                   # Same priority as Pre
        'FREE': 4                    # Legacy support
    }
    
    @classmethod
    def prioritize_schedules(cls, schedules: List[Dict]) -> List[Dict]:
        """
        Sort meter schedules by priority (TOW > ALTERNATE > OP + PRE > FREE).
        
        Args:
            schedules: List of schedule objects with 'schedule_type' field
        
        Returns:
            Sorted list with highest priority first
        """
        if not schedules:
            return []
        
        return sorted(
            schedules,
            key=lambda s: cls.SCHEDULE_PRIORITY.get(s.get('schedule_type', 'OP'), 99)
        )
    
    @classmethod
    def get_effective_schedule(cls, meter: Dict, check_day: int, check_time_min: int) -> Optional[Dict]:
        """
        Get the effective schedule for a meter at a specific day/time.
        
        Args:
            meter: Meter object with 'schedules' array (already prioritized)
            check_day: Day of week (0=Mon, 6=Sun)
            check_time_min: Time in minutes from midnight
        
        Returns:
            Effective schedule dict or None
        """
        schedules = meter.get('schedules', [])
        if not schedules:
            return None
        
        # Sort by priority
        prioritized = cls.prioritize_schedules(schedules)
        
        # Find first active schedule
        for schedule in prioritized:
            if cls.is_schedule_active(schedule, check_day, check_time_min):
                return schedule
        
        return None
    
    @classmethod
    def is_schedule_active(cls, schedule: Dict, check_day: int, check_time_min: int) -> bool:
        """
        Check if a schedule is active on given day/time.
        
        Args:
            schedule: Schedule object with days_applied, from_time, to_time
            check_day: Day of week (0=Mon, 6=Sun)
            check_time_min: Time in minutes from midnight
        
        Returns:
            True if schedule is active
        """
        # Parse days
        days_applied = schedule.get('days_applied')
        schedule_days = parse_days(days_applied)
        
        if check_day not in schedule_days:
            return False
        
        # Parse times
        from_time = schedule.get('from_time')
        to_time = schedule.get('to_time')
        
        from_min = parse_time_to_minutes(from_time)
        to_min = parse_time_to_minutes(to_time)
        
        if from_min is None or to_min is None:
            return False
        
        # Check time overlap
        return cls.check_time_overlap(from_min, to_min, check_time_min, 0)
    
    @staticmethod
    def check_time_overlap(schedule_start: int, schedule_end: int,
                          user_start: int, user_duration_min: int) -> bool:
        """
        Check if schedule overlaps with user's parking duration.
        
        Args:
            schedule_start: Schedule start time (minutes from midnight)
            schedule_end: Schedule end time (minutes from midnight)
            user_start: User start time (minutes from midnight)
            user_duration_min: How long user wants to park (minutes)
        
        Returns:
            True if there is overlap
        """
        user_end = user_start + user_duration_min
        
        # Handle overnight schedules (end < start)
        if schedule_end < schedule_start:
            schedule_end += 1440  # Add 24 hours
        
        # Handle user overnight parking
        if user_end >= 1440:
            user_end = user_end % 1440
            # Check both today and tomorrow
            return (schedule_start <= user_start or user_start <= schedule_end or
                    schedule_start <= user_end or user_end <= schedule_end)
        
        # Standard overlap check
        return not (user_end <= schedule_start or user_start >= schedule_end)
    
    @classmethod
    def aggregate_blockface_tow_schedules(cls, meters: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate TOW schedules at blockface level with majority rule.
        
        Rules:
        - If ALL meters have TOW → Check for overlap, block if any overlap
        - If MAJORITY have TOW → Use majority rule
        - If MIXED → Use majority rule (most common condition)
        
        Args:
            meters: List of meter objects with 'schedules' (already prioritized)
        
        Returns:
            {
                'has_tow': bool,
                'all_have_tow': bool,
                'tow_schedules': List[Dict],  # All TOW schedules for overlap checking
                'meters_with_tow': int,
                'meters_without_tow': int,
                'majority_rule': str,  # 'TOW', 'OPERATING'
                'blockface_rule': str,  # 'ALL_TOW', 'MAJORITY_TOW', 'MAJORITY_OPERATING'
                'display_text': str
            }
        """
        if not meters:
            return {
                'has_tow': False,
                'all_have_tow': False,
                'tow_schedules': [],
                'meters_with_tow': 0,
                'meters_without_tow': 0,
                'majority_rule': 'OPERATING',
                'blockface_rule': 'NO_TOW',
                'display_text': 'No meters on this block'
            }
        
        all_tow_schedules = []
        meters_with_tow = 0
        meters_without_tow = 0
        
        for meter in meters:
            meter_has_tow = False
            for schedule in meter.get('schedules', []):
                if schedule.get('schedule_type') == 'Tow':
                    meter_has_tow = True
                    all_tow_schedules.append({
                        'days_applied': schedule.get('days_applied'),
                        'from_time': schedule.get('from_time'),
                        'to_time': schedule.get('to_time'),
                        'from_time_min': parse_time_to_minutes(schedule.get('from_time')),
                        'to_time_min': parse_time_to_minutes(schedule.get('to_time'))
                    })
            
            if meter_has_tow:
                meters_with_tow += 1
            else:
                meters_without_tow += 1
        
        total_meters = len(meters)
        all_have_tow = (meters_with_tow == total_meters)
        
        # Determine majority rule
        if meters_with_tow > meters_without_tow:
            majority_rule = 'TOW'
            majority_text = f"Majority ({meters_with_tow}/{total_meters}) have tow-away"
        else:
            majority_rule = 'OPERATING'
            majority_text = f"Majority ({meters_without_tow}/{total_meters}) are operating"
        
        # Determine blockface rule
        if all_have_tow:
            blockface_rule = 'ALL_TOW'
            display_text = f"All {total_meters} meters have tow-away schedules"
        elif majority_rule == 'TOW':
            blockface_rule = 'MAJORITY_TOW'
            display_text = majority_text
        else:
            blockface_rule = 'MAJORITY_OPERATING'
            display_text = majority_text
        
        return {
            'has_tow': meters_with_tow > 0,
            'all_have_tow': all_have_tow,
            'tow_schedules': all_tow_schedules,
            'meters_with_tow': meters_with_tow,
            'meters_without_tow': meters_without_tow,
            'majority_rule': majority_rule,
            'blockface_rule': blockface_rule,
            'display_text': display_text
        }


# ============================================================================
# PART 10: SPECIAL EVENT ZONE DISPLAY FORMATTING
# ============================================================================

class SpecialEventZoneFormatter:
    """
    Format display text for meters in special event zones (Oracle Park, Chase Center).
    
    Rules (Dec 31, 2024 - CORRECTED):
    - Line 1: "[Zone Name] Schedule and Rates may apply. See schedule for details."
      - "schedule" is hyperlinked to SFMTA URL
      - Oracle Park only: "Oracle Park Schedule and Rates may apply..."
      - Chase Center only: "Chase Center Schedule and Rates may apply..."
      - Both zones: "Special Event Schedule and Rates may apply..."
    
    - Line 2+: "All other dates" + meter operating schedules
      - If meter has multiple schedules on different days:
        * Line 2: Schedule containing Monday (e.g., M-F) - "Weekdays [duration] [time] ($[rate]/hr)"
        * Line 3: Non-Monday schedules in chrono order - "Weekends [duration] [time] ($[rate]/hr)"
      - If meter has single schedule:
        * Line 2: "All other dates [duration] [days] [time] ($[rate]/hr)"
    """
    
    SFMTA_SCHEDULE_URL = "https://www.sfmta.com/notices/current-special-event-parking-regulations-schedule"
    
    @classmethod
    def format_special_event_display(cls,
                                     in_ballpark_zone: bool,
                                     in_arena_zone: bool,
                                     base_schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format multi-line display for special event zone meters.
        
        Args:
            in_ballpark_zone: True if meter is in Oracle Park zone
            in_arena_zone: True if meter is in Chase Center zone
            base_schedules: List of base operating schedule dicts (may have multiple)
        
        Returns:
            {
                'line1': str,  # Special event notice with hyperlinked "schedule"
                'line2': str,  # "All other dates" + Monday-containing schedule
                'line3': str,  # (Optional) Non-Monday schedule if exists
                'schedule_url': str,  # URL for hyperlink
                'has_special_event': bool
            }
        
        Examples:
            Oracle Park with single schedule:
                line1: "Oracle Park Schedule and Rates may apply. See schedule for details."
                line2: "All other dates 2hr limit M-Sa 9am-6pm ($4.00/hr)"
                line3: ""
            
            Chase Center with M-F and Sa-Su schedules:
                line1: "Chase Center Schedule and Rates may apply. See schedule for details."
                line2: "All other dates Weekdays 2hr limit 9am-6pm ($2.50/hr)"
                line3: "Weekends 4hr limit 12pm-10pm ($3.00/hr)"
            
            Both zones (overlap):
                line1: "Special Event Schedule and Rates may apply. See schedule for details."
                line2: "All other dates Daily 2hr limit 9am-6pm ($3.00/hr)"
                line3: ""
        """
        # Determine which zone(s) the meter is in
        if not in_ballpark_zone and not in_arena_zone:
            # Not in any special event zone - return empty
            return {
                'line1': '',
                'line2': '',
                'line3': '',
                'schedule_url': '',
                'has_special_event': False
            }
        
        # Build Line 1: Special event notice
        if in_ballpark_zone and in_arena_zone:
            # Overlap zone
            zone_name = "Special Event"
        elif in_ballpark_zone:
            # Ballpark only
            zone_name = "Oracle Park"
        else:
            # Arena only
            zone_name = "Chase Center"
        
        line1 = f"{zone_name} Schedule and Rates may apply. See schedule for details."
        
        # Build Line 2 and Line 3: "All other dates" + schedules
        line2, line3 = cls._format_base_schedule_lines(base_schedules)
        
        return {
            'line1': line1,
            'line2': line2,
            'line3': line3,
            'schedule_url': cls.SFMTA_SCHEDULE_URL,
            'has_special_event': True
        }
    
    @classmethod
    def _format_base_schedule_lines(cls, schedules: List[Dict[str, Any]]) -> tuple:
        """
        Format base schedules as multi-line display.
        
        Rules:
        - If no schedules: "All Other Days check meter for schedule and rates"
        - If single schedule covering all 7 days: "All Other Days [schedule]"
        - If multiple schedules:
          * Line 2: "All Other Weekdays [schedule]" (Monday-containing)
          * Line 3: "All Other Weekends [schedule]" (non-Monday)
        - Capitalization: "All Other Days" or "All Other Weekdays/Weekends"
        
        Args:
            schedules: List of schedule dicts with duration_minutes, days, time, rate
        
        Returns:
            (line2, line3) tuple of formatted strings
        """
        if not schedules:
            return ("All Other Days check meter for schedule and rate", "")
        
        # If single schedule, check if it covers all 7 days
        if len(schedules) == 1:
            schedule = schedules[0]
            days = schedule.get('days', [])
            
            # If covers all 7 days, use "All Other Days"
            if len(days) == 7:
                line2 = "All Other Days " + cls._format_single_schedule(schedule)
                return (line2, "")
            else:
                # Single schedule but not all days - still use "All Other Days"
                line2 = "All Other Days " + cls._format_single_schedule(schedule)
                return (line2, "")
        
        # Multiple schedules - separate into Monday-containing and non-Monday
        monday_schedule = None
        non_monday_schedules = []
        
        for schedule in schedules:
            days = schedule.get('days', [])
            if 0 in days:  # 0 = Monday
                monday_schedule = schedule
            else:
                non_monday_schedules.append(schedule)
        
        # If no Monday schedule, use first schedule as primary
        if not monday_schedule:
            monday_schedule = schedules[0]
            non_monday_schedules = schedules[1:] if len(schedules) > 1 else []
        
        # Format Line 2: "All Other Weekdays" + Monday schedule
        line2 = "All Other Weekdays " + cls._format_single_schedule(monday_schedule)
        
        # Format Line 3: "All Other Weekends" + non-Monday schedule (if exists)
        if non_monday_schedules:
            line3 = "All Other Weekends " + cls._format_single_schedule(non_monday_schedules[0])
        else:
            line3 = ""
        
        return (line2, line3)
    
    @classmethod
    def _format_single_schedule(cls, schedule: Dict[str, Any]) -> str:
        """
        Format a single schedule as "[days] [duration] [time] ($[rate]/hr)".
        
        Args:
            schedule: Dict with duration_minutes, days, from_time, to_time, rate
        
        Returns:
            Formatted string like "Weekdays 2hr limit 9am-6pm ($2.50/hr)"
        """
        # Extract schedule components
        duration_min = schedule.get('duration_minutes')
        days = schedule.get('days', [])
        from_time = schedule.get('from_time')
        to_time = schedule.get('to_time')
        rate = schedule.get('rate')
        
        # Format days
        days_display = format_day_display(days) if days else "Daily"
        
        # Format duration
        if duration_min:
            duration_display = format_duration_display(duration_min)
            duration_text = f"{duration_display} limit"
        else:
            duration_text = "No limit"
        
        # Format time range
        from_min = parse_time_to_minutes(from_time)
        to_min = parse_time_to_minutes(to_time)
        if from_min is not None and to_min is not None:
            # Use simplified time format (9am, 6pm instead of 9:00 AM, 6:00 PM)
            from_str = cls._format_simple_time(from_min)
            to_str = cls._format_simple_time(to_min)
            time_text = f"{from_str}-{to_str}"
        else:
            time_text = ""
        
        # Format rate
        if rate and float(rate) > 0:
            rate_text = f"(${float(rate):.2f}/hr)"
        else:
            rate_text = "(Free)"
        
        # Combine components
        parts = [days_display, duration_text]
        if time_text:
            parts.append(time_text)
        parts.append(rate_text)
        
        return " ".join(parts)
    
    @staticmethod
    def _format_simple_time(minutes: int) -> str:
        """
        Format time in simplified format (9am, 6pm, 12pm).
        
        Args:
            minutes: Minutes from midnight
        
        Returns:
            Simplified time string like "9am", "6pm", "12pm"
        """
        hours = minutes // 60
        mins = minutes % 60
        
        if hours == 0:
            hour_12 = 12
            period = 'am'
        elif hours < 12:
            hour_12 = hours
            period = 'am'
        elif hours == 12:
            hour_12 = 12
            period = 'pm'
        else:
            hour_12 = hours - 12
            period = 'pm'
        
        # Only show minutes if not on the hour
        if mins == 0:
            return f"{hour_12}{period}"
        else:
            return f"{hour_12}:{mins:02d}{period}"


# ============================================================================
# CONVENIENCE FUNCTIONS FOR CAP COLOR AND METER SCHEDULES
# ============================================================================

def normalize_cap_color(cap_color: Any) -> Dict[str, Any]:
    """
    Convenience function to normalize a single cap color.
    
    Examples:
        normalize_cap_color('YELLOW') → {'canonical': {'restriction': 'COMMERCIAL'}, ...}
        normalize_cap_color('GREEN') → {'canonical': {'restriction': 'STANDARD'}, ...}
    """
    return CapColorNormalizer.normalize_cap_color(cap_color)


def aggregate_blockface_cap_colors(meters: List[Dict]) -> Dict[str, Any]:
    """
    Convenience function to aggregate cap colors at blockface level.
    
    Args:
        meters: List of meter objects with 'cap_color' field
    
    Returns:
        Aggregation result with majority rule and eligibility
    """
    return CapColorNormalizer.aggregate_blockface_cap_colors(meters)


def prioritize_meter_schedules(schedules: List[Dict]) -> List[Dict]:
    """
    Convenience function to sort meter schedules by priority.
    
    Priority: TOW > ALTERNATE > OP + PRE > FREE
    """
    return MeterScheduleSelector.prioritize_schedules(schedules)


def get_effective_meter_schedule(meter: Dict, check_day: int, check_time_min: int) -> Optional[Dict]:
    """
    Convenience function to get effective schedule for a meter at specific time.
    """
    return MeterScheduleSelector.get_effective_schedule(meter, check_day, check_time_min)


def aggregate_blockface_tow_schedules(meters: List[Dict]) -> Dict[str, Any]:
    """
    Convenience function to aggregate TOW schedules at blockface level.
    """
    return MeterScheduleSelector.aggregate_blockface_tow_schedules(meters)


def format_special_event_zone_display(in_ballpark_zone: bool,
                                      in_arena_zone: bool,
                                      base_schedule: Dict[str, Any]) -> Dict[str, str]:
    """
    Convenience function to format special event zone display.
    
    Args:
        in_ballpark_zone: True if meter is in Oracle Park zone
        in_arena_zone: True if meter is in Chase Center zone
        base_schedule: Base operating schedule dict
    
    Returns:
        {
            'line1': str,  # Special event notice with SFMTA link
            'line2': str,  # "All Other Days" + base schedule
            'has_special_event': bool
        }
    """
    return SpecialEventZoneFormatter.format_special_event_display(
        in_ballpark_zone, in_arena_zone, base_schedule
    )


def format_meter_without_schedule(in_special_event_zone: bool) -> str:
    """
    Format display message for meters without operating schedules.
    
    Args:
        in_special_event_zone: True if meter is in a special event zone
    
    Returns:
        Appropriate message based on whether meter is in special event zone
    
    Examples:
        format_meter_without_schedule(True) → "All Other Days check meter for schedule and rate"
        format_meter_without_schedule(False) → "Check meter for schedule and rate"
    """
    if in_special_event_zone:
        return "All Other Days check meter for schedule and rate"
    else:
        return "Check meter for schedule and rate"


# ============================================================================
# PART 11: RULE DISPLAY FORMATTING FOR MODAL UI
# ============================================================================

from datetime import datetime, timedelta
from typing import Tuple


class RuleDisplayFormatter:
    """
    Complete rule display formatting for modal UI.
    Pre-computes all display strings during ingestion for consistent, performant rendering.
    
    Responsibilities:
    - Generate complete display text for each rule
    - Sort rules by frequency (most common first) then Monday-first
    - Calculate next upcoming restriction
    - Provide all text content for modal body (frontend owns design/layout)
    
    Modal Content Ownership:
    - Backend: ALL text content (location, cross streets, rules, next restriction)
    - Frontend: Design, layout, spacing, fonts, colors, banner, buttons
    """
    
    # Rule frequency order (most common/important first)
    RULE_FREQUENCY_ORDER = {
        'street-sweeping': 1,      # Most common and important
        'time-limit': 2,           # Very common
        'metered': 3,              # Common in commercial areas
        'rpp-zone': 4,             # Common in residential
        'no-parking': 5,           # Less common
        'tow-away': 6,             # Specific zones
        'parking-regulation': 7    # Catch-all
    }
    
    @classmethod
    def _format_simple_time(cls, minutes: int) -> str:
        """
        Format time in simplified format (8am, 6pm, 12am).
        No colons for on-the-hour times.
        
        Args:
            minutes: Minutes from midnight
        
        Returns:
            Simplified time string like "8am", "6pm", "12:30am"
        """
        hours = minutes // 60
        mins = minutes % 60
        
        if hours == 0:
            hour_12 = 12
            period = 'am'
        elif hours < 12:
            hour_12 = hours
            period = 'am'
        elif hours == 12:
            hour_12 = 12
            period = 'pm'
        else:
            hour_12 = hours - 12
            period = 'pm'
        
        # Only show minutes if not on the hour
        if mins == 0:
            return f"{hour_12}{period}"
        else:
            return f"{hour_12}:{mins:02d}{period}"
    
    @classmethod
    def _format_time_range_simple(cls, start_min: Optional[int], end_min: Optional[int]) -> str:
        """Format time range in simplified format: 8am-6pm"""
        if start_min is None or end_min is None:
            return ""
        return f"{cls._format_simple_time(start_min)}-{cls._format_simple_time(end_min)}"
    
    @classmethod
    def format_rule_display_text(cls, rule: Dict[str, Any]) -> Optional[str]:
        """
        Generate complete display text for a single rule.
        
        Standardized Exception Suffixes (Dec 31, 2024):
        - RPP Exception: "except permit" (lowercase, consistent)
        - Government Permit: "except government permit" (lowercase, consistent)
        
        Format Examples:
            "Street Cleaning Thu 12am-6am"
            "2hr limit Weekdays 8am-6pm except permit"
            "No Parking M-F 8am-6pm except permit"
            "2hr limit Weekdays 8am-6pm except government permit"
            "No oversized vehicles"
            "Meter M-Sa 9am-6pm ($4.00/hr)"
        
        Args:
            rule: Rule dict with canonical and display fields
        
        Returns:
            Complete display string ready for UI, or None to skip this rule
        """
        rule_type = rule.get('type', 'parking-regulation')
        regulation_text = str(rule.get('regulation', '')).lower()
        
        # SKIP: Paid/Pay + Permit regulations (meter dataset handles these)
        if 'paid' in regulation_text or 'pay or permit' in regulation_text:
            return None
        
        # Get canonical fields for time formatting
        start_time_min = rule.get('startTimeMin')
        end_time_min = rule.get('endTimeMin')
        time_range = cls._format_time_range_simple(start_time_min, end_time_min)
        
        # Get display fields
        display_days = rule.get('displayDays', '')
        display_duration = rule.get('displayDuration', '')
        
        # Determine exception suffix
        exception_suffix = cls._get_exception_suffix(rule)
        
        # Build description based on type
        if rule_type == 'street-sweeping':
            # "Street Cleaning Thu 12am-6am"
            parts = ['Street Cleaning']
            if display_days:
                parts.append(display_days)
            if time_range:
                parts.append(time_range)
            return ' '.join(parts)
        
        elif rule_type == 'time-limit':
            # "2hr limit Weekdays 8am-6pm except permit"
            # "4hr limit M-F 8am-6pm" (no RPP)
            # "2hr limit Weekdays 8am-6pm except government permit"
            parts = []
            if display_duration:
                parts.append(f"{display_duration} limit")
            if display_days:
                parts.append(display_days)
            if time_range:
                parts.append(time_range)
            
            # Add exception suffix if present
            if exception_suffix:
                parts.append(exception_suffix)
            
            return ' '.join(parts) if parts else 'Time limit'
        
        elif rule_type == 'metered':
            # "2hr Meter M-Sa 9am-6pm ($4.00/hr)" (with limit)
            # "Meter M-Sa 9am-6pm ($4.00/hr)" (without limit)
            rate = rule.get('rate')
            parts = []
            
            # Add duration if present
            if display_duration and display_duration != 'No':
                parts.append(f"{display_duration} Meter")
            else:
                parts.append('Meter')
            
            if display_days:
                parts.append(display_days)
            if time_range:
                parts.append(time_range)
            
            if rate:
                try:
                    rate_float = float(rate)
                    parts.append(f"(${rate_float:.2f}/hr)")
                except (ValueError, TypeError):
                    pass
            
            return ' '.join(parts)
        
        elif rule_type == 'rpp-zone':
            # Skip standalone RPP zones - they're merged with time-limit rules
            return None
        
        elif rule_type == 'no-parking':
            # "No Parking" (always)
            # "No Parking M-Su 3am-6am" (with time)
            # "No Parking M-F 8am-6pm except permit" (with RPP exception)
            parts = ['No Parking']
            if display_days:
                parts.append(display_days)
            if time_range:
                parts.append(time_range)
            
            # Add exception suffix if present
            if exception_suffix:
                parts.append(exception_suffix)
            
            return ' '.join(parts)
        
        elif rule_type == 'oversized-vehicle':
            # "No oversized vehicles" (informational only)
            return "No oversized vehicles"
        
        elif rule_type == 'tow-away':
            # "Tow-Away Zone Mon-Fri 8am-6pm"
            parts = ['Tow-Away Zone']
            if display_days:
                parts.append(display_days)
            if time_range:
                parts.append(time_range)
            return ' '.join(parts)
        
        else:
            # Fallback: use regulation text or generic
            return rule.get('regulation', 'Parking Regulation')
    
    @classmethod
    def _get_exception_suffix(cls, rule: Dict[str, Any]) -> str:
        """
        Determine standardized exception suffix for a rule.
        
        Standardized Suffixes (Dec 31, 2024):
        - RPP Exception: "except permit" (lowercase)
        - Government Permit: "except government permit" (lowercase)
        
        Returns:
            Exception suffix string or empty string
        """
        regulation = str(rule.get('regulation', '')).lower()
        exceptions = str(rule.get('exceptions', '')).lower()
        details = str(rule.get('regdetails', '')).lower()
        
        # Check for government permit special case
        if 'government' in regulation or 'government permit' in exceptions:
            return "except government permit"
        
        # Check for RPP areas
        has_rpp = bool(
            rule.get('permitArea') or
            rule.get('rpparea1') or
            rule.get('rpparea2') or
            rule.get('rpparea3')
        )
        
        # Check exception text for RPP
        has_rpp_exception = (
            'rpp holders are exempt' in exceptions or
            'permit' in exceptions or
            'permit' in details
        )
        
        # Return standardized suffix
        if has_rpp or has_rpp_exception:
            return "except permit"
        
        return ""
    
    @classmethod
    def sort_rules_for_display(cls, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort rules for modal display.
        
        Sorting Order:
        1. Monday-first (rules with Monday before others) - PRIMARY
        2. Frequency tier (most common first) - SECONDARY
        3. Alphabetical by type (for consistency) - TERTIARY
        
        Rationale: Rules affecting Monday (start of work week) are most relevant
        to users planning their week, regardless of rule type.
        
        Args:
            rules: List of rule dicts
        
        Returns:
            Sorted list (Monday rules first, then by frequency)
        """
        def get_sort_key(rule: Dict[str, Any]) -> Tuple[int, int, str]:
            rule_type = rule.get('type', 'parking-regulation')
            active_days = rule.get('activeDays', [])
            
            # Primary sort: Monday-first (0 if has Monday, 1 if not)
            has_monday = 0 if 0 in active_days else 1  # 0 = Monday in canonical format
            
            # Secondary sort: Frequency tier (lower = more common)
            frequency_tier = cls.RULE_FREQUENCY_ORDER.get(rule_type, 99)
            
            # Tertiary sort: Type name (for consistency)
            type_name = rule_type
            
            return (has_monday, frequency_tier, type_name)
        
        return sorted(rules, key=get_sort_key)
    
    @classmethod
    def calculate_next_restriction(cls, 
                                   rules: List[Dict[str, Any]], 
                                   current_datetime: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Calculate next upcoming absolute prohibition (restriction that prevents parking).
        
        Only considers:
        - Street sweeping
        - Tow-away zones
        - No parking zones
        - Meter TOW schedules (if implemented)
        
        Does NOT consider:
        - Time limits (you can still park, just with a limit)
        - RPP zones (you can park with permit)
        - Metered parking (you can park if you pay)
        
        Args:
            rules: List of rule dicts with canonical day/time fields
            current_datetime: Current time (defaults to now)
        
        Returns:
            {
                'type': 'street-sweeping',
                'datetime_iso': '2025-01-02T00:00:00',
                'display': 'Thu 12:00AM',
                'description': 'Street Cleaning',
                'days_until': 2
            }
            or None if no upcoming restrictions
        """
        if not rules:
            return None
        
        if current_datetime is None:
            current_datetime = datetime.now()
        
        # Filter to only absolute prohibitions
        restriction_types = {'street-sweeping', 'tow-away', 'no-parking'}
        restrictions = [r for r in rules if r.get('type') in restriction_types]
        
        if not restrictions:
            return None
        
        # Find next occurrence for each restriction
        upcoming = []
        
        for rule in restrictions:
            active_days = rule.get('activeDays', [])
            start_time_min = rule.get('startTimeMin')
            
            if not active_days or start_time_min is None:
                continue
            
            # Find next occurrence
            current_weekday = current_datetime.weekday()  # 0=Monday, 6=Sunday
            current_time_min = current_datetime.hour * 60 + current_datetime.minute
            
            # Check each active day
            for day in active_days:
                # Calculate days until this day
                days_until = (day - current_weekday) % 7
                
                # If it's today, check if time has passed
                if days_until == 0 and current_time_min >= start_time_min:
                    days_until = 7  # Next week
                
                # Calculate actual datetime
                next_date = current_datetime + timedelta(days=days_until)
                next_datetime = next_date.replace(
                    hour=start_time_min // 60,
                    minute=start_time_min % 60,
                    second=0,
                    microsecond=0
                )
                
                upcoming.append({
                    'rule': rule,
                    'datetime': next_datetime,
                    'days_until': days_until
                })
        
        if not upcoming:
            return None
        
        # Sort by datetime and get earliest
        upcoming.sort(key=lambda x: x['datetime'])
        next_restriction = upcoming[0]
        
        # Format display using 1-2 letter day format
        next_dt = next_restriction['datetime']
        day_names = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']
        day_name = day_names[next_dt.weekday()]
        
        # Format time in simplified format (12am not 12:00AM)
        hour = next_dt.hour
        minute = next_dt.minute
        period = 'am' if hour < 12 else 'pm'
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        
        # Only show minutes if not on the hour
        if minute == 0:
            time_str = f"{hour_12}{period}"
        else:
            time_str = f"{hour_12}:{minute:02d}{period}"
        
        # Display format: "Th 12am" (no description needed - clear from rules)
        display = f"{day_name} {time_str}"
        
        return {
            'type': next_restriction['rule'].get('type'),
            'datetime_iso': next_dt.isoformat(),
            'display': display,
            'days_until': next_restriction['days_until']
        }
    
    @classmethod
    def format_segment_for_modal(cls, 
                                 segment: Dict[str, Any],
                                 current_datetime: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Format complete segment data for modal display.
        
        Generates ALL text content for modal body:
        - Location header text
        - Cross streets text
        - Sorted rules with display text
        - Next restriction (if applicable)
        
        Frontend owns:
        - Banner (green/red with emoji)
        - Design/layout/spacing/fonts
        - Report Error button
        - Get Directions button
        
        Args:
            segment: Complete segment dict with rules
            current_datetime: Current time for next restriction calc
        
        Returns:
            {
                'location_text': '19TH ST (North, 2700-2798)',
                'cross_streets_text': 'York St → Bryant St',
                'rules': [
                    {
                        'display_text': 'Street Cleaning 12am-6am Thu',
                        'type': 'street-sweeping',
                        'is_absolute_prohibition': True
                    },
                    ...
                ],
                'next_restriction': {
                    'display': 'Thu 12:00AM',
                    'description': 'Street Cleaning'
                } or None
            }
        """
        # 1. Format location header
        street_name = segment.get('streetName', 'Unknown Street')
        cardinal = segment.get('cardinalDirection', segment.get('side', ''))
        from_addr = segment.get('fromAddress', '')
        to_addr = segment.get('toAddress', '')
        
        if from_addr and to_addr:
            location_text = f"{street_name} ({cardinal}, {from_addr}-{to_addr})"
        else:
            location_text = f"{street_name} ({cardinal})"
        
        # 2. Format cross streets
        from_street = segment.get('fromStreet')
        to_street = segment.get('toStreet')
        
        if from_street and to_street:
            cross_streets_text = f"{from_street} → {to_street}"
        elif from_street or to_street:
            cross_streets_text = from_street or to_street
        else:
            cross_streets_text = None
        
        # 3. Format and sort rules
        rules = segment.get('rules', [])
        sorted_rules = cls.sort_rules_for_display(rules)
        
        formatted_rules = []
        for rule in sorted_rules:
            display_text = cls.format_rule_display_text(rule)
            
            # Skip if display_text is None (e.g., standalone RPP zones)
            if display_text is None:
                continue
            
            is_prohibition = rule.get('type') in {'street-sweeping', 'tow-away', 'no-parking'}
            
            formatted_rules.append({
                'display_text': display_text,
                'type': rule.get('type'),
                'is_absolute_prohibition': is_prohibition
            })
        
        # 4. Calculate next restriction
        next_restriction = cls.calculate_next_restriction(rules, current_datetime)
        
        return {
            'location_text': location_text,
            'cross_streets_text': cross_streets_text,
            'rules': formatted_rules,
            'next_restriction': next_restriction
        }


# ============================================================================
# CONVENIENCE FUNCTIONS FOR RULE DISPLAY
# ============================================================================

def format_rule_for_modal(rule: Dict[str, Any]) -> str:
    """
    Convenience function to format a single rule for modal display.
    
    Example:
        format_rule_for_modal(rule) → "Street Cleaning 12am-6am Thu"
    """
    return RuleDisplayFormatter.format_rule_display_text(rule)


def sort_rules_for_modal(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to sort rules for modal display.
    
    Sorting:
    1. Frequency (most common first)
    2. Monday-first (within same frequency)
    """
    return RuleDisplayFormatter.sort_rules_for_display(rules)


def calculate_next_restriction(rules: List[Dict[str, Any]], 
                               current_datetime: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to calculate next upcoming restriction.
    
    Returns:
        {
            'display': 'Thu 12:00AM',
            'description': 'Street Cleaning',
            'days_until': 2
        }
        or None
    """
    return RuleDisplayFormatter.calculate_next_restriction(rules, current_datetime)


def format_segment_for_modal(segment: Dict[str, Any],
                             current_datetime: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Convenience function to format complete segment for modal.
    
    Returns all text content for modal body:
    - location_text
    - cross_streets_text
    - rules (sorted with display_text)
    - next_restriction
    """
    return RuleDisplayFormatter.format_segment_for_modal(segment, current_datetime)