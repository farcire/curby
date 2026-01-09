# MongoDB Collection Architecture - Final Implementation

**Date**: January 2, 2026  
**Status**: ✅ PRODUCTION READY

---

## Overview

The Curby parking application uses a **single-collection architecture** for street segment data, optimized for performance and maintainability.

---

## Production Collections

### 1. `street_segments` (PRIMARY COLLECTION)

**Purpose**: Complete street segment data with parking regulations, meters, and schedules

**Document Count**: 34,324 (17,162 CNNs × 2 sides)

**Schema**:
```javascript
{
  _id: ObjectId,
  cnn: String,                    // Centerline Network Node ID
  side: String,                   // "L" or "R"
  streetName: String,
  centerlineGeometry: GeoJSON,    // Street centerline
  blockfaceGeometry: GeoJSON,     // Parking edge (deterministic or synthetic)
  fromStreet: String,
  toStreet: String,
  fromAddress: String,
  toAddress: String,
  zip_code: String,
  layer: String,
  supervisor_district: String,
  cardinalDirection: String,      // N, S, E, W, NE, etc.
  
  // Parking regulations (non-metered)
  rules: [{
    type: String,                 // "parking-regulation", "street-sweeping"
    regulation: String,
    activeDays: [Number],         // [0-6] where 0=Sunday
    startTimeMin: Number,         // Minutes since midnight
    endTimeMin: Number,
    durationMinutes: Number,
    hasLimit: Boolean,
    displayDays: String,          // "M-F", "Daily", etc.
    displayTime: String,          // "9am-6pm"
    displayDuration: String,      // "2hr", "30min"
    description: String,          // Full display text
    permitArea: String,           // RPP area if applicable
    side: String
  }],
  
  // Metered parking
  meters: [{
    post_id: String,
    cap_color: String,            // Raw: "GREEN", "YELLOW", etc.
    cap_color_normalized: {       // Normalized cap color data
      canonical: {
        color: String,
        restriction: String,      // "GENERAL", "COMMERCIAL", etc.
        is_restricted: Boolean,
        vehicle_type: String
      },
      display: {
        restriction_text: String,
        user_eligible: Boolean
      }
    },
    location: {
      type: "Point",
      coordinates: [Number, Number]
    },
    schedules: [{                 // Prioritized: TOW > ALTERNATE > OP > PRE+FREE
      beginTime: String,
      endTime: String,
      rate: String,
      schedule_type: String       // "TOW", "ALTERNATE", "OP", "PRE", "FREE"
    }]
  }],
  
  // Blockface-level aggregations
  towScheduleAggregation: {
    has_tow: Boolean,
    all_have_tow: Boolean,
    tow_schedules: [Object],
    meters_with_tow: Number,
    meters_without_tow: Number,
    majority_rule: String,
    blockface_rule: String
  },
  
  capColorAggregation: {
    is_restricted: Boolean,
    restriction_type: String,
    eligible_meter_count: Number,
    ineligible_meter_count: Number,
    meter_count: Number,
    majority_rule: String,
    eligible_for_curby_user: Boolean,
    restriction_breakdown: Object
  },
  
  // Convenience flags
  eligibleForStandardUser: Boolean,
  blockfaceRestriction: String,
  hasHomogeneousTow: Boolean,
  hasHomogeneousCapColor: Boolean
}
```

**Indexes**:
- `{cnn: 1, side: 1}` (unique)
- `{centerlineGeometry: "2dsphere"}`

**Size**: ~566 bytes per document average

---

### 2. Supporting Collections (Raw Data)

These collections store raw SFMTA data for debugging and reference:

- **`streets`**: Raw Active Streets data (17,162 records)
- **`parking_regulations`**: Raw parking regulations (7,783 records)
- **`meter_schedules`**: Raw meter operating schedules (72,365 records)
- **`meters`**: Raw parking meter data (38,356 records)
- **`street_cleaning_schedules`**: Raw street cleaning data (37,878 records)
- **`street_nodes`**: Street network nodes (9,719 records)
- **`intersections`**: Intersection data (18,756 records)
- **`intersection_permutations`**: CNN-to-intersection mappings (21,046 records)

---

## Removed Collections

### `cnn_master_join` (OBSOLETE - DELETED)

