# Cardinal Direction Ingestion Issue

## Problem Identified

The cardinal direction data from the street sweeping schedule dataset (yhqp-riqs) is **NOT being ingested** into the `street_segments` collection. 

### Expected Data
According to yhqp-riqs dataset for CNN 868000 (18th Street):
- **18th Street R side**: blockside = "North"
- **18th Street L side**: blockside = "South"

### Actual Data in Database
- **18th Street R side**: No cardinal direction field
- **18th Street L side**: No cardinal direction field

## Root Cause

The data ingestion script is not extracting the `blockside` field from the street sweeping schedule (yhqp-riqs) and storing it in the `rules` array.

## Required Fix

### 1. Update Data Ingestion Script
The ingestion script (likely `ingest_data_cnn_segments.py` or similar) needs to be modified to:

1. **Extract blockside field** from yhqp-riqs dataset
2. **Store it in the rules** when creating street cleaning rules
3. **Map it to the correct side** (L or R)

### 2. Expected Rule Structure
Each street cleaning rule should include:
```python
{
    "type": "street-sweeping",
    "day": "Th",
    "startTime": "0",
    "endTime": "6",
    "blockside": "North",  # ← THIS FIELD IS MISSING
    # ... other fields
}
```

### 3. Ingestion Code Changes Needed

In the street cleaning ingestion section, add:
```python
# When processing street sweeping data from yhqp-riqs
rule = {
    "type": "street-sweeping",
    "day": sweeping_record.get("weekday"),
    "startTime": sweeping_record.get("fromhour"),
    "endTime": sweeping_record.get("tohour"),
    "blockside": sweeping_record.get("blockside"),  # ← ADD THIS
    # ... other fields
}
```

### 4. Re-ingestion Required

After fixing the ingestion script:
1. **Re-run ingestion** for Mission neighborhood
2. **Verify** that blockside field appears in rules
3. **Test** that API correctly extracts and displays cardinal directions

## Current Workaround

The API code is already prepared to extract cardinal directions from the `blockside` field in rules:

```python
# In main.py - this code is ready but has no data to work with
for rule in rules:
    if rule.get('blockside'):
        cardinal_direction = rule.get('blockside')
        break
```

Once the data is properly ingested, the display will automatically show:
- "18th Street (North side, 2700-2798)" for R side
- "18th Street (South side, 2701-2799)" for L side

## Action Items

- [ ] Locate and update the data ingestion script
- [ ] Add blockside field extraction from yhqp-riqs
- [ ] Re-run ingestion for Mission neighborhood
- [ ] Verify cardinal directions appear in database
- [ ] Test API response shows correct cardinal directions
- [ ] Run validation script to check data quality

## References

- yhqp-riqs dataset: Street Sweeping Schedule with blockside field
- CNN 868000: 18th Street test case
- Expected: R=North, L=South