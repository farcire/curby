# Data Quality Follow-Up Tasks

## Overview
This document tracks data quality issues identified during the street sweeping and parking regulations analysis. These issues require manual verification and potential data corrections.

---

## 1. Manual Verification of Unpaired Street Cleaning Blocks

### Issue Description
Identified 1,767 CNNs (91.4% of unpaired cases) where:
- Street cleaning data exists on only ONE side (L or R)
- The opposite side has blockface geometry overlay
- BUT no parking rules are available for that side

### Impact
- Users may receive incomplete parking information
- Missing regulations could lead to parking violations
- Data completeness is compromised

### Action Required
**Manual verification of parking regulations for 1,767 blocks**

### Resources
- **Data File**: [`backend/manual_verification_list.csv`](backend/manual_verification_list.csv:1)
- **Script**: [`backend/generate_manual_verification_list.py`](backend/generate_manual_verification_list.py:1)
- **Columns in CSV**:
  - `cnn`: CNN identifier
  - `street_name`: Street name
  - `side`: Which side needs verification (L or R)
  - `cardinal_direction`: Cardinal direction of segment
  - `from_address`: Start of address range
  - `to_address`: End of address range
  - `number_range`: Combined range for reference

### Statistics
- Total CNNs with unpaired street cleaning: 1,933
- CNNs requiring manual verification: 1,767
- Percentage: 91.4%

### Verification Process
1. For each CNN in the list:
   - Verify if parking regulations exist on the specified side
   - Check physical signage if available
   - Consult SFMTA records or street view imagery
   - Document findings

2. Update database with verified regulations:
   - Add missing parking rules to `parking_regulations` collection
   - Link to appropriate blockface geometry
   - Update `street_segments` with new rules

3. Track progress:
   - Mark verified CNNs in a tracking spreadsheet
   - Document any discrepancies found
   - Note blocks that need physical inspection

### Priority
**HIGH** - Affects data completeness and user experience

### Estimated Effort
- ~5-10 minutes per block for desk research
- ~1,767 blocks = 147-295 hours of work
- Consider batching by neighborhood or street for efficiency

---

## 2. Address Range Data Type Inconsistency

### Issue Description
Address fields (`from_address`, `to_address`) contain mixed data types:
- Some are strings (e.g., "301", "331")
- Some are floats/numbers (e.g., 0, 0.0)
- This caused sorting errors in the verification script

### Impact
- Data processing errors
- Inconsistent sorting and filtering
- Potential query issues

### Action Required
1. **Audit address fields** across all collections:
   - `street_segments.fromAddress`
   - `street_segments.toAddress`
   - `parking_regulations` address fields
   - `street_cleaning_schedules` address fields

2. **Standardize data types**:
   - Convert all address fields to strings
   - Pad with leading zeros if needed for sorting
   - Handle special cases (0, null, empty)

3. **Update ingestion scripts**:
   - Ensure consistent type casting during data import
   - Add validation for address fields

### Priority
**MEDIUM** - Affects data processing but workaround exists

### Estimated Effort
- 2-4 hours for audit
- 4-8 hours for standardization script
- 2 hours for testing

---

## 3. Missing Cardinal Directions

### Issue Description
Many segments in the verification list have empty `cardinal_direction` fields, making it harder to identify specific blocks.

### Impact
- Reduced clarity in manual verification
- Harder to match blocks to physical locations
- Potential confusion in user-facing displays

### Action Required
1. **Identify segments with missing cardinal directions**
2. **Derive cardinal directions** from:
   - Street geometry
   - Address progression
   - Neighboring segments
3. **Update database** with derived values
4. **Add validation** to prevent future missing values

### Priority
**LOW** - Nice to have, not blocking

### Estimated Effort
- 4-6 hours for analysis and script
- 2 hours for validation

---

## 4. Zero Address Ranges Investigation

### Issue Description
Many blocks in the verification list show `0-0` address ranges, which may indicate:
- Data quality issues in source data
- Intersection-only segments
- Missing address information

