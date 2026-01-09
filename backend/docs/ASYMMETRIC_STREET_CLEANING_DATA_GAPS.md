# Asymmetric Street Cleaning Data Gaps Analysis

## Executive Summary

**Critical Finding**: Out of 12,253 unique street segments (CNNs) in the dataset, **1,933 segments (15.8%) have street cleaning data on only one side**, indicating potential data quality issues where the opposite side is completely missing cleaning schedules.

## Key Statistics

- **Total Segments Analyzed**: 22,573
- **Unique CNNs**: 12,253
- **CNNs with Both Sides**: 10,320 (84.2%)
- **CNNs with One Side Only**: 1,933 (15.8%) ⚠️
- **Data Quality Issue**: YES - Significant asymmetry detected

## What This Means

This analysis specifically identifies cases where:
- ✅ One side of the street HAS street cleaning schedules
- ❌ The opposite side is COMPLETELY MISSING cleaning data

This is distinct from normal scheduling variations where both sides have cleaning but on different days/times (which is expected and intentional).

## Sample Cases of Missing Data

### 1. 01st Street (CNN 111000)
- **Present Side**: R (Southwest side, 300-336)
- **Missing Side**: L
- **Schedule**: Wednesday 12:00 AM-2:00 AM
- **Limits**: Folsom St - Guy Pl

### 2. 02nd Street (Multiple Segments)
Seven consecutive segments (CNN 129000-134000) all show:
- **Present Side**: R (Southwest side)
- **Missing Side**: L
- **Various schedules**: Tuesday/Wednesday/Thursday 3:00 AM-5:00 AM
- **Address ranges**: 2-198 (Market St to Howard St)

### 3. 03rd Street (Extensive Missing Data)
Multiple segments throughout 03rd Street show asymmetry:
- CNNs 185207, 185208: R side present, L side missing (1500-1698)
- CNNs 194101, 194201: Alternating sides missing (2900-2999)
- CNNs 195101-222201: Extensive pattern of missing sides (3000-5598)

## Geographic Patterns

The missing data appears to affect:
1. **Downtown corridors**: 01st, 02nd Streets near Market
2. **Major arterials**: 03rd Street (extensive missing data)
3. **Various neighborhoods**: Pattern spans multiple districts

## Potential Causes

1. **Data Collection Issues**: One side may not have been surveyed
2. **Source Data Problems**: Original dataset may have incomplete records
3. **Ingestion Errors**: Data pipeline may have failed to capture one side
4. **Physical Reality**: Some streets may genuinely have one-sided cleaning (e.g., waterfront, parks)

## Impact on Users

Users searching for parking on streets with missing data will:
- ❌ Not see complete street cleaning information
- ❌ May receive incomplete parking guidance
- ❌ Could potentially park illegally if the missing side has actual cleaning

## Recommendations

### Immediate Actions
1. **Cross-reference with source data**: Check if DataSF's original dataset has both sides
2. **Field verification**: Sample 10-20 segments to verify physical signage
3. **User feedback**: Monitor if users report missing cleaning schedules

### Data Quality Fixes
1. **Re-ingest affected segments**: If source data is complete
2. **Manual data entry**: For segments confirmed to have two-sided cleaning
3. **Flag in UI**: Mark segments with potential incomplete data

### Long-term Solutions
1. **Automated validation**: Add checks during ingestion to flag one-sided segments
2. **Regular audits**: Quarterly review of asymmetric patterns
3. **Source data monitoring**: Track when DataSF updates their dataset

## Next Steps

1. ✅ **Analysis Complete**: 1,933 segments identified with missing side data
2. ⏭️ **Verify Sample**: Check 10 segments against DataSF source data
3. ⏭️ **Field Check**: Physically verify 5 segments with street signage
4. ⏭️ **Prioritize Fixes**: Focus on high-traffic streets first
5. ⏭️ **Update Database**: Implement fixes for confirmed missing data

## Technical Details

- **Analysis Script**: `backend/analyze_missing_side_cleaning.py`
- **Report File**: `backend/missing_side_cleaning_report.json`
- **Source Data**: `backend/segments_with_sweeping_rules.json`
- **Date**: 2025-12-29

## Related Issues

- See `backend/DATA_QUALITY_ISSUES.md` for other known data problems
- CNN 961000 previously documented with similar issues
- This analysis complements ongoing data quality improvements

---

**Status**: Analysis complete, awaiting verification and remediation plan