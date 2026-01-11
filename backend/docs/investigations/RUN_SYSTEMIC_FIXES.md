# Running Systemic Issue Fixes

This guide walks you through executing the fixes for the two systemic issues identified in the audit.

**Note**: The 4,090 segments with null schedules are segments without parking meters - this is expected and normal.

## Prerequisites

### 1. Backup Database
**CRITICAL**: Always backup before making bulk changes.

```bash
# You're already in the backend directory, so just run:
python backup_database.py
```

This creates a JSON backup in `./database_backups/backup_TIMESTAMP/cnn_segments.json`

### 2. Verify Environment
Ensure you have the required environment variables:

```bash
# Check MongoDB connection
echo $MONGODB_URI

# Check if Gemini API key is set (optional for these fixes)
echo $GEMINI_API_KEY
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

Required packages:
- `motor` - MongoDB async driver
- `sodapy` - SF Open Data API client
- `pymongo` - MongoDB sync driver

## Execution Steps

### Step 1: Fix Sweeping Interpretations

This fixes:
- ✓ Broken sweeping interpretations (22,573 segments with "None None")
- ✓ No parking + sweeping edge cases (116 segments)

**Command**:
```bash
cd backend
python fix_sweeping_interpretations.py
```

**Expected Output**:
```
================================================================================
FIXING STREET SWEEPING INTERPRETATIONS
================================================================================
Found 22573 segments with broken sweeping interpretations
Fixed 100 segments...
Fixed 200 segments...
...
✓ Fixed 22573 segments with sweeping interpretations

================================================================================
FIXING NO PARKING + SWEEPING COMBINATIONS
================================================================================
Found 116 segments needing special interpretation
Fixed 10 segments...
Fixed 20 segments...
...
✓ Fixed 116 segments with no-parking + sweeping combinations

================================================================================
VERIFICATION
================================================================================
Segments with 'None None' interpretations: 0
Segments with proper sweeping interpretations: 22,573

Sample fixed segment:
  CNN: 1786000
  Side: L
  Display: 35th Avenue (East side, 2850-2898)
  Sweeping interpretation:
    Summary: Street Cleaning
    Details: No parking Friday 9:00 AM-11:00 AM for street cleaning.

================================================================================
FIXES COMPLETE
================================================================================
```

**What It Does**:
1. Finds all segments with "None None" interpretations
2. Creates proper interpretations for street sweeping rules
3. Handles special two-line display for no parking + sweeping
4. Updates segments with fixed interpretations
5. Verifies all fixes applied correctly

**Time**: 15-25 minutes

**Troubleshooting**:
- If segments not found, verify JSON files exist in backend/
- If MongoDB connection fails, check MONGODB_URI
- If updates fail, check MongoDB write permissions

### Step 2: Re-run Audits

Verify all fixes were successful.

**Commands**:
```bash
cd backend
python audit_meter_and_interpretation_issues.py
python audit_meter_data_in_rules.py
```

**Expected Output** (audit_meter_and_interpretation_issues.py):
```
================================================================================
PARKING DATA AUDIT
================================================================================
Analyzing 34,324 segments...

Issue 1: Segments with null schedules
Found: 4,090 segments (11.9%)
ℹ️  EXPECTED (non-metered segments)

Issue 2: Segments with sweeping rules
Found: 22,573 segments (65.8%)
All have proper interpretations ✓

Issue 3: No parking + sweeping combinations
Found: 116 segments (0.3%)
All have proper two-line display ✓

================================================================================
AUDIT COMPLETE
================================================================================
Results saved to: METER_AND_INTERPRETATION_AUDIT.json
```

**Expected Output** (audit_meter_data_in_rules.py):
```
================================================================================
METER DATA IN RULES AUDIT
================================================================================
Total segments: 34,324

SCHEDULE STATUS BREAKDOWN
Segments with schedules array: 30,234
  - With valid meter data: 26,144
  - With null/empty data: 4,090
Segments without schedules: 4,090