### Examples from Verification List
```
CNN 207101: 03RD ST, Side R, Range: 0-0
CNN 204101: 03RD ST, Side R, Range: 0-0
CNN 205201: 03RD ST, Side L, Range: 0-0
```

### Action Required
1. **Analyze zero-range segments**:
   - Count total occurrences
   - Identify patterns (specific streets, neighborhoods)
   - Determine if these are valid (intersections) or errors

2. **Categorize segments**:
   - Valid intersection segments (keep as 0-0)
   - Missing data (needs research)
   - Data errors (needs correction)

3. **Update or flag** as appropriate

### Priority
**MEDIUM** - May affect significant portion of data

### Estimated Effort
- 3-4 hours for analysis
- Variable time for corrections based on findings

---

## 5. Blockface Geometry Without Rules Pattern

### Issue Description
The high percentage (91.4%) of unpaired CNNs having blockface geometry but no rules suggests a systematic data gap, possibly:
- Incomplete data import from source
- Missing dataset that should be integrated
- Systematic exclusion of certain regulation types

### Action Required
1. **Root cause analysis**:
   - Review data ingestion logs
   - Check source datasets for completeness
   - Identify if specific regulation types are missing

2. **Investigate source data**:
   - SFMTA parking regulations dataset completeness
   - Compare with other cities' data patterns
   - Check for additional datasets that should be integrated

3. **Document findings** and update ingestion process if needed

### Priority
**HIGH** - May reveal systematic data issues

### Estimated Effort
- 4-8 hours for investigation
- Variable time for fixes based on findings

---

## 6. Data Validation and Quality Metrics

### Action Required
Create ongoing data quality monitoring:

1. **Automated checks**:
   - Count of unpaired CNNs (should decrease over time)
   - Percentage of segments with complete data
   - Address range validation
   - Cardinal direction completeness

2. **Regular reports**:
   - Weekly data quality dashboard
   - Track verification progress
   - Monitor new data quality issues

3. **Alerting**:
   - Alert on significant data quality degradation
   - Flag new unpaired CNNs after data updates

### Priority
**MEDIUM** - Prevents future issues

### Estimated Effort
- 6-8 hours for initial setup
- 1-2 hours/week for monitoring

---

## Implementation Plan

### Phase 1: Immediate (This Week)
- [ ] Review manual verification list
- [ ] Prioritize high-traffic streets for verification
- [ ] Begin manual verification of top 50 blocks
- [ ] Document verification process

### Phase 2: Short-term (Next 2 Weeks)
- [ ] Fix address data type inconsistency
- [ ] Investigate zero-range segments
- [ ] Set up basic data quality monitoring
- [ ] Continue manual verification (target: 200 blocks)

### Phase 3: Medium-term (Next Month)
- [ ] Complete root cause analysis of systematic gaps
- [ ] Derive missing cardinal directions
- [ ] Implement automated validation checks
- [ ] Continue manual verification (target: 500 blocks)

### Phase 4: Long-term (Next Quarter)
- [ ] Complete all manual verifications
- [ ] Establish ongoing quality monitoring
- [ ] Document lessons learned
- [ ] Update data ingestion processes

---

## Tracking

### Progress Metrics
- Manual verifications completed: 0 / 1,767 (0%)
- Data type fixes: Not started
- Cardinal directions added: Not started
- Zero-range segments analyzed: Not started

### Last Updated
December 5, 2024

### Owner
Data Quality Team

---

## Related Documents
- [`backend/DATA_QUALITY_ISSUES.md`](backend/DATA_QUALITY_ISSUES.md:1) - Original data quality findings
- [`backend/analyze_missing_sides_pattern.py`](backend/analyze_missing_sides_pattern.py:1) - Analysis script
- [`backend/manual_verification_list.csv`](backend/manual_verification_list.csv:1) - Verification list

---

## 7. Oversized Vehicle Regulations Monitoring

### Issue Description
Identified systematic misinterpretation of "oversized vehicle" parking regulations across the database. These regulations are displaying incorrectly (e.g., as "time-limit" instead of "No oversize vehicles").

