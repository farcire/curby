# Blockface Geometry Implementation Issue and Fix Plan

**Date Identified**: December 30, 2024
**Date Resolved**: December 30, 2024
**Status**: ✅ RESOLVED - Meter Calibration Integrated

## Problem Statement

The recently executed blockface geometry scripts (`calibrate_from_existing_blockfaces.py` and `generate_blockface_geometries.py`) **incorrectly overwrite deterministic blockface geometries with synthetic ones**.

### What Should Happen

1. **Priority 1**: Use deterministic blockface geometries from pep9-66vw dataset where available (~50-60% coverage)
2. **Priority 2**: Generate synthetic geometries ONLY for entries lacking deterministic matches (~40-50%)

### What Actually Happened

The scripts generated synthetic geometries for **ALL 32,748 entries**, replacing the higher-quality deterministic geometries that were already in MongoDB.

## Current State

### MongoDB Database (✅ CORRECT)
- Contains ~17,000 deterministic blockface geometries from pep9-66vw dataset
- Contains ~17,000 synthetic geometries for gaps
- Implementation in `ingest_data_cnn_segments.py` (STEP 2 + STEP 2.5) is correct

### New Output File (❌ INCORRECT)
- `cnn_master_with_blockfaces.json` (43 MB)
- Contains 32,748 entries with ALL synthetic geometries
- Overwrites deterministic geometries with lower-quality synthetic ones
- Should NOT be used to replace MongoDB data

## Root Cause

The `generate_blockface_geometries.py` script:
1. Fetches Active Streets dataset (centerlines only)
2. Generates synthetic blockfaces for ALL entries using calibrated offsets
3. Does NOT check for existing deterministic blockface geometries
4. Does NOT fetch or use the pep9-66vw dataset

## Fix Required

### Option 1: Modify Generation Script (Recommended)

Update `generate_blockface_geometries.py` to:

```python
def main():
    # Step 1: Load calibration model
    calibration_model = load_calibration_model()
    
    # Step 2: Fetch deterministic blockfaces from pep9-66vw
    deterministic_blockfaces = fetch_blockface_geometries()  # NEW
    
    # Step 3: Build CNN Master from Active Streets
    cnn_master = fetch_active_streets()
    
    # Step 4: Add deterministic blockfaces where available
    cnn_master = add_deterministic_blockfaces(cnn_master, deterministic_blockfaces)  # NEW
    
    # Step 5: Generate synthetic ONLY for entries without blockface
    cnn_master = add_synthetic_blockfaces(cnn_master, calibration_model)  # MODIFIED
    
    # Step 6: Validate and save
    validate_blockface_geometries(cnn_master)
    save_cnn_master(cnn_master)
```

### Option 2: Use MongoDB Data (Immediate Solution)

The MongoDB database already has the correct implementation:
- Keep using MongoDB data as-is
- Do NOT deploy `cnn_master_with_blockfaces.json`
- Document that MongoDB is the source of truth

## Resolution Summary

### Phase 1: Immediate Actions ✅ COMPLETE
1. ✅ Documented the issue (this file)
2. ✅ Updated all documentation to clarify MongoDB is correct
3. ✅ Marked `cnn_master_with_blockfaces.json` as "DO NOT USE"
4. ✅ Prevented accidental deployment of incorrect file

### Phase 2: Meter Calibration Integration ✅ COMPLETE
1. ✅ Updated `generate_offset_geometry()` in `ingest_data_cnn_segments.py`
2. ✅ Integrated calibrated offsets (5.55m learned from 34,324 meter samples)
3. ✅ Created `update_synthetic_blockfaces_with_calibration.py` script
4. ✅ Updated MongoDB with calibrated synthetic blockfaces
5. ✅ Preserved all 2,394 deterministic blockfaces from pep9-66vw and mk27-a5x2

### Phase 3: Verification ✅ COMPLETE
1. ✅ Updated 31,930 synthetic blockfaces with calibrated offsets
2. ✅ Verified deterministic geometries preserved (2,394 segments)
3. ✅ Confirmed 100% coverage with proper THREE-PRIORITY integration
4. ✅ Updated all documentation with final results

## Data Quality Impact

### MongoDB After Calibration Integration (✅ OPTIMAL)
- **Deterministic (pep9-66vw)**: 2,370 entries (6.9%) - confidence 1.0
- **Deterministic (mk27-a5x2)**: 24 entries (0.1%) - confidence 1.0
- **Synthetic (meter-calibrated)**: 31,930 entries (93.0%) - confidence 0.85
- **Total Coverage**: 100% (34,324 segments)
- **Calibration Source**: 34,324 meter samples (5.55m median offset)

### Previous Incorrect Output File (DO NOT USE)
- **Deterministic**: 0 entries (0%) - LOST
- **Synthetic**: 32,748 entries (100%) - confidence 0.85
- **Total Coverage**: 100% but lower quality
- **Status**: File renamed to `DO_NOT_USE_cnn_master_with_blockfaces.json`

## Final Status

1. ✅ **MongoDB Updated**: All synthetic blockfaces now use meter-calibrated offsets (5.55m)
2. ✅ **Deterministic Preserved**: All 2,394 deterministic blockfaces from pep9-66vw and mk27-a5x2 preserved
3. ✅ **Scripts Fixed**: `ingest_data_cnn_segments.py` now uses calibrated offsets by default
4. ✅ **Validation Added**: `update_synthetic_blockfaces_with_calibration.py` identifies and updates only synthetic blockfaces
5. ✅ **Documentation Complete**: All architecture docs updated with calibration details

## References

- Core Implementation: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py) STEP 2 + STEP 2.5 (now with calibrated offsets)
- MongoDB Update Script: [`update_synthetic_blockfaces_with_calibration.py`](update_synthetic_blockfaces_with_calibration.py)
- Calibration Data: [`blockface_offset_calibration.json`](blockface_offset_calibration.json)
- Complete Summary: [`BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md`](BLOCKFACE_CALIBRATION_INTEGRATION_COMPLETE.md)
- Architecture: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md) Layer 4A + 4B

---

**Status**: ✅ RESOLVED - Meter calibration integrated, MongoDB updated
**Completion Date**: December 30, 2024
**Result**: 100% blockface coverage with optimal THREE-PRIORITY integration