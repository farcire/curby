# CNN 961000 Investigation Summary

## Overview
CNN 961000 represents **19th Street** between **York Street** and **Bryant Street** in the **Mission** neighborhood (zip code 94110).

**🚨 CRITICAL FINDING**: This investigation revealed a **data quality issue** in the SFMTA Socrata dataset - the right side street cleaning schedule is missing.

---

## 1. Active Streets Data (Primary Backbone)

### Street Segment Information
- **CNN**: 961000
- **Street Name**: 19TH ST
- **From Street**: YORK ST (f_node_cnn: 24009000)
- **To Street**: BRYANT ST (t_node_cnn: 24012000)
- **Neighborhood**: Inner Mission
- **Analysis Neighborhood**: Mission
- **Supervisor District**: 9
- **Zip Code**: 94110
- **Layer**: STREETS
- **Class Code**: 5
- **One-Way**: B (Both directions)
- **Jurisdiction**: DPW

### Address Ranges
- **Left Side (L)**:
  - From Address: 2701
  - To Address: 2799
  - Parity: Odd numbers

- **Right Side (R)**:
  - From Address: 2700
  - To Address: 2798
  - Parity: Even numbers

### Geometry
- **Type**: LineString
- **Coordinates**: 
  - Start: [-122.409032825, 37.760543037]
  - End: [-122.409997159, 37.760485264]
- **Direction**: Runs roughly east-west

---

## 2. Street Cleaning Data

### Left Side (L) - South Side ✅
- **CNN**: 961000
- **Side**: L (cnnrightleft)
- **Cardinal Direction**: South (blockside)
- **Schedule**:
  - Day: Friday (Fri)
  - Time: 0-6 (12:00 AM - 6:00 AM)
  - Weeks: All weeks (week1-5 all = 1)
  - Holidays: 0 (cleaning occurs on holidays)
- **Limits**: York St - Bryant St
- **Corridor**: 19th St
- **Block Sweep ID**: 1634161
- **Status**: ✅ Present in Socrata dataset

### Right Side (R) - North Side 🚨
- **Status**: ❌ **MISSING FROM SOCRATA DATASET**
- **Verified Schedule** (manual visual inspection):
  - Day: Thursday (Thu)
  - Time: 0-6 (12:00 AM - 6:00 AM)
  - Cardinal Direction: North
  - Limits: York St - Bryant St (inferred)
- **Impact**: Users will not see this street cleaning restriction
- **Data Quality Issue**: This record should exist but is absent from the dataset

### Geometry Match
The street cleaning geometry for the left side matches the Active Streets centerline:
- Start: [-122.409032825784, 37.760543037674]
- End: [-122.409997158385, 37.7604852639]

---

## 3. Parking Regulations Data

### Current Status
**✅ VERIFIED: No parking regulations exist for CNN 961000**

### Manual Verification
- Visual inspection confirms: **No parking regulation signs** on this block
- Both sides (L and R) have no parking restrictions beyond street cleaning
- Dataset correctly reflects reality

### Technical Notes
Parking regulations in the SFMTA dataset:
1. Do NOT have a CNN field
2. Are matched by **geometry proximity** to street centerlines
3. Use spatial joins to determine which segment they apply to

### Investigation Notes
- The [`match_parking_regulations_to_segments()`](../ingest_data_cnn_segments.py:242) function performs spatial matching
- Uses multi-point sampling to determine which side (L/R) a regulation applies to
- Maximum distance threshold: 0.0005 degrees (~50 meters)
- For CNN 961000, no parking regulations were found within this threshold
- **Confirmed accurate** - no regulations exist physically

---

## 4. Database State (MongoDB)

### Segment 1: Left Side (L) ✅
```json
{
  "cnn": "961000",
  "side": "L",
  "streetName": "19TH ST",
  "fromStreet": "York St",
  "toStreet": "Bryant St",
  "fromAddress": "2701",
  "toAddress": "2799",
  "cardinalDirection": "South",
  "displayName": "19th Street (South side, 2701-2799)",
  "rules": [
    {
      "type": "street-sweeping",
      "description": "Street Cleaning Friday 12:00 AM-6:00 AM",
      "day": "Fri",
      "startTime": "0",
      "endTime": "6",
      "blockside": "South",
      "limits": "York St  -  Bryant St",
      "activeDays": [5],
      "startTimeMin": 0,
      "endTimeMin": 360
    }
  ],
  "schedules": []
}
```

### Segment 2: Right Side (R) 🚨
```json
{
  "cnn": "961000",
  "side": "R",
  "streetName": "19TH ST",
  "fromStreet": null,
  "toStreet": null,
  "fromAddress": "2700",
  "toAddress": "2798",
  "cardinalDirection": null,
  "displayName": null,
  "rules": [],
  "schedules": []
}
```

