# Data Quality Issues

This document tracks known data quality issues in the SFMTA Socrata datasets used by Curby.

---

## Issue #1: Missing Street Cleaning Records

**Status**: 🚨 OPEN  
**Severity**: HIGH  
**Discovered**: December 4, 2025  
**Dataset**: Street Cleaning Schedules (`yhqp-riqs`)

### Description

The Street Cleaning Schedules dataset is missing records for some street segments that have verified street cleaning schedules. This results in incomplete parking restriction information being displayed to users.

### Example Case: CNN 961000R

**Location**: 19th Street (North side), between York St and Bryant St, Mission neighborhood

**What's Missing**:
- CNN: 961000
- Side: R (Right/North)
- Day: Thursday
- Time: 12:00 AM - 6:00 AM
- Cardinal Direction: North

**What's Present**:
- CNN: 961000
- Side: L (Left/South) ✅
- Day: Friday
- Time: 12:00 AM - 6:00 AM
- Cardinal Direction: South

**Verification Method**: Manual visual inspection of street signs

### Impact

**User Safety**: HIGH
- Users parking on affected segments won't see street cleaning restrictions
- Risk of parking tickets for users relying on the app
- Undermines user trust in app accuracy

**Data Completeness**: UNKNOWN
- Unknown how many other records are missing
- Requires dataset-wide validation
- May indicate systemic data collection issue

**System Functionality**: LOW
- System handles missing data gracefully
- No crashes or errors
- Can implement workarounds (cardinal direction inference)

### Root Cause Analysis

**Possible Causes**:
1. Data collection process may not capture all sides of streets
2. Data entry error or omission
3. Update/sync issue between SFMTA systems and Socrata
4. Different data sources for left vs right sides

**Pattern Observed**:
- Left side (L) has data ✅
- Right side (R) is missing ❌
- Suggests potential systematic issue with right-side data collection

### Recommended Actions

#### Immediate (Week 1)
1. ✅ Document the issue (DONE)
2. ⏭️ Report to SFMTA data team
3. ⏭️ Create validation script to find similar issues
4. ⏭️ Implement cardinal direction inference as workaround

#### Short-term (Month 1)
1. ⏭️ Run validation across entire dataset
2. ⏭️ Generate report of all potentially missing records
3. ⏭️ Implement user feedback mechanism for data corrections
4. ⏭️ Add data quality metrics to monitoring dashboard

#### Long-term (Quarter 1)
1. ⏭️ Establish regular data quality audits
2. ⏭️ Create feedback loop with SFMTA for corrections
3. ⏭️ Implement automated validation on data updates
4. ⏭️ Build confidence scores for data completeness

### Workarounds Implemented

**None yet** - Pending implementation

**Planned Workarounds**:
1. **Cardinal Direction Inference**: Use geometry or opposite side to infer missing cardinal directions
2. **Display Name Generation**: Generate names even without street cleaning data
3. **Street Limit Fallback**: Use Active Streets `f_st`/`t_st` fields when cleaning limits missing
4. **User Warnings**: Display data completeness indicators in UI

### Related Issues

- Issue #2: Right side segments missing cardinal directions (caused by this issue)
- Issue #3: Right side segments missing from/to streets (caused by this issue)

### References

