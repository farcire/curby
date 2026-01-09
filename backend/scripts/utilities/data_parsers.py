"""
Data Parsers - Pure Parsing Functions
======================================

Converts raw SFMTA data formats to canonical internal formats.
NO business logic, NO display formatting, NO aggregation.
Just pure data transformation.

Canonical Formats:
- Days: Array of integers [0-6] where 0=Monday, 6=Sunday
- Times: Integer minutes from midnight (0-1439)
- Duration: Integer minutes

Usage:
    from data_parsers import parse_days, parse_time, parse_duration
    
    days = parse_days("MON-FRI")  # → [0,1,2,3,4]
    time = parse_time("9:00 AM")  # → 540
    duration = parse_duration("2", unit_hint="hours")  # → 120
"""

from typing import Optional, List, Any
import re


# ============================================================================
# DAY PARSING
# ============================================================================

class DayParser:
    """Parse ANY day format from SFMTA datasets to canonical [0-6] array."""
    
    DAY_ABBREVIATIONS = {
        'M': 0, 'MO': 0, 'MON': 0, 'MONDAY': 0,
        'TU': 1, 'TUE': 1, 'TUES': 1, 'TUESDAY': 1,
        'W': 2, 'WE': 2, 'WED': 2, 'WEDNESDAY': 2,
        'TH': 3, 'THU': 3, 'THUR': 3, 'THURS': 3, 'THURSDAY': 3,
        'F': 4, 'FR': 4, 'FRI': 4, 'FRIDAY': 4,
        'SA': 5, 'SAT': 5, 'SATURDAY': 5,
        'SU': 6, 'SUN': 6, 'SUNDAY': 6
    }
    
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
        
        Examples:
            "DAILY" → [0,1,2,3,4,5,6]
            "MON-FRI" → [0,1,2,3,4]
            "Th" → [3]
            "Mon,Wed,Fri" → [0,2,4]
        """
        if not day_input or not isinstance(day_input, str):
            return []
        
        day_str = str(day_input).strip().upper()
        
        if not day_str or day_str in ('NAN', 'NONE', 'NULL', ''):
            return []
        
        # Pattern matching
        if day_str in cls.EVERY_DAY_PATTERNS:
            return [0, 1, 2, 3, 4, 5, 6]
        if day_str in cls.WEEKDAY_PATTERNS:
            return [0, 1, 2, 3, 4]
        if day_str in cls.WEEKEND_PATTERNS:
            return [5, 6]
        if day_str in cls.SCHOOL_DAY_PATTERNS:
            return [0, 1, 2, 3, 4]
        
        # Range parsing
        for separator in ['-', ' THRU ', ' THROUGH ', ' TO ']:
            if separator in day_str:
                return cls._parse_range(day_str, separator)
        
        # List parsing
        if any(sep in day_str for sep in [',', '&', '/', ';']):
            return cls._parse_list(day_str)
        
        # Single day
        return cls._parse_single(day_str)
    
    @classmethod
    def _parse_range(cls, day_str: str, separator: str) -> List[int]:
        parts = day_str.split(separator)
        if len(parts) != 2:
            return []
        
        start_day = cls._get_day_value(parts[0].strip())
        end_day = cls._get_day_value(parts[1].strip())
        
        if start_day is None or end_day is None:
            return []
        
        if start_day <= end_day:
            return list(range(start_day, end_day + 1))
        else:
            return list(range(start_day, 7)) + list(range(0, end_day + 1))
    
    @classmethod
    def _parse_list(cls, day_str: str) -> List[int]:
        parts = re.split(r'[,&/;]', day_str)
        result = set()
        
        for part in parts:
            day_val = cls._get_day_value(part.strip())
            if day_val is not None:
                result.add(day_val)
        
        return sorted(list(result))
    
    @classmethod
    def _parse_single(cls, day_str: str) -> List[int]:
        day_val = cls._get_day_value(day_str)
        return [day_val] if day_val is not None else []
    
    @classmethod
    def _get_day_value(cls, day_str: str) -> Optional[int]:
        clean_str = day_str.strip().upper()
        
        if clean_str in cls.DAY_ABBREVIATIONS:
            return cls.DAY_ABBREVIATIONS[clean_str]
        
        for abbrev, value in cls.DAY_ABBREVIATIONS.items():
            if clean_str.startswith(abbrev):
                return value
        
        return None


# ============================================================================
# TIME PARSING
# ============================================================================

class TimeParser:
    """Parse ANY time format from SFMTA datasets to minutes from midnight."""
    
    @classmethod
    def parse(cls, time_input: Any) -> Optional[int]:
        """
        Parse any time format to minutes from midnight (0-1439).
        
        Examples:
            "9" → 540 (9:00 AM)
            "1800" → 1080 (6:00 PM)
            "9:00 AM" → 540
            "6:00 PM" → 1080
        """
        if not time_input:
            return None
        
        try:
            time_str = str(time_input).strip().upper()
        except:
            return None
        
        if not time_str or time_str in ('NAN', 'NONE', 'NULL', ''):
            return None
        
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
        if 'AM' not in time_str and 'PM' not in time_str:
            return None
        
        try:
            is_pm = 'PM' in time_str
            is_am = 'AM' in time_str
            
            clean_str = re.sub(r'[^\d:]', '', time_str)
            
            if ':' in clean_str:
                parts = clean_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
            else:
                hours = int(clean_str)
                minutes = 0
            
            if is_pm and hours < 12:
                hours += 12
            elif is_am and hours == 12:
                hours = 0
            
            return hours * 60 + minutes
        except:
            return None
    
    @classmethod
    def _parse_24hour_colon(cls, time_str: str) -> Optional[int]:
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
        clean_str = re.sub(r'[^\d]', '', time_str)
        
        if not clean_str:
            return None
        
        try:
            val = int(clean_str)
            
            if 0 <= val < 24:
                return val * 60
        except:
            pass
        
        return None
    
    @classmethod
    def _parse_iso_time(cls, time_str: str) -> Optional[int]:
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
# DURATION PARSING
# ============================================================================

class DurationParser:
    """Parse ANY duration/time limit format to integer minutes."""
    
    @classmethod
    def parse(cls, value: Any, unit_hint: str = None) -> Optional[int]:
        """
        Parse any duration format to integer minutes.
        
        Args:
            value: Duration value (string, int, float)
            unit_hint: 'hours' or 'minutes' if known from dataset
        
        Returns:
            Integer minutes, or None if no limit
        
        Examples:
            parse("2", "hours") → 120
            parse("120", "minutes") → 120
            parse(2.5, "hours") → 150
            parse("0") → None (no limit)
        """
        if not value or value in (0, "0", "0.0"):
            return None
        
        try:
            num_value = float(value)
            
            if num_value == 0:
                return None
            
            if unit_hint == "hours":
                return int(num_value * 60)
            elif unit_hint == "minutes":
                return int(num_value)
            else:
                # Auto-detect: if value > 24, assume minutes
                if num_value > 24:
                    return int(num_value)
                else:
                    return int(num_value * 60)
        except (ValueError, TypeError):
            return None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def parse_days(day_input: Any) -> List[int]:
    """Parse days to canonical [0-6] array."""
    return DayParser.parse(day_input)


def parse_time(time_input: Any) -> Optional[int]:
    """Parse time to minutes from midnight."""
    return TimeParser.parse(time_input)


def parse_duration(value: Any, unit_hint: str = None) -> Optional[int]:
    """Parse duration to integer minutes."""
    return DurationParser.parse(value, unit_hint)