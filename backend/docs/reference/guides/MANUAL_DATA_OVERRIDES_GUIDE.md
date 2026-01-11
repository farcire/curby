# Manual Data Overrides System

## Overview

The Manual Data Overrides system allows you to augment or correct missing/incorrect data from SFMTA datasets. This is essential for handling data gaps where official datasets are incomplete or inaccurate.

## Problem Solved

SFMTA's open data has systematic gaps:
- **Missing opposite sides**: Some CNNs have street cleaning data for only L or R side
- **Incomplete coverage**: Certain street segments lack parking regulation data
- **Data quality issues**: Occasional incorrect or outdated information

When you physically verify parking regulations on-site that differ from or are missing in the official data, you can add manual overrides to ensure the application displays accurate information.

## System Components

### 1. Override Data File
**Location**: [`backend/manual_data_overrides.json`](backend/manual_data_overrides.json)

This JSON file contains all manual corrections with:
- Detailed match criteria (street name, side, address range, CNN)
- Override data (sweeping schedule, cardinal direction, times)
- Verification metadata (date, reason, verified by)

### 2. Override Application Logic
**Location**: [`backend/apply_manual_overrides.py`](backend/apply_manual_overrides.py)

Python module that:
- Loads overrides from JSON
- Matches segments based on criteria
- Applies override data to matching segments
- Tracks statistics on applied overrides