- Investigation Report: [`backend/cnn_961000_investigation/INVESTIGATION_SUMMARY.md`](cnn_961000_investigation/INVESTIGATION_SUMMARY.md)
- Ingestion Code: [`backend/ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)
- Data Model: [`backend/models.py`](models.py)

---

## Issue #2: Missing Cardinal Directions for Segments Without Street Cleaning

**Status**: 🚨 OPEN  
**Severity**: MEDIUM  
**Discovered**: December 4, 2025  
**Caused By**: Issue #1

### Description

Street segments that don't have street cleaning schedules in the dataset also don't have cardinal directions (North, South, East, West). This is because cardinal directions are currently only extracted from the street cleaning `blockside` field.

### Impact

**User Experience**: MEDIUM
- Cannot generate proper display names (e.g., "19th Street (North side)")
- Less intuitive navigation and identification of segments
- Reduced usability for users trying to find specific sides of streets

**Data Completeness**: MEDIUM
- Affects all segments without street cleaning data
- Includes segments where cleaning exists but is missing from dataset (Issue #1)
- Also affects segments that genuinely have no street cleaning

### Solution

**Implement Cardinal Direction Inference**:
1. Use geometry analysis to determine orientation
2. Calculate perpendicular direction to street centerline
3. Determine which side is north/south/east/west
4. Or use opposite of known side (if L=South, then R=North)

**Status**: Planned for implementation

---

## Issue #3: Missing From/To Streets for Segments Without Street Cleaning

**Status**: 🚨 OPEN  
**Severity**: LOW  
**Discovered**: December 4, 2025  
**Caused By**: Issue #1

### Description

Street segments without street cleaning schedules don't have `fromStreet` and `toStreet` fields populated. These fields currently only come from the street cleaning `limits` field.

### Impact

**User Experience**: LOW
- Less context about segment boundaries
- Users can't see cross streets for segments without cleaning
- Minor inconvenience, not critical functionality

**Data Completeness**: MEDIUM
- Affects all segments without street cleaning data
- Information exists in Active Streets dataset but isn't being used

### Solution

**Use Active Streets as Fallback**:
1. Extract `f_st` (from street) and `t_st` (to street) from Active Streets dataset
2. Populate `fromStreet` and `toStreet` for all segments
3. Use street cleaning limits as primary source, Active Streets as fallback

**Status**: Planned for implementation

---

## Data Quality Metrics

### Current State (as of Dec 4, 2025)

| Metric | Value | Status |
|--------|-------|--------|
| **Active Streets Coverage** | 100% | ✅ Complete |
| **Street Cleaning Coverage** | Unknown | ⚠️ Needs audit |
| **Parking Regulations Coverage** | Unknown | ⚠️ Needs audit |
| **Cardinal Direction Coverage** | ~50% | ⚠️ Incomplete |
| **From/To Streets Coverage** | ~50% | ⚠️ Incomplete |

### Known Issues Summary

| Issue | Severity | Status | Affected Records |
|-------|----------|--------|------------------|
| Missing street cleaning records | HIGH | Open | Unknown (≥1) |
| Missing cardinal directions | MEDIUM | Open | ~50% of segments |
| Missing from/to streets | LOW | Open | ~50% of segments |

---

## Validation Scripts

### Planned Validation Checks

1. **Missing Street Cleaning Detector**
   - Find CNNs where only one side has street cleaning
   - Flag for manual verification
   - Generate report of potentially missing records

2. **Cardinal Direction Validator**
   - Identify segments without cardinal directions
   - Attempt to infer from geometry
   - Flag segments that can't be inferred

3. **Data Completeness Checker**
   - Calculate coverage metrics for all datasets
   - Track completeness over time
   - Alert on degradation

### Implementation Status

- ⏭️ Missing Street Cleaning Detector: Not implemented
- ⏭️ Cardinal Direction Validator: Not implemented
- ⏭️ Data Completeness Checker: Not implemented

---

## Reporting Process

### How to Report a Data Quality Issue

1. **Document the Issue**
   - Location (CNN, address, or coordinates)
   - What's wrong (missing, incorrect, outdated)
   - How you verified it (visual inspection, official source, etc.)
   - Impact on users

2. **Add to This Document**
   - Create new issue section
   - Assign severity and status
   - Link to investigation reports

3. **Create Investigation Report**
   - Use [`inspect_cnn_961000.py`](inspect_cnn_961000.py) as template
   - Export raw data for analysis
   - Document findings

4. **Notify SFMTA** (for source data issues)
   - Prepare detailed report
   - Include verification evidence
   - Request correction timeline

---

## Contact Information

### SFMTA Data Team
- **Dataset Portal**: https://data.sfgov.org
- **Support**: (Contact information needed)
- **API Documentation**: https://dev.socrata.com/

### Internal Team
- **Data Quality Owner**: (To be assigned)
- **Technical Lead**: (To be assigned)
- **Product Owner**: (To be assigned)

---

**Last Updated**: December 4, 2025  
**Next Review**: (To be scheduled)