### Investigation Details
- **Investigation Date:** December 5, 2024
- **Example Location:** 18th Street North (2700-2798), CNN 868000
- **Documentation:** [`backend/OVERSIZED_VEHICLE_FIX_SUMMARY.md`](backend/OVERSIZED_VEHICLE_FIX_SUMMARY.md:1)

### Regulation Types Identified

#### Type 1: Length AND Height Restrictions
**Display Format:** "No oversize vehicles (>22ft long, >7ft tall) [time] [days]"
- Regulation text contains "No oversized vehicles"
- Details mention "longer than 22 feet or taller than 7 feet"
- May have time/day restrictions or apply 24/7
- **Parking Eligibility:** Does NOT affect eligibility (assumes user has standard vehicle)
- **Severity:** Low (informational only)

#### Type 2: Height-Only Restrictions  
**Display Format:** "No parking vehicles >6ft high [time] [days]"
- Regulation text mentions height restriction only
- Typically "vehicles over 6 feet high"
- May have time/day restrictions
- **Parking Eligibility:** Does NOT affect eligibility (assumes user has standard vehicle)
- **Severity:** Low (informational only)

### Impact
- Incorrect display of parking regulations to users
- Misclassification of regulation type
- Potential confusion about parking restrictions
- **Critical:** These restrictions should NOT block parking eligibility

### Action Required

1. **Immediate Database Fix**:
   - Find all segments with oversized vehicle regulations
   - Update interpretation field with correct display format
   - Set `applies_to_user: false` in logic
   - Set `affects_eligibility: false` in parking_eligibility
   - Change severity from "high" to "low"

2. **Update Ingestion Pipeline**:
   - Modify [`backend/ingest_data_cnn_segments.py`](backend/ingest_data_cnn_segments.py:1)
   - Add special handling for oversized vehicle regulations
   - Detect regulation type from text patterns
   - Generate correct interpretation during ingestion

3. **Update Deterministic Parser**:
   - Modify [`backend/deterministic_parser.py`](backend/deterministic_parser.py:1)
   - Add pattern matching for "oversized" or "oversize" keywords
   - Extract height/length restrictions from details field
   - Parse time restrictions (handle "2400-600" format)
   - Parse day restrictions (handle "M-Su" format)

4. **Ongoing Monitoring**:
   - Monitor for new variations of oversized regulations
   - Check for keywords: "oversize", "oversized", height/length restrictions
   - Document any new patterns discovered
   - Update interpretation rules as needed

### Known Patterns
Based on analysis of existing data:
- **Variations 1,2,3,4,5,7,8,10,13:** Type 1 (length AND height)
- **Variations 6,9,11,12:** Type 2 (height only)

### Priority
**HIGH** - Affects user experience and parking eligibility logic

### Estimated Effort
- Database fix script: 2-3 hours
- Ingestion pipeline update: 3-4 hours
- Deterministic parser update: 2-3 hours
- Testing and validation: 2-3 hours
- **Total:** 9-13 hours

### Related Files
- [`backend/18TH_ST_NORTH_PARKING_INVESTIGATION.md`](backend/18TH_ST_NORTH_PARKING_INVESTIGATION.md:1) - Detailed investigation
- [`backend/OVERSIZED_VEHICLE_FIX_SUMMARY.md`](backend/OVERSIZED_VEHICLE_FIX_SUMMARY.md:1) - Fix requirements
- [`backend/investigate_oversized_regulations.py`](backend/investigate_oversized_regulations.py:1) - Analysis script
- [`backend/get_18th_st_north_details.py`](backend/get_18th_st_north_details.py:1) - Investigation script

### Status
- [x] Issue identified and documented
- [ ] Database fix script created
- [ ] Database records updated
- [ ] Ingestion pipeline updated
- [ ] Deterministic parser updated
- [ ] Testing completed
- [ ] Monitoring established

- [`backend/generate_manual_verification_list.py`](backend/generate_manual_verification_list.py:1) - List generation script