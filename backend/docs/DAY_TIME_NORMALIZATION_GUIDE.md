# Day and Time Normalization Guide

**Last Updated:** December 31, 2024  
**Module:** `regulation_normalizer.py`  
**Status:** ✅ IMPLEMENTED

## Overview

All day and time parsing and formatting logic is centralized in the `regulation_normalizer.py` module. This is the **single source of truth** for temporal data normalization across the entire application.

## Architecture

### Core Principle

**Parse Once, Use Everywhere**: All temporal data is normalized at ingestion time and stored in both canonical (machine-readable) and display (human-readable) formats.

### Module Location

```
backend/regulation_normalizer.py
```

### Key Functions

```python
from regulation_normalizer import (
    normalize_regulation,    # Main normalization function
    parse_days,             # Parse day strings to [0-6] array
    parse_time_to_minutes,  # Parse time strings to minutes
    format_day_display,     # Format days for display
    format_time_12hour      # Format time in 12-hour format
)
```

## Dataset-Specific Day Formats

### Street Cleaning Schedules (`yhqp-riqs`)

**Field:** `weekday`  
**Examples:**
- `"Th"` → Thursday
- `"Mon"` → Monday
- `"TUES"` → Tuesday
- `"Friday"` → Friday

**Usage:**
```python
normalized = normalize_regulation(row.to_dict(), dataset_type='street_cleaning')
```

### Parking Regulations (`hi6h-neyh`)

**Field:** `days`  
**Examples:**
- `"MON-FRI"` → Monday through Friday
- `"DAILY"` → All 7 days
- `"Mon,Wed,Fri"` → Specific days
- `"SCHOOL DAYS"` → Monday-Friday (school context)

**Usage:**
```python
normalized = normalize_regulation(row.to_dict(), dataset_type='parking_reg')
```

### Meter Schedules (`6cqg-dxku`)

**Field:** `days_applied`  
**Examples:**
- `"Mo-Su"` → Monday through Sunday
- `"Mo-Fr"` → Monday through Friday
- `"Sa,Su"` → Saturday and Sunday

**Usage:**
```python
normalized = normalize_regulation(row.to_dict(), dataset_type='meter')
```

### Manual Overrides (`manual_data_overrides.json`)

**Field:** `weekday`  
**Examples:**
- `"Thursday"` → Full day name
- `"Monday-Friday"` → Range with full names

**Usage:**
```python
normalized = normalize_regulation(data, dataset_type='manual')
```

## Canonical Format

### Days

**Format:** Array of integers `[0-6]`  
**Convention:** Python weekday (0=Monday, 6=Sunday)

```python
{
    "canonical": {
        "days": [0, 1, 2, 3, 4],  # Monday-Friday
        "all_week": false
    }
}
```

### Time

**Format:** Integer minutes from midnight (0-1439)

```python
{
    "canonical": {
        "time_start": 480,   # 8:00 AM
        "time_end": 1080,    # 6:00 PM
        "all_day": false
    }
}
```

## Display Format

### Day Display Rules

**Smart Overrides** (in priority order):

1. **All 7 days** `[0,1,2,3,4,5,6]` → `"Daily"`
2. **Mon-Fri with "school" context** → `"School Days"`
3. **Mon-Fri (default)** → `"Weekdays"`
4. **Sat-Sun** → `"Weekends"`
5. **All other patterns** → Minimal abbreviations

### Minimal Abbreviations

Use 1-2 letters for clarity:
- Monday → **M**
- Tuesday → **Tu** (2 letters to distinguish from Thursday)
- Wednesday → **W**
- Thursday → **Th** (2 letters to distinguish from Tuesday)
- Friday → **F**
- Saturday → **Sa** (2 letters to distinguish from Sunday)
- Sunday → **Su** (2 letters to distinguish from Saturday)

### Examples

```python
[0,1,2,3,4,5,6] → "Daily"
[0,1,2,3,4]     → "Weekdays"
[5,6]           → "Weekends"
[0,2,4]         → "M, W, F"
[1,2,3]         → "Tu-Th"
[3]             → "Th"
```

### Time Display

**Format:** 12-hour with AM/PM