**⚠️ MISSING DATA**: Manually verified that this segment should have:
- **Cardinal Direction**: "North"
- **Street Cleaning**: Thursday 12:00 AM - 6:00 AM
- **From/To Streets**: York St - Bryant St
- This data is **missing from the Socrata dataset**

---

## 5. Verified Ground Truth vs Dataset

| Attribute | Left Side (L) | Right Side (R) |
|-----------|---------------|----------------|
| **Cardinal Direction** | South ✅ | North ❌ (missing) |
| **Street Cleaning Day** | Friday ✅ | Thursday ❌ (missing) |
| **Street Cleaning Time** | 12:00 AM - 6:00 AM ✅ | 12:00 AM - 6:00 AM ❌ (missing) |
| **From/To Streets** | York St - Bryant St ✅ | Should be York St - Bryant St ❌ |
| **Parking Regulations** | None ✅ | None ✅ |
| **In Socrata Dataset** | ✅ Yes | ❌ No |
| **Physically Exists** | ✅ Yes | ✅ Yes |

---

## 6. Key Findings

### ✅ What's Working
1. **Active Streets data** is complete and accurate
2. **Street cleaning** is properly matched to the LEFT side (South)
3. **Address ranges** are correctly assigned to each side
4. **Geometry** is accurate and matches between datasets
5. **Display name** is generated correctly for the left side
6. **Parking regulations** correctly show as none (verified accurate)

### 🚨 Critical Data Quality Issue

#### **MISSING STREET CLEANING RECORD IN SOCRATA DATASET**
- **Problem**: Right side (R) street cleaning is **missing from the Socrata dataset**
- **Dataset ID**: `yhqp-riqs` (Street Cleaning Schedules)
- **Missing Record Details**:
  - CNN: 961000
  - Side: R (cnnrightleft)
  - Day: Thursday
  - Time: 12:00 AM - 6:00 AM
  - Cardinal: North
  - Limits: York St - Bryant St
- **Verification Method**: Manual visual inspection of street signs
- **Impact**: 
  - Users won't see street cleaning for the north side
  - Incorrect parking guidance (missing critical restriction)
  - Potential parking tickets for users relying on app
  - Data completeness issue affects user trust
- **Root Cause**: Socrata dataset is incomplete for CNN 961000R
- **Action Required**: Report to SFMTA data team

#### Issue 2: Right Side Missing Cardinal Direction
- **Problem**: Right side (R) has no `cardinalDirection` or `displayName`
- **Cause**: Missing street cleaning schedule (see above)
- **Impact**: Display name cannot be generated without cardinal direction
- **Verified Cardinal**: North (opposite of South)
- **Solution**: Implement cardinal direction inference from geometry

#### Issue 3: Right Side Missing From/To Streets
- **Problem**: Right side has `fromStreet: null` and `toStreet: null`
- **Cause**: Street limits only come from street cleaning schedules
- **Impact**: Less context for users about segment boundaries
- **Solution**: Copy from Active Streets data (f_st/t_st fields)

---

## 7. Data Quality Assessment

### Completeness
- **Active Streets**: ✅ 100%
- **Street Cleaning**: 🚨 **50% (MISSING RIGHT SIDE DATA)**
  - Left side (South): ✅ Present in dataset
  - Right side (North): ❌ **Missing from dataset** (verified to exist physically)
- **Parking Regulations**: ✅ 0% (verified correct - none exist)
- **Parking Meters**: ✅ 0% (verified correct - none exist)

### Accuracy
- **Geometry matching**: ✅ Excellent
- **Address ranges**: ✅ Correct
- **Cardinal direction**: ⚠️ Only available for left side (right side missing from source)
- **Time parsing**: ✅ Correct (0-6 = midnight to 6am)
- **Parking regulations**: ✅ Correctly shows none

### Consistency
- **CNN matching**: ✅ Perfect (direct match)
- **Side determination**: ✅ Correct (L/R properly assigned)
- **Display formatting**: ⚠️ Incomplete for right side (due to missing source data)

---

## 8. Recommendations

### 🚨 Critical Actions

#### 1. Report Data Quality Issue to SFMTA
- **Dataset**: Street Cleaning Schedules (yhqp-riqs)
- **Issue**: Missing record for CNN 961000R
- **Details**: 
  - Missing: Thursday 12:00 AM - 6:00 AM, North side
  - Present: Friday 12:00 AM - 6:00 AM, South side (961000L)
- **Impact**: User safety and parking compliance

