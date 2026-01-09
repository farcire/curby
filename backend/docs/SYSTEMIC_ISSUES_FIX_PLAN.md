# Systemic Issues Fix Plan

## Executive Summary

Based on the comprehensive audit ([`METER_AND_INTERPRETATION_AUDIT.json`](backend/METER_AND_INTERPRETATION_AUDIT.json:1)), we identified two critical systemic issues affecting data quality:

1. **Broken Sweeping Interpretations**: 22,573 segments (65.8%) have "None None" interpretations
2. **No Parking + Sweeping Edge Cases**: 116 segments (0.3%) need special two-line display

**Note on Null Schedules**: The 4,090 segments (11.9%) with null schedule values are segments without parking meters in their area. This is expected and normal - not all street segments have metered parking.

**Note on Missing Meters Field**: Meter data is stored in the `schedules` array, not a separate `meters` field. The data structure is correct as designed.

## Issue Details

### 1. Broken Sweeping Interpretations (22,573 segments)

**Problem**: Street sweeping rules have interpretations with "None None" summaries and generic fallback messages.

**Example**:
```json
{
  "type": "street-sweeping",
  "interpretation": {
    "display": {
      "summary": "None None",
      "details": "Unable to fully interpret this restriction. Please check signage."
    }
  }
}
```

**Root Cause**: LLM interpretation system received incomplete or malformed input for sweeping rules, triggering fallback interpretations.

**Impact**:
- Users see unhelpful "None None" messages
- Street cleaning schedules are not clearly communicated
- 65.8% of segments affected

**Solution**: [`fix_sweeping_interpretations.py`](backend/fix_sweeping_interpretations.py:1)

### 2. No Parking + Sweeping Edge Cases (116 segments)

**Problem**: Segments with "No parking any time" combined with street sweeping schedules create ambiguity. Users might think parking is only prohibited during sweeping times.

**Example Segment**: "16th Street (South side, 601-699)" has:
- 1 "No parking any time" rule
- 4 street sweeping rules

**Root Cause**: Display logic doesn't handle the combination of absolute prohibition + informational sweeping schedules.

**Impact**:
- User confusion about when parking is actually prohibited
- Potential parking violations
- Unclear signage interpretation

**Solution**: Two-line display pattern:
```
Line 1: "No Parking Any Time" (primary restriction, high severity)
Line 2: "Street Cleaning [schedule]" (informational only)
```

Implemented in [`fix_sweeping_interpretations.py`](backend/fix_sweeping_interpretations.py:1)

## Implementation Plan

### Phase 1: Fix Sweeping Interpretations

**Script**: [`fix_sweeping_interpretations.py`](backend/fix_sweeping_interpretations.py:1)

**Steps**:
1. Find all segments with `rules.interpretation.display.summary == "None None"`
2. For each street-sweeping rule:
   - Parse day, startTime, endTime from rule
   - Create proper interpretation:
     ```json
     {
       "type": "street-sweeping",
       "display": {
         "summary": "Street Cleaning",
         "details": "No parking Fri 9:00 AM-11:00 AM for street cleaning.",
         "severity": "medium",
         "icon": "street-cleaning"
       }
     }
     ```
3. Update segment with fixed interpretation

**Expected Results**:
- Segments with "None None": 22,573 → 0
- Segments with proper sweeping interpretations: 0 → 22,573

**Execution**:
```bash
cd backend
python fix_sweeping_interpretations.py
```

### Phase 2: Fix No Parking + Sweeping Combinations

**Script**: [`fix_sweeping_interpretations.py`](backend/fix_sweeping_interpretations.py:1) (same script, different function)

**Steps**:
1. Load 116 problem segments from [`segments_no_parking_plus_sweeping.json`](backend/segments_no_parking_plus_sweeping.json:1)
2. For each segment:
   - Identify "no parking any time" rule
   - Identify sweeping rules
   - Create two-line interpretation:
     - Line 1: No parking (priority 1, high severity)
     - Line 2: Sweeping schedule (priority 2, informational)
3. Update segment with special interpretation

**Expected Results**:
- 116 segments with clear two-line display
- No user confusion about parking prohibition