KING STREET ANALYSIS
Found 12 King Street segments
King Street (Southeast side, 201-299)
  CNN: 7833101, Side: L
  Schedules count: 8
  Sample schedule: {rate: 2.0, beginTime: 9, endTime: 18, ...}

================================================================================
AUDIT COMPLETE
================================================================================
```

**What They Do**:
1. Scan all segments for interpretation issues
2. Verify meter data only appears when actual meters exist
3. Analyze King Street and other metered segments
4. Generate detailed reports
5. Provide executive summaries

**Time**: 5-10 minutes each

## Verification Checklist

After running all fixes, verify:

- [ ] **"None None" Interpretations**: Should be 0 (was 22,573)
- [ ] **No Parking + Sweeping**: All 116 segments should have two-line display
- [ ] **Null Schedules**: 4,090 (expected - documented as non-metered segments)
- [ ] **Meter Data in Rules**: Only appears for segments with actual meters

### Manual Spot Checks

#### Check Sweeping Interpretation
```bash
# Query a segment with sweeping rules
mongo elegant-lynx-play --eval "db.cnn_segments.findOne({cnn: '1786000', side: 'L', 'rules.type': 'street-sweeping'}, {'rules.$': 1})"
```

Expected: `interpretation.display.summary` should be "Street Cleaning", not "None None"

#### Check No Parking + Sweeping
```bash
# Query one of the 116 edge case segments
mongo elegant-lynx-play --eval "db.street_segments.findOne({cnn: '698000', side: 'L'}, {rules: 1})"
```

Expected: Two interpretations with `display_priority` 1 and 2

#### Check Meter Data Accuracy
```bash
# Run the meter data audit
python backend/audit_meter_data_in_rules.py
```

Expected: Meter data only appears for segments with actual meters (King Street should show meters, residential streets without meters should not)

## Rollback Procedure

If issues occur:

```bash
# 1. Stop any running processes

# 2. Restore from backup
python restore_database.py ./database_backups/backup_TIMESTAMP/cnn_segments.json

# 3. Review error logs in terminal output

# 4. Fix script issues

# 5. Re-run with corrected logic
```

**Note**: Replace `TIMESTAMP` with the actual timestamp from your backup directory.

## Success Metrics

### Before Fixes
- "None None": 22,573 (65.8%)
- No parking + sweeping: 116 (unclear display)
- Null schedules: 4,090 (11.9% - non-metered segments)

### After Fixes (Target)
- "None None": 0 (0%)
- No parking + sweeping: 116 (clear two-line display)
- Null schedules: 4,090 (documented as expected)
- Meter data accuracy: 100% (only shows when meters exist)

## Next Steps

After successful execution:

1. **Update Frontend**: Ensure UI handles two-line display for no parking + sweeping
2. **Verify Meter Display**: Ensure meter data only shows when actual meters exist
3. **Monitor Performance**: Check API response times
4. **User Testing**: Verify display clarity with sample users
5. **Schedule Regular Audits**: Run audits monthly to catch new issues

## Support

If you encounter issues:

1. Check logs in terminal output
2. Review [`SYSTEMIC_ISSUES_FIX_PLAN.md`](SYSTEMIC_ISSUES_FIX_PLAN.md:1) for detailed explanations
3. Verify MongoDB connection and permissions
4. Check SF Open Data API status: https://data.sfgov.org/

## Related Documentation

- [`SYSTEMIC_ISSUES_FIX_PLAN.md`](SYSTEMIC_ISSUES_FIX_PLAN.md:1) - Detailed fix plan
- [`METER_AND_INTERPRETATION_AUDIT.json`](METER_AND_INTERPRETATION_AUDIT.json:1) - Current audit results
- [`fix_sweeping_interpretations.py`](fix_sweeping_interpretations.py:1) - Sweeping fix script
- [`audit_meter_and_interpretation_issues.py`](audit_meter_and_interpretation_issues.py:1) - Main audit script
- [`audit_meter_data_in_rules.py`](audit_meter_data_in_rules.py:1) - Meter data accuracy audit
- [`backup_database.py`](backup_database.py:1) - Database backup script
- [`restore_database.py`](restore_database.py:1) - Database restore script