#### 2. Implement Data Validation Checks
- Flag CNNs where only one side has street cleaning
- Alert when opposite sides have different days (common pattern)
- Create report of potentially missing records
- Run validation across entire dataset to find similar issues

### Immediate Technical Actions

#### 1. Implement Cardinal Direction Inference
- Use geometry analysis to determine north/south/east/west
- Or use opposite of known side (if South is L, then North is R)
- For 961000: L=South, therefore R=North
- Apply to all segments missing cardinal direction

#### 2. Copy Street Limits from Active Streets
- Use `f_st` and `t_st` fields as fallback
- Ensures all segments have from/to street context
- For 961000R: Use "YORK ST" and "BRYANT ST" from Active Streets

#### 3. Generate Synthetic Display Names
- Create display names even without street cleaning data
- Use inferred cardinal direction
- Format: "19th Street (North side, 2700-2798)"

### Long-term Improvements

1. **Create Data Quality Monitoring Dashboard**
   - Track missing records over time
   - Alert on new data quality issues
   - Monitor dataset completeness metrics

2. **Establish Feedback Loop with SFMTA**
   - Regular data quality reports
   - Process for reporting and tracking corrections
   - Automated validation on data updates

3. **Add Synthetic Data Generation**
   - Infer missing cardinal directions from geometry
   - Generate display names for all segments
   - Create fallback values for missing metadata

4. **Implement User Feedback Mechanism**
   - Allow users to report missing/incorrect data
   - Crowdsource data validation
   - Build confidence scores based on verification

---

## 9. Files Generated

1. **streets_961000.json** - Raw Active Streets data
2. **cleaning_961000.json** - Raw street cleaning schedules (only left side)
3. **sample_regulations.json** - Sample parking regulations (for reference)
4. **INVESTIGATION_SUMMARY.md** - This comprehensive analysis document
5. **inspect_cnn_961000.py** - Reusable investigation script

---

## 10. Related Code References

- [`ingest_data_cnn_segments.py`](../ingest_data_cnn_segments.py) - Main ingestion script
- [`models.py`](../models.py) - StreetSegment data model (line 26)
- [`display_utils.py`](../display_utils.py) - Display name generation
- [`match_regulation_to_segment()`](../ingest_data_cnn_segments.py:92) - Spatial matching logic
- [`generate_display_messages()`](../display_utils.py) - Display formatting
- [`extract_street_limits()`](../ingest_data_cnn_segments.py:212) - Street limit parsing

---

## 11. Next Steps

### For Development Team
1. ✅ Complete investigation (DONE)
2. ⏭️ Create data quality issue report
3. ⏭️ Implement cardinal direction inference
4. ⏭️ Create validation script to find similar issues
5. ⏭️ Update documentation across project

### For SFMTA Data Team
1. ⏭️ Review missing record for CNN 961000R
2. ⏭️ Add missing street cleaning schedule to dataset
3. ⏭️ Audit dataset for similar missing records
4. ⏭️ Establish data quality validation process

### For Product Team
1. ⏭️ Decide on user-facing messaging for incomplete data
2. ⏭️ Consider adding "Report an issue" feature
3. ⏭️ Plan for handling data quality issues in UI

---

## Conclusion

CNN 961000 reveals a **critical data quality issue** in the SFMTA Socrata dataset that has significant implications for user safety and app reliability.

### Summary of Findings

| Aspect | Status | Notes |
|--------|--------|-------|
| **Active Streets** | ✅ Complete | Full coverage, accurate data |
| **Left Side Cleaning** | ✅ Complete | Friday 12AM-6AM, South side |
| **Right Side Cleaning** | 🚨 **Missing** | Should be Thursday 12AM-6AM, North side |
| **Parking Regulations** | ✅ Verified None | Correctly shows no regulations |
| **Data Quality** | ❌ **Issue Found** | Missing critical safety information |

### Impact Assessment

**User Impact**: HIGH
- Users parking on north side won't see Thursday cleaning restriction
- Risk of parking tickets
- Undermines trust in app accuracy

**Data Quality Impact**: MEDIUM
- Indicates potential systemic issue
- Unknown how many other records are missing
- Requires dataset-wide validation

**Technical Impact**: LOW
- System handles missing data gracefully
- Can implement workarounds (cardinal inference)
- No system failures or crashes

### Action Required

This finding requires immediate attention:
1. **Report to SFMTA** - Missing data affects public safety
2. **Implement validation** - Find and document similar issues
3. **Add inference logic** - Mitigate impact of missing data
4. **Update documentation** - Inform team of data quality concerns

---

**Investigation Date**: December 4, 2025  
**Investigator**: Roo (AI Assistant)  
**Verification Method**: Manual visual inspection + dataset analysis  
**Status**: Complete - Action items identified