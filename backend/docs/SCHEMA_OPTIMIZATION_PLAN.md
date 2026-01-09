# MongoDB Schema Optimization Plan
## January 1, 2026

## Issues Identified

### 1. Wrong Street Name Field
**Current**: Using `streetname` from Active Streets
**Should Use**: `street_name_gc` (geocoded street name)
**Location**: `ingest_data_cnn_segments.py` lines 471, 481

### 2. Unnecessary Display Fields
**Current MongoDB has**:
- `displayName` - "Baker Street (West side, 951-1099)"
- `displayNameShort` - "Baker Street (West side)"
- `displayAddressRange` - "951-1099"
- `displayCardinal` - "West side"

**Problem**: These are redundant - frontend can format from raw fields

### 3. Modal Content Duplication
**Current**: `modalContent` object duplicates data already in MongoDB
**Problem**: Adds storage overhead and processing time

## Optimal MongoDB Schema

### Keep (Essential Raw Data):
```json
{
  "cnn": "2615000",
  "side": "L",
  "streetName": "BAKER ST",              // ← FIX: Use street_name_gc
  "cardinalDirection": "West",
  "fromAddress": "951",
  "toAddress": "1099",
  "fromStreet": "Pinar Ln",
  "toStreet": "Terra Vista Ave",
  "centerlineGeometry": {...},
  "blockfaceGeometry": {...},
  "rules": [
    {
      "type": "street-sweeping",
      "description": "Street Cleaning Wednesday 9:00 AM-11:00 AM",  // ← Keep (complex)
      "activeDays": [2],
      "startTimeMin": 540,
      "endTimeMin": 660,
      "blockside": "West"
    }
  ],
  "schedules": [],
  "zip_code": "94115",
  "layer": "STREETS"
}
```

### Remove (Redundant):
- `displayName` - Frontend formats as: `${streetName} (${cardinalDirection}, ${fromAddress}-${toAddress})`
- `displayNameShort` - Frontend formats as: `${streetName} (${cardinalDirection})`
- `displayAddressRange` - Frontend formats as: `${fromAddress}-${toAddress}`
- `displayCardinal` - Frontend formats as: `${cardinalDirection} side`
- `modalContent` - Frontend formats from raw fields

## Implementation Changes

### 1. Update Ingestion Script (`ingest_data_cnn_segments.py`)

**Lines 471, 481** - Change:
```python
"streetName": row.get("streetname"),  # WRONG
```
To:
```python
"streetName": row.get("street_name_gc"),  # CORRECT - geocoded name
```

**Lines 922-939** - Remove display field generation:
```python
# DELETE THIS ENTIRE SECTION (lines 922-939)
msgs = generate_display_messages(...)
segment["displayName"] = msgs["display_name"]
segment["displayNameShort"] = msgs["display_name_short"]
segment["displayAddressRange"] = msgs["display_address_range"]
segment["displayCardinal"] = msgs["display_cardinal"]
modal_content = format_segment_for_modal(segment)
segment["modalContent"] = modal_content
```

### 2. Update Frontend (`BlockfaceDetail.tsx`)

**Current (lines 56-66)** - Looking for modalContent:
```typescript
const modalContent = blockface.modalContent || {
  location_text: `${cleanStreetName(blockface.streetName)}...`,
  ...
};
```

**Change to** - Use raw fields directly:
```typescript
// Location line
const locationText = blockface.fromAddress && blockface.toAddress
  ? `${cleanStreetName(blockface.streetName)} (${blockface.cardinalDirection}, ${blockface.fromAddress}-${blockface.toAddress})`
  : `${cleanStreetName(blockface.streetName)} (${blockface.cardinalDirection})`;

// Cross streets line  
const crossStreetsText = blockface.fromStreet && blockface.toStreet
  ? `${blockface.fromStreet} → ${blockface.toStreet}`
  : null;

// Rules - use pre-computed descriptions
const rules = blockface.rules.map(r => r.description);
```

## Benefits

### Storage Savings:
- Remove 4 redundant string fields per segment
- Remove modalContent object per segment
- ~40% reduction in document size

### Processing Time:
- Eliminate `generate_display_messages()` call (lines 922-930)
- Eliminate `format_segment_for_modal()` call (lines 938-939)
- ~30% faster ingestion

### Maintainability:
- Single source of truth for each data point
- Frontend owns simple presentation logic
- Backend owns complex logic (rule normalization)

## Migration Steps

1. Update `ingest_data_cnn_segments.py`:
   - Fix streetname field (use street_name_gc)
   - Remove display field generation (lines 922-939)

2. Update `BlockfaceDetail.tsx`:
   - Remove modalContent dependency
   - Format from raw fields directly

3. Re-run ingestion:
   ```bash
   cd backend
   python ingest_data_cnn_segments.py
   ```

4. Test frontend modal display

5. Verify performance improvement

## Field Reference

### Active Streets Dataset Fields:
- `street_name_gc` - Geocoded street name (CORRECT)
- `streetname` - Raw street name (WRONG - inconsistent)
- `cnn` - Centerline Network ID
- `lf_fadd`, `lf_toadd` - Left side address range
- `rt_fadd`, `rt_toadd` - Right side address range
- `line` - Centerline geometry

### Street Cleaning Dataset Fields:
- `blockside` - Cardinal direction (North, South, East, West)
- `limits` - Cross street limits ("Pinar Ln  -  Terra Vista Ave")
- `cnn` - Centerline Network ID
- `cnnrightleft` - Side (L or R)