### 3. Integration Points
The override system is integrated into both ingestion scripts:
- [`backend/ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) - Step 5.4
- [`backend/ingest_with_batching.py`](backend/ingest_with_batching.py) - Step 5.4

Overrides are applied **after** SFMTA data is loaded but **before** final segment processing.

## How to Add a New Override

### Step 1: Physically Verify the Data
Go to the location and verify:
- Street name and address range
- Which side (L or R) needs correction
- Cardinal direction (North, South, East, West)
- Street cleaning day and time
- Any other parking regulations

### Step 2: Add Override to JSON

Edit [`backend/manual_data_overrides.json`](backend/manual_data_overrides.json):

```json
{
  "overrides": [
    {
      "id": "unique-identifier",
      "type": "street_sweeping",
      "reason": "Explanation of why override is needed",
      "verified_date": "YYYY-MM-DD",
      "verified_by": "Your name",
      "match_criteria": {
        "street_name_regex": "STREET.*NAME",
        "side": "L or R",
        "from_address": "2700",
        "to_address": "2798",
        "cnn": null
      },
      "data": {
        "type": "street-sweeping",
        "day": "Thursday",
        "startTime": "12:00 AM",
        "endTime": "6:00 AM",
        "blockside": "North",
        "weekday": "Thursday",
        "fromhour": "12:00 AM",
        "tohour": "6:00 AM",
        "cnnrightleft": "R"
      },
      "notes": "Additional context"
    }
  ]
}
```

### Step 3: Run Ingestion

The override will be automatically applied during the next ingestion:

```bash
cd backend && python ingest_with_batching.py
```

Look for the output:
```
=== STEP 5.4: Applying Manual Data Overrides ===
  ✓ Applied override 'your-override-id' to STREET NAME R 2700-2798
✓ Applied 1 overrides (0 not matched)
```

## Match Criteria Fields

### Required Fields
- **street_name_regex**: Regular expression to match street name (case-insensitive)
  - Example: `"19TH.*ST"` matches "19TH ST", "19TH STREET", etc.

### Optional Fields (use for precise matching)
- **side**: "L" or "R" - which side of the street
- **from_address**: Starting address number
- **to_address**: Ending address number  
- **cnn**: Specific CNN identifier (if known)

**Tip**: Start with broader criteria (just street name and side) and add more specific criteria if needed to avoid false matches.

## Override Data Fields

### For Street Sweeping Overrides

```json
"data": {
  "type": "street-sweeping",
  "day": "Thursday",              // Display day name
  "startTime": "12:00 AM",        // Display start time
  "endTime": "6:00 AM",           // Display end time
  "blockside": "North",           // Cardinal direction
  "weekday": "Thursday",          // Day for parsing
  "fromhour": "12:00 AM",         // Start time for parsing
  "tohour": "6:00 AM",            // End time for parsing
  "cnnrightleft": "R",            // Side code
  "limits": null                  // Optional: cross streets
}
```

### Future Override Types
The system is designed to support additional override types:
- `parking_regulation` - General parking rules
- `time_limit` - Time-limited parking
- `rpp_zone` - Residential permit zones
- `meter` - Parking meter data

## Verification Workflow

1. **Identify Data Gap**: Notice missing or incorrect data in the application
2. **Physical Verification**: Visit the location and document actual signage
3. **Create Override**: Add entry to `manual_data_overrides.json`
4. **Test Locally**: Run ingestion and verify override is applied
5. **Deploy**: Commit changes and redeploy application
6. **Validate**: Check that the application now shows correct data

## Example: 19th Street Case

### Problem
- CNN has street cleaning data for L side (2701-2799)
- R side (2700-2798) is missing from SFMTA dataset
- Physical verification shows: North side, Thursday 12AM-6AM

### Solution
```json
{
  "id": "19th-st-r-2700-2798",
  "type": "street_sweeping",
  "reason": "Missing from SFMTA street cleaning schedules dataset - physically verified on-site",
  "verified_date": "2025-12-04",
  "verified_by": "User",
  "match_criteria": {
    "street_name_regex": "19TH.*ST",
    "side": "R",
    "from_address": "2700",
    "to_address": "2798"
  },
  "data": {
    "type": "street-sweeping",
    "day": "Thursday",
    "startTime": "12:00 AM",
    "endTime": "6:00 AM",
    "blockside": "North",
    "weekday": "Thursday",
    "fromhour": "12:00 AM",
    "tohour": "6:00 AM",
    "cnnrightleft": "R"
  }
}
```

## Testing Overrides

### Test Override Loading
```bash
cd backend && python apply_manual_overrides.py
```

Expected output:
```
Loaded 1 overrides
  - 19th-st-r-2700-2798: street_sweeping
```

### Test Full Ingestion
```bash
cd backend && python ingest_with_batching.py 2>&1 | tee ingestion.log
```

Check the log for:
```
=== STEP 5.4: Applying Manual Data Overrides ===
  ✓ Applied override '19th-st-r-2700-2798' to 19TH ST R 2700-2798
```

### Verify in Database
```python
# Query the segment
db.street_segments.find_one({
    "streetName": {"$regex": "19TH", "$options": "i"},
    "side": "R",
    "fromAddress": "2700"
})

# Check for override rule
# Should have a rule with "source": "manual_override"
```

## Best Practices

1. **Document Everything**: Always include detailed `reason` and `notes` fields
2. **Verify On-Site**: Never add overrides without physical verification
3. **Use Specific Criteria**: Make match criteria as specific as needed to avoid false matches
4. **Track Verification Date**: Update `verified_date` if you re-verify
5. **Version Control**: Commit override changes with descriptive messages
6. **Regular Audits**: Periodically re-verify overrides as signage may change

## Troubleshooting

### Override Not Applied
- Check match criteria - may be too specific or have typos
- Verify street name regex matches actual data
- Check ingestion logs for "not matched" warnings

### Wrong Segment Matched
- Make match criteria more specific
- Add CNN or exact address range
- Check for similar street names

### Override Appears Twice
- Ensure unique `id` for each override
- Check that match criteria doesn't match multiple segments

## Future Enhancements

Potential improvements to the override system:
1. **Web UI**: Admin interface to add/edit overrides
2. **Bulk Import**: CSV import for multiple overrides
3. **Validation**: Automated checks for override data quality
4. **Expiration**: Auto-expire overrides after a certain date
5. **Conflict Detection**: Warn if override conflicts with SFMTA data
6. **Audit Log**: Track when overrides are applied and by whom

## Related Files

- [`backend/manual_data_overrides.json`](backend/manual_data_overrides.json) - Override data
- [`backend/apply_manual_overrides.py`](backend/apply_manual_overrides.py) - Application logic
- [`backend/ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py) - Main ingestion
- [`backend/ingest_with_batching.py`](backend/ingest_with_batching.py) - Batched ingestion
- [`GEOMETRY_FIX_SUMMARY.md`](GEOMETRY_FIX_SUMMARY.md) - Related geometry fixes