```python
0    → "12:00 AM"
540  → "9:00 AM"
720  → "12:00 PM"
1080 → "6:00 PM"
```

## Complete Normalization Output

```python
{
    "canonical": {
        "days": [0, 1, 2, 3, 4],
        "time_start": 480,
        "time_end": 1080,
        "all_day": false,
        "all_week": false
    },
    "display": {
        "days": "Weekdays",
        "time": "8:00 AM-6:00 PM",
        "summary": "Weekdays 8:00 AM-6:00 PM"
    },
    "raw": {
        "days": "MON-FRI",
        "time_start": "8:00 AM",
        "time_end": "6:00 PM",
        "dataset": "parking_reg"
    }
}
```

## Integration Points

### Backend Files Using Normalizer

1. **`ingest_data_cnn_segments.py`** (lines 16, 354-390, 604-631)
   - Street cleaning normalization
   - Parking regulation normalization

2. **`apply_manual_overrides.py`** (lines 9, 80-110)
   - Manual override normalization

3. **`display_utils.py`**
   - ⚠️ Day/time functions DEPRECATED
   - Only street name and address formatting remain

4. **`deterministic_parser.py`**
   - ⚠️ DEPRECATED - All functions moved to `regulation_normalizer.py`

### Frontend Integration

Frontend should use pre-computed display strings from the API:

```typescript
// Use pre-computed display strings
<span>{rule.displayDays}</span>  // "Weekdays"
<span>{rule.displayTime}</span>  // "8:00 AM-6:00 PM"

// Or full summary
<span>{rule.description}</span>  // "Weekdays 8:00 AM-6:00 PM"
```

## Migration Notes

### Old Code (DEPRECATED)

```python
# ❌ OLD - Do not use
from deterministic_parser import _parse_days, parse_time_to_minutes
from display_utils import format_restriction_description

active_days = _parse_days(row.get("days"))
start_min = parse_time_to_minutes(row.get("from_time"))
description = format_restriction_description(...)
```

### New Code (CURRENT)

```python
# ✅ NEW - Use this
from regulation_normalizer import normalize_regulation

normalized = normalize_regulation(row.to_dict(), dataset_type='parking_reg')

# Access canonical data
days = normalized['canonical']['days']
time_start = normalized['canonical']['time_start']

# Access display strings
display_days = normalized['display']['days']
display_time = normalized['display']['time']
summary = normalized['display']['summary']
```

## Benefits

1. **Single Source of Truth**: All parsing logic in one place
2. **Consistent Behavior**: Same rules across all datasets
3. **Pre-computed Display**: No runtime formatting needed
4. **Easy Maintenance**: Update logic in one file
5. **Better Testing**: Test one module comprehensively
6. **Clear Documentation**: All formats documented together

## Testing

```python
# Test day parsing
from regulation_normalizer import parse_days

assert parse_days("MON-FRI") == [0, 1, 2, 3, 4]
assert parse_days("DAILY") == [0, 1, 2, 3, 4, 5, 6]
assert parse_days("Th") == [3]

# Test time parsing
from regulation_normalizer import parse_time_to_minutes

assert parse_time_to_minutes("9:00 AM") == 540
assert parse_time_to_minutes("1800") == 1080
assert parse_time_to_minutes("6") == 360

# Test display formatting
from regulation_normalizer import format_day_display

assert format_day_display([0,1,2,3,4,5,6]) == "Daily"
assert format_day_display([0,1,2,3,4]) == "Weekdays"
assert format_day_display([0,2,4]) == "M, W, F"
```

## Future Enhancements

1. **Duration Normalization**: Add standardized duration parsing (hours/minutes)
2. **Timezone Support**: Handle timezone conversions if needed
3. **Localization**: Support multiple languages for display strings
4. **Validation**: Add input validation and error handling
5. **Performance**: Cache frequently used normalizations

## References

- Implementation: [`backend/regulation_normalizer.py`](backend/regulation_normalizer.py)
- Usage in ingestion: [`backend/ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py)
- Manual overrides: [`backend/apply_manual_overrides.py`](backend/apply_manual_overrides.py)
- Architecture: [`CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md`](../CURBY_ARCHITECTURE_ANALYSIS_Dec282025.md)