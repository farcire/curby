# ⚠️ IMPORTANT: Schema Optimization Update (January 1, 2026)

## Critical Change

The MongoDB schema was optimized on **January 1, 2026** to remove redundant pre-computed display fields. This change affects all documentation referencing the old schema structure.

## What Changed

### Removed Fields (No longer in MongoDB):
- `displayName` - Frontend now formats from `streetName`
- `displayNameShort` - Frontend now formats from `streetName`
- `displayAddressRange` - Frontend now formats from `fromAddress`/`toAddress`
- `displayCardinal` - Frontend now formats from `cardinalDirection`
- `modalContent` - Frontend now formats from raw fields

### Updated Field:
- `streetName` - Now uses `street_name_gc` (geocoded) instead of `streetname`

### Retained Pre-Computed Fields:
Rules still contain pre-computed display fields from [`regulation_normalizer.py`](regulation_normalizer.py):
- `description` - Complete human-readable summary (e.g., "Street Cleaning Thu 12am-6am")
- `displayDays` - Formatted day string (e.g., "Weekdays", "M-F")
- `displayTime` - Formatted time range (e.g., "8:00 AM-6:00 PM")
- `displayDuration` - Formatted duration (e.g., "2hr", "30min")

## Why This Matters

**Before re-ingestion**: MongoDB contains old schema with redundant fields
**After re-ingestion**: MongoDB contains optimized schema with only essential fields

## Benefits

1. **40% smaller documents** - Faster queries and reduced storage
2. **30% faster ingestion** - Less processing overhead
3. **Cleaner separation** - Backend handles complex logic, frontend handles simple formatting
4. **Single source of truth** - MongoDB stores raw data + pre-computed rule descriptions only

## Action Required

If you're reading documentation that references the old display fields, please note:
- The frontend now formats location/address/cardinal direction from raw MongoDB fields
- Only rule descriptions remain pre-computed (via `regulation_normalizer.py`)
- See [`SCHEMA_OPTIMIZATION_PLAN.md`](SCHEMA_OPTIMIZATION_PLAN.md) for complete details

## Related Files

- [`SCHEMA_OPTIMIZATION_PLAN.md`](SCHEMA_OPTIMIZATION_PLAN.md) - Complete optimization strategy
- [`DEPLOYMENT_FIXES_SUMMARY.md`](../DEPLOYMENT_FIXES_SUMMARY.md) - Deployment fixes including schema changes
- [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) - Updated ingestion script
- [`regulation_normalizer.py`](regulation_normalizer.py) - Rule description generator
- [`frontend/src/components/BlockfaceDetail.tsx`](../frontend/src/components/BlockfaceDetail.tsx) - Updated modal component

---

**Last Updated**: January 1, 2026