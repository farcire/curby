# Street Cleaning Integration Guide

**Last Updated**: December 31, 2024  
**Dataset**: Street Cleaning Schedules (`yhqp-riqs`)  
**Status**: Ready for Integration

---

## Overview

This guide documents the complete integration of street cleaning data into the CNN Master dataset, including field structure, display formatting, and handling of edge cases.

## Key Decisions

✅ **Missing Data Handling**: Display only the side we have data for (current behavior)  
✅ **Week-of-Month Format**: "2nd & 4th Thu" (ordinal numbers)  
✅ **Holiday Display**: Show "except holidays" when holidays=0, don't show otherwise  
✅ **Integration Timing**: Integrate now with known gaps, document incompleteness  
✅ **SFMTA Reporting**: Log in data issues documentation for future comprehensive report

---

## Dataset Structure

### Unique Identifier
**CNN + corridor_side** (e.g., "6113000_L", "6113000_R")

### Key Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `cnn` | String | Centerline Network ID | "6113000" |
| `corridor_side` | String | L (Left) or R (Right) | "L" |
| `fullname` | String | Day name or "HOLIDAY" | "Monday", "HOLIDAY" |
| `weekday` | String | Day abbreviation | "Mon", "Holiday" |
| `fromhour` | Integer | Start hour (0-23) | 6 |
| `tohour` | Integer | End hour (0-23) | 8 |
| `week1` | String | 1st week active (1/0) | "1" |
| `week2` | String | 2nd week active (1/0) | "1" |
| `week3` | String | 3rd week active (1/0) | "0" |
| `week4` | String | 4th week active (1/0) | "1" |
| `week5` | String | 5th week active (1/0) | "0" |
| `holidays` | String | Clean on holidays (1/0) | "0" |

### Week-of-Month Patterns

**100% of records** use week-of-month scheduling:
- **All weeks (1st-5th)**: 62.8%
- **2nd & 4th only**: 18.4%
- **1st & 3rd only**: 11.6%
- **1st, 3rd, 5th**: 5.9%

### Holiday Field

