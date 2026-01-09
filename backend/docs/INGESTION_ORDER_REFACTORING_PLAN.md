# Ingestion Order Refactoring Plan

## Problem
Current implementation loads meter schedules FIRST, then matches them to meters. This is backwards according to the architecture specification.

**Current Order (WRONG)**:
1. Streets ✓
2. Blockfaces
3. Parking Regulations  
4. **Load Schedules → Build lookup → Load Meters → Attach schedules**
5. Street Sweeping

**Correct Order** (per INGESTION_ARCHITECTURE_SPECIFICATION.md):
1. Streets ✓
2. Intersections & Permutations
3. **Parking Meters** (match to CNN+side)
4. Blockfaces with Meters
5. Blockfaces (deterministic match)
6. Synthetic Blockface Generation
7. **Meter Operating Schedules** (match TO meters via post_id)
8. Meter Rates
9. Non-Parking Regulations
10. Street Sweeping

## Refactoring Steps

### Step 1: Reorganize Step Numbers
- Current Step 2 (Blockfaces) → New Step 5
- Current Step 2.5 (Synthetic) → New Step 6
- Current Step 3 (Regulations) → New Step 9
- Current Step 4 (Meters+Schedules) → Split into Step 3 (Meters) and Step 7 (Schedules)
- Current Step 5 (Sweeping) → New Step 10

### Step 2: Split Meter/Schedule Logic

**New Step 3 - Load Meters Only**:
```python
# Load metered blockfaces for CNN+side mapping
metered_blockfaces_df = fetch_data_as_dataframe(METERED_BLOCKFACES_ID, app_token)
blockface_to_cnn_side = {}  # Build lookup

# Load meters
meters_df = fetch_data_as_dataframe(METERS_DATASET_ID, app_token)

# Match meters to segments (CNN+side)
for meter_row in meters_df:
    # Match via blockface_id or CNN+address
    # Add meter to segment WITHOUT schedules
    segment["meters"].append({
        "post_id": post_id,
        "cap_color": cap_color,
        "location": {...},
        "schedules": []  # Empty initially
    })
```

**New Step 7 - Load Schedules and Attach**:
```python
# Load meter schedules
schedules_df = fetch_data_as_dataframe(METER_SCHEDULES_DATASET_ID, app_token)

# Build lookup by post_id
schedules_by_post = {}
for schedule_row in schedules_df:
    post_id = schedule_row.get("post_id")
    schedules_by_post[post_id].append({...})

# Iterate through ALL segments and attach schedules to meters
for segment in all_segments:
    for meter in segment.get("meters", []):
        post_id = meter["post_id"]
        meter_schedules = schedules_by_post.get(post_id, [])
        meter["schedules"] = prioritize_meter_schedules(meter_schedules)
```

### Step 3: Update Checkpoint Numbers
- Checkpoint "2" → "5" (blockfaces)
- Checkpoint "2.5" → "6" (synthetic)
- Checkpoint "3" → "9" (regulations)
- Checkpoint "4" → Split into "3" (meters) and "7" (schedules)
- Checkpoint "5" → "10" (sweeping)

### Step 4: Add Missing Steps
- Step 2: Intersection Permutations (future)
- Step 4: Blockfaces with Meters (already have this data)
- Step 8: Meter Rates (future)

## Implementation Strategy

Given the complexity, we have two options:

### Option A: Create New File
Create `ingest_data_cnn_segments_v2.py` with correct order, test it, then replace original.

**Pros**: 
- Safe - keeps working version
- Can test thoroughly before switching
- Easy to compare differences

**Cons**:
- Temporary duplication

### Option B: Refactor In-Place
Modify existing file step by step with careful testing.

**Pros**:
- No duplication
- Single source of truth

**Cons**:
- Riskier - could break working code
- Harder to rollback

## Recommendation

**Use Option A**: Create `ingest_data_cnn_segments_v2.py` with correct architecture, test it, then replace the original once verified.

## Key Changes Summary

1. **Step 3 (NEW)**: Load meters, match to CNN+side, store WITHOUT schedules
2. **Step 4 (NEW)**: Process metered blockfaces metadata
3. **Step 5 (MOVED)**: Blockface geometries (was Step 2)
4. **Step 6 (MOVED)**: Synthetic blockfaces (was Step 2.5)
5. **Step 7 (NEW)**: Load schedules, attach TO meters via post_id
6. **Step 8 (FUTURE)**: Meter rates
7. **Step 9 (MOVED)**: Parking regulations (was Step 3)
8. **Step 10 (MOVED)**: Street sweeping (was Step 5)

## Testing Plan

1. Run with `--force-restart` on test database
2. Verify meter count matches
3. Verify schedule attachment (should be >0% not 100% NULL)
4. Verify all 4 schedules per meter are kept
5. Compare final segment count with original
6. Spot-check specific segments for correctness

## Timeline

- Document creation: ✓ Complete
- Create v2 file: 30-45 minutes
- Test run: 30-45 minutes
- Verification: 15 minutes
- **Total**: ~2 hours

## Date
January 4, 2026 (PST)