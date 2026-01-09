# Street Cleaning Dataset Analysis Guide

## Overview

This guide explains how to analyze the street cleaning dataset (yhqp-riqs) to answer critical questions about data quality and implementation requirements.

## Analysis Scripts Created

### 1. `analyze_street_cleaning_dataset.py`
**Purpose**: Comprehensive analysis of the yhqp-riqs dataset

**What it does**:
- Counts streets with missing opposite-side cleaning data
- Analyzes field completeness (which fields exist and how complete they are)
- Generates manual verification list for streets needing physical verification
- Creates comprehensive JSON report

**Outputs**:
- `street_cleaning_manual_verification.csv` - List of streets to verify physically
- `street_cleaning_analysis_report.json` - Complete analysis results

**Run it**:
```bash
cd backend
python analyze_street_cleaning_dataset.py
```

### 2. `analyze_week_of_month_patterns.py`
**Purpose**: Determine if FullName field contains week-of-month info or if we need week1-5 binary fields

**What it does**:
- Compares text field content (FullName, corridor, etc.) with week1-5 binary fields
- Tests if we can parse "2nd Thursday" from text
- Calculates success rate of text parsing vs binary fields
- Provides implementation recommendation

**Outputs**:
- `week_of_month_analysis.json` - Detailed analysis results
- Console recommendation on which approach to use

**Run it**:
```bash
cd backend
python analyze_week_of_month_patterns.py
```

## Questions Answered

### Q1: How many streets have missing opposite-side cleaning data?

**Answer from**: `analyze_street_cleaning_dataset.py`

The script will output:
```
CNNs with ONLY ONE side: [NUMBER]
```

This is the count of streets that need manual verification. The script generates a CSV file with all these streets for you to physically verify.

### Q2: Can FullName field identify 2nd/4th week schedules?

**Answer from**: `analyze_week_of_month_patterns.py`

The script will provide a recommendation:
- **If text parsing success rate ≥ 95%**: Use text parsing with binary fallback
- **If text parsing success rate 70-95%**: Prefer binary fields, use text as validation
- **If text parsing success rate < 70%**: MUST use week1-5 binary fields

## Implementation Recommendations

### For Street Cleaning Display

Based on your requirements, implement these display formats:

#### With Holiday Suspension (holidays = 0)
```
"Street Cleaning M, W, F 8am-10am except holidays"
```

#### Without Holiday Suspension (holidays = 1 or NULL)
```
"Street Cleaning M, W, F 8am-10am"
```

#### With Week-of-Month (if week fields indicate specific weeks)
```
"Street Cleaning 2nd & 4th Thu 8am-10am except holidays"
```

### For Meter Holiday Override

Create special handling for SF holidays:
- **January 1** (New Year's Day)
- **December 25** (Christmas Day)
- **4th Thursday of November** (Thanksgiving)

On these days:
- Meters are FREE (unless meter schedule indicates otherwise)
- Street cleaning does NOT occur (if holidays = 0)

## Manual Verification Workflow

1. **Run Analysis Script**:
   ```bash
   python analyze_street_cleaning_dataset.py
   ```

2. **Open CSV File**:
   - File: `street_cleaning_manual_verification.csv`
   - Contains all streets with missing opposite-side data

3. **Physical Verification**:
   - For each street, physically check if opposite side has cleaning signs
   - Fill in columns:
     - `Verification_Status`: CONFIRMED_MISSING / HAS_CLEANING / UNKNOWN
     - `Opposite_Side_Schedule`: If HAS_CLEANING, note the schedule
     - `Notes`: Any additional observations

4. **Create Manual Overrides**:
   - For streets with `HAS_CLEANING` status, create entries in `manual_data_overrides.json`
   - Use the schedule information you collected

## Implementation in ingest_data_cnn_segments.py

### Current Status
⏭️ Street cleaning integration pending (will be STEP 5.7)

### Planned Implementation

Add to the ingestion pipeline:

```python
def match_street_cleaning(all_entries, cleaning_df):
    """Enhanced with week-of-month and holiday support"""
    matched_count = 0
    
    # Build CNN+side index
    cnn_index = {}
    for entry in all_entries:
        key = f"{entry.get('cnn')}_{entry.get('side')}"
        cnn_index[key] = entry
    
    for idx, row in cleaning_df.iterrows():
        cnn = row.get("cnn")
        side = row.get("cnnrightleft")
        
        if not cnn or not side:
            continue
        
        # Direct lookup
        key = f"{cnn}_{side}"
        entry = cnn_index.get(key)
        
        if entry:
            # NEW: Extract week-of-month scheduling
            weeks_active = []
            for week_num in range(1, 6):
                field = f"week{week_num}ofmon"
                if row.get(field, "N").upper() in ["Y", "1"]:
                    weeks_active.append(week_num)
            
            # NEW: Extract holiday flag (0 = no cleaning on holidays)
            holidays_value = row.get("holidays", "1")
            skip_holidays = (str(holidays_value) == "0")
            
            # Normalize regulation
            normalized = normalize_regulation(row.to_dict(), dataset_type='street_cleaning')
            
            # Build display description
            base_desc = normalized['display']['summary']
            if skip_holidays:
                description = f"{base_desc} except holidays"
            else:
                description = base_desc
            
            entry["rules"].append({
                "type": "street-sweeping",
                "day": row.get("weekday"),
                "startTime": row.get("fromhour"),
                "endTime": row.get("tohour"),
                
                # NEW: Week-of-month and holiday fields
                "weeksOfMonth": weeks_active,  # [] = all weeks, [2,4] = 2nd & 4th
                "skipHolidays": skip_holidays,  # True if holidays = 0
                
                # Pre-computed fields from normalizer
                "activeDays": normalized['canonical']['days'],
                "startTimeMin": normalized['canonical']['time_start'],
                "endTimeMin": normalized['canonical']['time_end'],
                "description": description,  # Includes "except holidays" if needed
                "displayDays": normalized['display']['days'],
                "displayTime": normalized['display']['time'],
                
                # Metadata
                "corridor": row.get("corridor"),
                "limits": row.get("limits"),
                "blockside": row.get("blockside"),
                "side": side
            })
            matched_count += 1
    
    return matched_count
```

## Next Steps

1. ✅ Run both analysis scripts
2. ✅ Review the generated reports
3. ✅ Complete manual verification CSV
4. ⏭️ Implement enhancements in ingest_data_cnn_segments.py (STEP 5.7)
5. ✅ Create manual overrides for confirmed missing data
6. ⏭️ Test the enhanced implementation

## Files Generated

After running the scripts, you'll have:
- `street_cleaning_manual_verification.csv` - For manual verification
- `street_cleaning_analysis_report.json` - Complete analysis
- `week_of_month_analysis.json` - Week-of-month field analysis

## Questions?

If you need to modify the analysis or add additional checks, both scripts are well-commented and easy to extend.