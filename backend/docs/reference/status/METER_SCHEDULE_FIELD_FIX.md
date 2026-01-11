# Meter Schedule Field Mapping Fix

## Problem Discovered

After running the ingestion scripts, the `street_segments` collection showed **100% of meters (115,023 total) had NULL schedule data**. Investigation revealed the root cause:

### Wrong Field Names Used

The ingestion script was trying to extract fields that **don't exist** in the Socrata API response:

```python
# ❌ WRONG - These fields don't exist
schedule_entry = {
    "beginTime": row.get("beg_time_dt"),      # Returns None
    "endTime": row.get("end_time_dt"),        # Returns None
    "rate": row.get("rate"),                  # Returns None
    "schedule_type": row.get("schedule_type") # This one exists
}
```

### Actual Available Fields

The Meter Operating Schedules dataset (6cqg-dxku) provides these fields:

```python
Available fields (12):
- active_meter_status
- applied_color_rule
- block_side
- cap_color
- days_applied          # ✓ "Mo,Tu,We,Th,Fr"
- from_time             # ✓ "7:00 AM"
- post_id               # ✓ "201-00040"
- priority              # ✓ 1
- schedule_type         # ✓ "Operating Schedule", "Tow", "Alternate"
- street_and_block
- time_limit            # ✓ "60 minutes"
- to_time               # ✓ "6:00 PM"
```

### Example Data

```json
{
  "post_id": "201-00040",
  "schedule_type": "Operating Schedule",
  "days_applied": "Mo,Tu,We,Th,Fr",
  "from_time": "7:00 AM",
  "to_time": "6:00 PM",
  "time_limit": "60 minutes",
  "cap_color": "Yellow",
  "priority": 1,
  "block_side": "Even"
}
```

## Solution Applied

Fixed `ingest_data_cnn_segments.py` lines 804-836 to use correct field names:

```python
schedule_entry = {
    "days_applied": row.get("days_applied"),  # "Mo,Tu,We,Th,Fr"
    "from_time": row.get("from_time"),        # "7:00 AM"
    "to_time": row.get("to_time"),            # "6:00 PM"
    "time_limit": row.get("time_limit"),      # "60 minutes"
    "schedule_type": row.get("schedule_type"), # "Operating Schedule", "Tow", "Alternate"
    "cap_color": row.get("cap_color"),        # "Yellow", "Grey", etc.
    "priority": row.get("priority"),          # Priority number
    "block_side": row.get("block_side")       # "Even", "Odd"
}
```

## Multiple Schedules Per Meter

The user reported that a single `post_id` can have **4 different schedules** attached. This is correct and expected:

- **Operating Schedule** - Normal metered hours (e.g., Mon-Fri 7am-6pm)
- **Tow** - Tow-away hours (e.g., Mon-Fri 7am-9am)
- **Alternate** - Weekend/alternate schedule (e.g., Sat 7am-6pm)
- **Additional schedules** - Other time periods

The `prioritize_meter_schedules()` function **only sorts** schedules by priority (TOW > ALTERNATE > OP > PRE+FREE), it does **NOT filter** them. All schedules are kept.

## Next Steps

1. ✅ **Fixed field mapping** - Use correct Socrata API field names
2. ⏳ **Wipe MongoDB** - Clear existing data with NULL schedules
3. ⏳ **Re-run ingestion** - Use `--force-restart` flag
4. ⏳ **Verify schedules** - Check that meters now have all 4 schedules
5. ⏳ **Run interpretation layer** - Apply 24/7 No Parking conflict resolution

## Commands

```bash
# 1. Wipe database
cd backend && python3 wipe_mongodb.py

# 2. Run full ingestion (30-45 minutes)
cd backend && python3 ingest_data_cnn_segments.py --force-restart

# 3. Check results
cd backend && python3 check_meter_ingestion_results.py

# 4. Run interpretation layer
cd backend && python3 generate_interpretation_layer.py
```

## Impact

This fix will restore **115,023 meters** with their complete schedule data, enabling proper display of:
- Operating hours
- Tow-away periods
- Time limits
- Day-specific schedules
- Priority-based schedule selection

## Date

January 4, 2026 (PST)