**92.7% of records** have `holidays=0` (no cleaning on SF's 3 holidays):
- January 1 (New Year's Day)
- December 25 (Christmas Day)
- 4th Thursday of November (Thanksgiving)

---

## Holiday Override Pattern

### The HOLIDAY Entry Mechanism

SFMTA uses a special `FullName="HOLIDAY"` entry to control holiday cleaning behavior.

**Pattern 1: HOLIDAY Override (holidays=0)**
1. CNN+side has one or more days with `holidays=1` (cleaning on holidays)
2. Same CNN+side has `HOLIDAY` entry with `holidays=0` (no cleaning on holidays)
3. **Result**: HOLIDAY entry **overrides** all holidays=1 → NO cleaning on holidays
4. **Display**: Show "except holidays" suffix

**Pattern 2: HOLIDAY Confirmation (holidays=1)**
1. CNN+side has `HOLIDAY` entry with `holidays=1` (cleaning on holidays)
2. **Result**: Cleaning DOES occur on holidays
3. **Display**: Do NOT show "except holidays" suffix

**Hypothesis to Verify**: Pattern 1 (HOLIDAY with holidays=0) ALWAYS has at least one other entry with holidays=1 for the same CNN+side. This confirms that HOLIDAY entries are specifically used to override or confirm holiday behavior.

### Example 1: CNN 6113000R (HOLIDAY Override)

**Raw Data**:
```
CNN 6113000, Side R:
- Monday:    holidays=1  (would clean on holidays)
- HOLIDAY:   holidays=0  (overrides Monday - NO cleaning on holidays)
- Wednesday: holidays=0
- Friday:    holidays=0
- Saturday:  holidays=0
```

**Display**: "Street Cleaning M, W, F, Sa 6am-8am except holidays"

**Note**: Even though Monday has holidays=1, the HOLIDAY entry overrides it.

### Example 2: HOLIDAY Confirmation (holidays=1)

**Raw Data**:
```
CNN XXXXX, Side L:
- Tuesday:  holidays=1  (cleaning on holidays)
- HOLIDAY:  holidays=1  (confirms cleaning on holidays)
```

**Display**: "Street Cleaning Tu 8am-10am"

**Note**: No "except holidays" suffix because HOLIDAY entry has holidays=1.

### Implementation Logic

```python
def should_skip_holidays(cnn_side_records):
    """
    Determine if 'except holidays' should be shown.
    
    The HOLIDAY entry is only special when it CONTRADICTS a day's holidays=1.
    - If day holidays=1 AND HOLIDAY holidays=0 → Override to "except holidays"
    - Otherwise → Use consistent holidays value
    - If NO HOLIDAY entry → Use day's holidays field directly
    """
    # Check for override case: HOLIDAY=0 contradicting days=1
    has_override = any(
        r.get("fullname") == "HOLIDAY" and str(r.get("holidays")) == "0"
        for r in cnn_side_records
    )
    has_days_with_1 = any(
        r.get("fullname") != "HOLIDAY" and str(r.get("holidays")) == "1"
        for r in cnn_side_records
    )
    
    if has_override and has_days_with_1:
        return True  # Override case: HOLIDAY=0 overrides days=1
    
    # Otherwise use day's holidays field (consistent)
    regular_days = [r for r in cnn_side_records if r.get("fullname") != "HOLIDAY"]
    if regular_days:
        # Use first day's holidays value (all should be consistent)
        return str(regular_days[0].get("holidays")) == "0"
    
    return True  # Default to showing "except holidays"
```

---

## Display Format Specification

### Format Template

```
Street Cleaning {days} {time_range} {holiday_clause}
```

### Components

#### 1. Days Format

**Single Day**: "M", "Tu", "W", "Th", "F", "Sa", "Su"

**Multiple Days**: Comma-separated, no "and"
- "M, W, F"
- "Tu, Th"
- "M, Tu, W, Th, F, Sa"

**Day Abbreviations**:
```python
DAY_ABBREV = {
    "Monday": "M",
    "Tuesday": "Tu",
    "Wednesday": "W",
    "Thursday": "Th",
    "Friday": "F",
    "Saturday": "Sa",
    "Sunday": "Su"
}
```

#### 2. Time Range Format

**Format**: "{from_hour}am-{to_hour}am" or "{from_hour}pm-{to_hour}pm"

**Examples**:
- "6am-8am"
- "8am-10am"
- "12pm-2pm"

**Conversion Logic**:
```python
def format_time(hour):
    """Convert 24-hour to 12-hour format."""
    if hour == 0:
        return "12am"
    elif hour < 12:
        return f"{hour}am"
    elif hour == 12:
        return "12pm"
    else:
        return f"{hour-12}pm"

time_range = f"{format_time(from_hour)}-{format_time(to_hour)}"
```

#### 3. Holiday Clause

**When to show**: `holidays=0` OR HOLIDAY override exists

**Format**: " except holidays" (note the leading space)

**Do NOT use**: parentheses, "on holidays", or other variations

---

## Week-of-Month Display

### Ordinal Number Format

**Use ordinal numbers**: "1st", "2nd", "3rd", "4th", "5th"

**Examples**:
- "2nd & 4th Thu" (not "Week 2 & 4 Thu")
- "1st, 3rd, 5th Mon" (not "Week 1, 3, 5 Mon")
- "Every Thu" (when all 5 weeks active)

### Implementation

```python
def format_weeks(week1, week2, week3, week4, week5):
    """Format week-of-month display."""
    weeks_active = []
    week_values = [week1, week2, week3, week4, week5]
    
    for i, val in enumerate(week_values, start=1):
        if str(val) == "1":
            weeks_active.append(i)
    
    # If all 5 weeks, show "Every"
    if len(weeks_active) == 5:
        return "Every"
    
    # Convert to ordinals
    ordinals = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}
    week_strs = [ordinals[w] for w in weeks_active]
    
    # Join with & for 2 items, commas for 3+
    if len(week_strs) == 1:
        return week_strs[0]
    elif len(week_strs) == 2:
        return f"{week_strs[0]} & {week_strs[1]}"
    else:
        return ", ".join(week_strs[:-1]) + f", {week_strs[-1]}"
```

### Display Examples

| Weeks Active | Display |
|--------------|---------|
| 1,2,3,4,5 | "Every Thu 8am-10am except holidays" |
| 2,4 | "2nd & 4th Thu 8am-10am except holidays" |
| 1,3 | "1st & 3rd Mon 6am-8am except holidays" |
| 1,3,5 | "1st, 3rd, 5th Fri 12pm-2pm except holidays" |
| 2 | "2nd Wed 8am-10am except holidays" |

---

## Complete Examples

### Example 1: CNN 6113000L (South Side)

**Raw Data**:
```
CNN: 6113000, Side: L
Records:
- Tuesday:  6am-8am, weeks 1-5, holidays=0
- Thursday: 6am-8am, weeks 1-5, holidays=0
- Sunday:   6am-8am, weeks 1-5, holidays=0
```

**Display**: "Street Cleaning Tu, Th, Su 6am-8am except holidays"

### Example 2: CNN 6113000R (North Side with HOLIDAY Override)

**Raw Data**:
```
CNN: 6113000, Side: R
Records:
- Monday:    6am-8am, weeks 1-5, holidays=1
- HOLIDAY:   6am-8am, weeks 1-5, holidays=0  ← OVERRIDE
- Wednesday: 6am-8am, weeks 1-5, holidays=0
- Friday:    6am-8am, weeks 1-5, holidays=0
- Saturday:  6am-8am, weeks 1-5, holidays=0
```

**Display**: "Street Cleaning M, W, F, Sa 6am-8am except holidays"

**Note**: Even though Monday has holidays=1, the HOLIDAY entry overrides it.

### Example 3: Typical 2nd & 4th Pattern

**Raw Data**:
```
CNN: 123000, Side: L
Records:
- Thursday: 8am-10am, weeks 2,4, holidays=0
```

**Display**: "Street Cleaning 2nd & 4th Thu 8am-10am except holidays"

### Example 4: All Weeks Pattern

**Raw Data**:
```
CNN: 456000, Side: R
Records:
- Monday: 6am-8am, weeks 1-5, holidays=0
```

**Display**: "Street Cleaning Every Mon 6am-8am except holidays"

---

## Data Quality Issues

### Asymmetric Coverage

**Issue**: 15.8% of CNNs (1,933 out of 12,253) have cleaning on only ONE side

**Impact**: Users won't see restrictions for missing side

**Solution**: Display only the side we have data for

**Documentation**: See Issue #1 in [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md)

**Verification List**: `street_cleaning_manual_verification.csv`

### Missing Opposite Side Example

**CNN 961000** (19th Street):
- **L side (South)**: Friday 12am-6am ✅
- **R side (North)**: Missing ❌ (should be Thursday 12am-6am)

**Current Behavior**: Show only South side cleaning

**Future**: Manual verification and override system

---

## Integration Steps

### Step 1: Extract Week-of-Month Fields

```python
def extract_weeks_active(record):
    """Extract which weeks are active."""
    weeks_active = []
    for week_num in range(1, 6):
        field = f"week{week_num}"
        if str(record.get(field, '0')) == '1':
            weeks_active.append(week_num)
    return weeks_active
```

### Step 2: Check for HOLIDAY Override

```python
def check_holiday_override(cnn, side, all_records):
    """Check if CNN+side has HOLIDAY override."""
    cnn_side_records = [
        r for r in all_records 
        if r.get("cnn") == cnn and r.get("corridor_side") == side
    ]
    
    return any(
        r.get("fullname") == "HOLIDAY" and str(r.get("holidays")) == "0"
        for r in cnn_side_records
    )
```

### Step 3: Group and Format Display

```python
def format_street_cleaning_display(cnn, side, records):
    """Format street cleaning display for CNN+side."""
    # Filter records for this CNN+side (exclude HOLIDAY entries from display)
    day_records = [
        r for r in records 
        if r.get("cnn") == cnn 
        and r.get("corridor_side") == side
        and r.get("fullname") != "HOLIDAY"
    ]
    
    if not day_records:
        return None
    
    # Check for HOLIDAY override
    has_override = check_holiday_override(cnn, side, records)
    
    # Group by time range (assuming same time for all days)
    from_hour = day_records[0].get("fromhour")
    to_hour = day_records[0].get("tohour")
    
    # Extract days
    days = []
    for record in day_records:
        day_abbrev = DAY_ABBREV.get(record.get("fullname"), "")
        if day_abbrev:
            days.append(day_abbrev)
    
    # Sort days (M, Tu, W, Th, F, Sa, Su)
    day_order = ["M", "Tu", "W", "Th", "F", "Sa", "Su"]
    days = sorted(days, key=lambda d: day_order.index(d))
    
    # Format time range
    time_range = f"{format_time(from_hour)}-{format_time(to_hour)}"
    
    # Add holiday clause
    holiday_clause = " except holidays" if has_override or str(day_records[0].get("holidays")) == "0" else ""
    
    # Build display string
    days_str = ", ".join(days)
    return f"Street Cleaning {days_str} {time_range}{holiday_clause}"
```

### Step 4: Integrate into MongoDB Collection

```python
# In ingest_data_cnn_segments.py (STEP 5.7)
def add_street_cleaning_to_segments(all_entries, cleaning_df):
    """Add street cleaning to MongoDB street_segments collection."""
    for entry in all_entries:
        cnn = entry["cnn"]
        side = entry["side"]
        
        # Get street cleaning display
        display = format_street_cleaning_display(cnn, side, cleaning_df)
        
        if display:
            entry["streetCleaning"] = {
                "display": display,
                "source": "yhqp-riqs",
                "lastUpdated": datetime.now().isoformat()
            }
```

---

## Testing

### Test Cases

1. **Standard 2nd & 4th Pattern**
   - Input: CNN with week2=1, week4=1, holidays=0
   - Expected: "Street Cleaning 2nd & 4th Thu 8am-10am except holidays"

2. **HOLIDAY Override Pattern**
   - Input: CNN with Monday holidays=1 + HOLIDAY holidays=0
   - Expected: "Street Cleaning M, W, F, Sa 6am-8am except holidays"

3. **All Weeks Pattern**
   - Input: CNN with all weeks 1-5 active
   - Expected: "Street Cleaning Every Mon 6am-8am except holidays"

4. **Asymmetric Coverage**
   - Input: CNN with only L side data
   - Expected: Display only L side, R side shows no cleaning data

### Verification Script

Run [`verify_holiday_pattern.py`](verify_holiday_pattern.py) to verify:
- HOLIDAY override pattern frequency
- Consistency across dataset
- CNN 6113000 specific case

---

## References

- **Dataset**: [Street Cleaning Schedules (yhqp-riqs)](https://data.sfgov.org/City-Infrastructure/Street-Sweeping-Schedule/yhqp-riqs)
- **Analysis Scripts**:
  - [`analyze_street_cleaning_dataset.py`](analyze_street_cleaning_dataset.py)
  - [`analyze_week_fields_correct.py`](analyze_week_fields_correct.py)
  - [`verify_holiday_pattern.py`](verify_holiday_pattern.py)
- **Documentation**:
  - [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md) - Issue #1
  - [`STREET_CLEANING_ANALYSIS_GUIDE.md`](STREET_CLEANING_ANALYSIS_GUIDE.md)
- **Implementation**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 5.7 (when implemented)

---

**Last Updated**: December 31, 2024  
**Next Review**: After HOLIDAY pattern verification