**Why Removed**:
- Incomplete implementation (only 902 of 34,324 expected documents)
- Script `generate_cnn_master_complete.py` was never finished
- Redundant with `street_segments` collection
- Different schema that didn't match current architecture

**Deleted**: January 2, 2026

---

## Data Ingestion

**Script**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)

**Features**:
- ✅ Resumable with checkpoint system (gzip-compressed)
- ✅ Handles MongoDB timeouts (5min timeout, batch size 100, retry logic)
- ✅ 100% coverage (34,324 segments for 17,162 CNNs)
- ✅ TOW schedule detection (372 schedules detected)
- ✅ Manual override system for data corrections

**Checkpoint Steps**:
1. Create CNN segments from Active Streets
2. Add blockface geometries (deterministic)
2.5. Generate synthetic blockfaces (5.55m calibrated offset)
3. Match parking regulations (spatial + geometric)
4. Match meters with schedules (blockface-based)
5. Match street cleaning schedules (CNN + side)
5.4. Apply manual data overrides
5.5. Finalize segments
5.6. Aggregate blockface-level meter rules
5.7. Finalize cardinal directions
6. Upload to MongoDB

**Run Command**:
```bash
cd backend
python ingest_data_cnn_segments.py --resume
```

---

## Statistics

**Total Coverage**:
- 34,324 street segments (100%)
- 17,162 CNNs × 2 sides (L/R)

**Parking Data**:
- 22,574 segments with street sweeping (65.8%)
- 481 segments with parking regulations (1.4%)
- 3,763 segments with meters (11.0%)
  - 698 commercial vehicles only (18.6% of metered)
  - 372 with TOW schedules (9.9% of metered)
  - 3,065 standard parking available (81.4% of metered)

**Geometry**:
- 34,324 segments with blockface geometry (100%)
  - 2,370 deterministic from pep9-66vw (6.9%)
  - 24 deterministic from mk27-a5x2 (0.1%)
  - 31,930 synthetic with calibrated offset (93.0%)

---

## Frontend Integration

**Query Pattern**:
```javascript
// Get parking info for location
const segments = await db.street_segments.find({
  centerlineGeometry: {
    $near: {
      $geometry: { type: "Point", coordinates: [lon, lat] },
      $maxDistance: 50
    }
  }
}).toArray();

// All data is in one collection - no joins needed!
segments.forEach(segment => {
  // Access rules directly
  const regulations = segment.rules;
  
  // Access meters directly
  const meters = segment.meters;
  
  // Access aggregations directly
  const isTowZone = segment.towScheduleAggregation?.has_tow;
  const isEligible = segment.eligibleForStandardUser;
});
```

**Benefits**:
- ✅ Single query for all parking data
- ✅ No joins required
- ✅ Fast geospatial queries
- ✅ All display fields pre-computed
- ✅ Blockface-level aggregations ready

---

## Architecture Decisions

### Why Single Collection?

1. **Performance**: No joins needed, single query gets all data
2. **Simplicity**: One source of truth, easier to maintain
3. **Geospatial**: Efficient spatial queries on centerline geometry
4. **Completeness**: All related data co-located

### Why Not Pre-Compute Display Strings?

The current schema stores **canonical data** (days as numbers, times as minutes) rather than pre-computed display strings. This allows:

1. **Flexibility**: Frontend can format based on user preferences
2. **Smaller Size**: 40% reduction in storage
3. **Internationalization**: Easy to add multiple languages
4. **Dynamic Formatting**: Can change display logic without re-ingestion

Display formatting is handled by [`regulation_normalizer.py`](regulation_normalizer.py) which provides consistent formatting across all interfaces.

---

## References

- **Architecture**: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md)
- **Ingestion Script**: [`ingest_data_cnn_segments.py`](ingest_data_cnn_segments.py)
- **Display Formatting**: [`regulation_normalizer.py`](regulation_normalizer.py)
- **Rule Engine**: [`rule_engine.py`](rule_engine.py)
- **Data Quality**: [`DATA_QUALITY_LOG.md`](DATA_QUALITY_LOG.md)

---

**Document Version**: 1.0  
**Last Updated**: January 2, 2026  
**Status**: ✅ Production Ready