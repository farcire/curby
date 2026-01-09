# CNN 111000 (01st Street) Investigation Report

## Executive Summary

**Critical Finding**: DataSF source data contains **2 street cleaning records** for CNN 111000, but our local database only has **1 segment with 0 schedules**. This confirms a **data ingestion failure** for this location.

## User-Reported Reality vs. Our Data

### User's Visual Verification (May 2025)
- **R side (Southwest)**: Street Cleaning **Wednesday 12:01am - 6:00am**
- **L side**: Street Cleaning **Thursday 12:01am - 6:00am**

### DataSF Source Data (Current)
Found **2 records** for CNN 111000:

#### Record 1
- **CNN**: 111000
- **Block Side**: SouthWest
- **Week Day**: **Wed**
- **Time**: **0:00 - 2:00** (12:00am - 2:00am)
- **Corridor**: 01st St

#### Record 2
- **CNN**: 111000
- **Block Side**: SouthWest
- **Week Day**: **Thu**
- **Time**: **0:00 - 2:00** (12:00am - 2:00am)
- **Corridor**: 01st St

### Our Local Database
- **Segments Found**: 1 (R side only)
- **Side**: R
- **Schedules**: **0** ❌
- **Display Name**: None
- **Blockside**: None

## Key Discrepancies

### 1. Time Range Mismatch
- **User reports**: 12:01am - **6:00am**
- **DataSF shows**: 12:00am - **2:00am**
- **Discrepancy**: 4-hour difference in end time

This suggests either:
- DataSF data is outdated (hasn't been updated since schedule change)
- User is seeing different signage than what's in the official dataset
- There are multiple overlapping regulations (e.g., meter + cleaning)

### 2. Missing L Side Data
- **DataSF**: Has 2 records (both marked "SouthWest" but different days)
- **Our Data**: Only 1 segment (R side) with NO schedules
- **Issue**: We're missing the L side entirely AND not properly ingesting the R side schedules

### 3. Both Records Show "SouthWest"
DataSF shows both Wednesday and Thursday records as "SouthWest" blockside, which is unusual. This could indicate:
- Both sides of the street are on the southwest side of the block
- Data quality issue in DataSF's blockside field
- Need to use CNN + weekday combination to distinguish sides

## Root Cause Analysis

### Data Ingestion Failure
Our ingestion process failed to:
1. ✗ Create separate L and R segments for CNN 111000
2. ✗ Attach street cleaning schedules to the R segment
3. ✗ Properly map DataSF's blockside to our L/R designation

### Possible Causes
1. **CNN-to-Side Mapping Issue**: Our logic may not correctly split CNN 111000 into L/R sides
2. **Blockside Interpretation**: "SouthWest" blockside may not map cleanly to L or R
3. **Schedule Attachment Logic**: Even when segment exists, schedules aren't being attached
4. **Data Filtering**: Records may be filtered out during ingestion due to missing fields

## Meter Data Investigation

Attempted to query DataSF meter data but received **400 Bad Request** error. This suggests:
- The meter dataset may use different field names (not 'cnn')
- Need to query by street name + address range instead
- Meter data may be in a different dataset

## Impact Assessment

### User Experience Impact
Users searching for parking on 01st Street (300-336 block) will:
- ❌ See NO street cleaning information
- ❌ Not know when to move their car
- ❌ Risk getting ticketed for parking during cleaning hours

### Data Quality Impact
- This is likely **not an isolated case**
- If CNN 111000 has ingestion issues, other CNNs probably do too
- The 1,933 segments with "missing side" data may have similar root causes

## Recommendations

### Immediate Actions

1. **Fix CNN 111000 Specifically**
   - Manually create L and R segments
   - Attach Wednesday schedule to one side
   - Attach Thursday schedule to other side
   - Verify which side is actually L vs R using geometry

2. **Investigate Time Discrepancy**
   - Check if DataSF data was updated recently
   - Field verify actual signage on 01st Street
   - Check if there are overlapping regulations (meter + cleaning)

3. **Re-run Ingestion for All CNNs**
   - Fix the blockside-to-side mapping logic
   - Ensure schedules are properly attached
   - Validate that both L and R sides are created when appropriate

### Long-term Solutions

1. **Improve Ingestion Logic**
   ```python
   # Current issue: Not properly handling multiple records per CNN
   # Solution: Group by CNN, then create L/R based on weekday or blockside
   ```

2. **Add Validation Checks**
   - Flag CNNs with only one side when DataSF has multiple records
   - Alert when schedules exist in source but not in local DB
   - Verify schedule attachment after ingestion

3. **Cross-Reference with Meters**
   - Query meter data by street name + address
   - Check if metered locations have different cleaning schedules
   - Document any conflicts between meter hours and cleaning hours

4. **Field Verification Program**
   - Sample 50-100 locations for physical verification
   - Compare signage to both DataSF and our database
   - Identify systematic discrepancies

## Related Issues

- See [`ASYMMETRIC_STREET_CLEANING_DATA_GAPS.md`](ASYMMETRIC_STREET_CLEANING_DATA_GAPS.md) - 1,933 segments with missing side data
- See [`DATA_QUALITY_ISSUES.md`](DATA_QUALITY_ISSUES.md) - Other known data problems
- CNN 961000 previously documented with similar issues

## Next Steps

1. ✅ **Investigation Complete**: Confirmed data ingestion failure
2. ⏭️ **Fix Ingestion Logic**: Update code to properly handle CNN 111000 pattern
3. ⏭️ **Re-ingest Data**: Run corrected ingestion for all affected CNNs
4. ⏭️ **Field Verify**: Check actual signage on 01st Street for time accuracy
5. ⏭️ **Validate Fix**: Confirm CNN 111000 now shows correct data for both sides

---

**Investigation Date**: 2025-12-29  
**Investigator**: Roo  
**Status**: Root cause identified, awaiting remediation