**Execution**: Included in same script as Phase 2

### Phase 3: Validation and Meter Data Audit

**Script**: [`audit_meter_and_interpretation_issues.py`](backend/audit_meter_and_interpretation_issues.py:1)

**Steps**:
1. Re-run comprehensive audit
2. Audit meter data in rules to ensure accuracy
3. Verify metrics:
   - "None None" interpretations: 22,573 → 0
   - No parking + sweeping: 116 → properly handled
   - Null schedules: 4,090 (expected - non-metered segments)
4. Generate new audit report
5. Sample test segments from each category

**Execution**:
```bash
cd backend
python audit_meter_and_interpretation_issues.py
python audit_meter_data_in_rules.py
```

## Execution Order

```bash
# 1. Backup database
python backend/backup_database.py

# 2. Fix sweeping interpretations (fixes "None None" + no parking edge cases)
python backend/fix_sweeping_interpretations.py

# 3. Re-run audits to verify improvements
python backend/audit_meter_and_interpretation_issues.py
python backend/audit_meter_data_in_rules.py

# 4. Review audit reports
cat backend/METER_AND_INTERPRETATION_AUDIT.json
cat backend/METER_DATA_AUDIT_SUMMARY.json
```

## Success Criteria

### Quantitative Metrics
- [ ] "None None" interpretations: 22,573 → 0 (100% reduction)
- [ ] No parking + sweeping: 116 segments with proper two-line display
- [ ] Null schedules: 4,090 (documented as expected - non-metered segments)
- [ ] Meter data only appears in rules when actual meters exist for that CNN

### Qualitative Metrics
- [ ] Street sweeping schedules display clearly
- [ ] No parking + sweeping combinations are unambiguous
- [ ] User-facing display text is clear and actionable
- [ ] Meter data only shows for segments that actually have meters

## Risk Mitigation

### Data Backup
Before running fixes:
```bash
# Backup MongoDB
./backend/backup_database.sh
```

### Rollback Plan
If issues occur:
1. Restore from backup
2. Review error logs
3. Fix script issues
4. Re-run with corrected logic

### Testing Strategy
1. Test on sample segments first (limit to 10-100)
2. Verify results manually
3. Run full ingestion/fixes
4. Validate with comprehensive audit

## Dependencies

### Python Packages
- `motor` - MongoDB async driver
- `sodapy` - SF Open Data API client
- `asyncio` - Async execution

### External Data Sources
- SFMTA Parking Meters: `data.sfgov.org/8vzz-qzz9`

### Environment Variables
- `MONGODB_URI` - MongoDB connection string
- `GEMINI_API_KEY` - (optional) for future LLM interpretations

## Timeline

- **Phase 1** (Meter Ingestion): ~30-60 minutes (depends on API rate limits)
- **Phase 2** (Sweeping Fixes): ~10-20 minutes
- **Phase 3** (No Parking + Sweeping): ~5 minutes
- **Phase 4** (Validation): ~5 minutes

**Total Estimated Time**: 1-2 hours

## Next Steps

1. Review this plan
2. Backup database
3. Execute Phase 1 (meter ingestion)
4. Execute Phase 2 (sweeping fixes)
5. Execute Phase 4 (validation)
6. Document results
7. Update API documentation with new meter data structure

## Related Files

- [`METER_DATA_INGESTION_NEEDED.md`](backend/METER_DATA_INGESTION_NEEDED.md:1) - Original meter ingestion spec
- [`METER_AND_INTERPRETATION_AUDIT.json`](backend/METER_AND_INTERPRETATION_AUDIT.json:1) - Audit results
- [`segments_with_null_schedules.json`](backend/segments_with_null_schedules.json:1) - 4,090 affected segments
- [`segments_with_sweeping_rules.json`](backend/segments_with_sweeping_rules.json:1) - 22,573 affected segments
- [`segments_no_parking_plus_sweeping.json`](backend/segments_no_parking_plus_sweeping.json:1) - 116 edge cases
- [`audit_meter_and_interpretation_issues.py`](backend/audit_meter_and_interpretation_issues.py:1) - Reusable audit script