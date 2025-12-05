# Backend Data Model Update

**Date:** December 5, 2025  
**Purpose:** Support AI-powered parking regulation interpretation system

## Overview

The backend data model has been updated to support the LLM interpretation workflow described in [`UNIQUE_REGULATIONS_EXTRACTION_PLAN.md`](../UNIQUE_REGULATIONS_EXTRACTION_PLAN.md) and [`PARKING_REGULATION_INTERPRETATION_SYSTEM.md`](PARKING_REGULATION_INTERPRETATION_SYSTEM.md).

## New Models

### 1. `RegulationConditions`
Structured representation of parking regulation conditions:
- `days`: List of day names (e.g., `['Monday', 'Tuesday']`)
- `hours`: Time range string (e.g., `'9AM-6PM'`)
- `time_limit_minutes`: Integer time limit (e.g., `120` for 2 hours)
- `exceptions`: List of exceptions (e.g., `['RPP exempt', 'Holidays']`)

### 2. `RegulationInterpretation`
AI-interpreted parking regulation in plain language:
- `action`: Type of regulation (`'allowed'`, `'prohibited'`, `'time-limited'`, `'restricted'`, `'permit-required'`)
- `summary`: Plain English summary for users
- `severity`: Impact level (`'critical'`, `'high'`, `'medium'`, `'low'`)
- `conditions`: Structured conditions (see above)
- `details`: Additional context
- `confidence_score`: Judge's confidence (0.0-1.0)
- `judge_verified`: Whether judge approved
- `notes`: Additional notes

### 3. `SourceRegulationFields`
Raw fields from SFMTA parking regulations dataset:
- Maps directly to fields in the `parking_regulations` collection
- Includes: `regulation`, `days`, `hours`, `hrlimit`, `rpparea1`, etc.

### 4. `ParkingRule` (Updated)
Enhanced to support AI interpretation:
- `type`: Rule type (e.g., `'parking-regulation'`, `'street-sweeping'`)
- `source_text`: Original regulation text
- `source_fields`: Raw source data
- `interpreted`: AI-interpreted data (optional)
- `interpretation_ref`: Reference to cached interpretation by `unique_id`
- Legacy fields maintained for backward compatibility

### 5. `CachedInterpretation`
Cached interpretation stored in MongoDB for O(1) lookup:
- `unique_id`: MD5 hash of source field combination
- `source_fields`: Original regulation fields
- `interpreted`: AI-generated interpretation
- `metadata`: Usage stats, timestamps, verification status

### 6. `GoldenDatasetEntry`
Entry in the golden dataset for LLM evaluation:
- Matches structure in [`golden_dataset_template.json`](golden_dataset_template.json)
- Used for training and validation

### 7. `WorkerOutput` & `JudgeEvaluation`
Support for Worker → Judge LLM pipeline:
- `WorkerOutput`: Initial interpretation from worker LLM
- `JudgeEvaluation`: Quality assessment from judge LLM
- `ProcessedInterpretation`: Combined result with metadata

## Updated Models

### `Blockface` (No Breaking Changes)
- Maintains backward compatibility
- `rules` field now uses enhanced `ParkingRule` model
- Existing API responses remain unchanged

### `StreetSegment` (No Changes Required)
- Already uses flexible `rules: List[Dict]` structure
- Can accommodate new interpretation fields without schema changes

## Database Schema Changes

### New Collection: `regulation_interpretations`
```javascript
{
  "_id": "abc123def456...",  // unique_id (MD5 hash)
  "source_fields": {
    "regulation": "TIME LIMITED",
    "days": "M-F",
    "hours": "0800-1800",
    "hrlimit": 2,
    "rpparea1": "W"
  },
  "interpreted": {
    "action": "time-limited",
    "summary": "2 Hour Parking Mon-Fri 8am-6pm except Permit W",
    "severity": "medium",
    "conditions": {
      "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "hours": "8am-6pm",
      "time_limit_minutes": 120,
      "exceptions": ["Permit W"]
    },
    "details": "",
    "confidence_score": 0.95,
    "judge_verified": true,
    "notes": ""
  },
  "metadata": {
    "usage_count": 143,
    "created_at": "2025-11-30T23:00:00Z",
    "model": "gemini-2.0-flash-exp",
    "human_verified": true,
    "last_updated": "2025-11-30T23:30:00Z"
  }
}
```

### Updated Collection: `parking_regulations`
Add new field:
```javascript
{
  // ... existing fields ...
  "interpretation_ref": "abc123def456..."  // NEW: Reference to cached interpretation
}
```

## API Response Format

### Current Format (Maintained)
```json
{
  "id": "797000_L",
  "rules": [
    {
      "type": "parking-regulation",
      "description": "2 HR PARKING 8AM-6PM MON-FRI EXCEPT PERMIT W"
    }
  ]
}
```

### Enhanced Format (New)
```json
{
  "id": "797000_L",
  "rules": [
    {
      "type": "parking-regulation",
      "source_text": "2 HR PARKING 8AM-6PM MON-FRI EXCEPT PERMIT W",
      "source_fields": {
        "regulation": "TIME LIMITED",
        "days": "M-F",
        "hours": "0800-1800",
        "hrlimit": "2",
        "rpparea1": "W"
      },
      "interpreted": {
        "action": "time-limited",
        "summary": "2 Hour Parking Mon-Fri 8am-6pm except Permit W",
        "severity": "medium",
        "conditions": {
          "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
          "hours": "8am-6pm",
          "time_limit_minutes": 120,
          "exceptions": ["Permit W"]
        },
        "confidence_score": 0.95,
        "judge_verified": true
      },
      "interpretation_ref": "abc123def456..."
    }
  ]
}
```

## Migration Path

### Phase 1: Model Update (✅ Complete)
- Updated Pydantic models in `models.py`
- Backward compatible with existing data

### Phase 2: Cache Population (Next)
1. Run `extract_unique_regulations.py` to identify ~292 unique combinations
2. Process through Worker → Judge pipeline using `process_unique_interpretations.py`
3. Store results in `regulation_interpretations` collection

### Phase 3: Link Regulations (Next)
1. Run `link_regulations_to_interpretations.py`
2. Add `interpretation_ref` field to all parking regulations

### Phase 4: API Integration (Next)
1. Update `main.py` to load interpretation cache at startup
2. Modify `/api/v1/blockfaces` endpoint to include interpreted data
3. Frontend can optionally use `interpreted.summary` for display

## Benefits

1. **Performance**: O(1) lookup instead of LLM call per regulation
2. **Cost**: $0.10 one-time vs $60/month for 1K users
3. **Consistency**: Same regulation always gets same interpretation
4. **Quality**: Judge-verified interpretations with confidence scores
5. **Backward Compatible**: Existing API responses unchanged

## Frontend Integration

The frontend TypeScript types in `frontend/src/types/parking.ts` already support this structure through the flexible `ParkingRule` interface. No breaking changes required.

## Next Steps

1. ✅ Update data models (Complete)
2. ⏳ Extract unique regulation combinations
3. ⏳ Process through LLM pipeline
4. ⏳ Populate interpretation cache
5. ⏳ Update API endpoints
6. ⏳ Test end-to-end workflow

## References

- [`UNIQUE_REGULATIONS_EXTRACTION_PLAN.md`](../UNIQUE_REGULATIONS_EXTRACTION_PLAN.md) - Complete implementation plan
- [`PARKING_REGULATION_INTERPRETATION_SYSTEM.md`](PARKING_REGULATION_INTERPRETATION_SYSTEM.md) - System architecture
- [`golden_dataset_template.json`](golden_dataset_template.json) - Golden dataset structure
- [`GEMINI_FREE_TIER_STRATEGY.md`](../GEMINI_FREE_TIER_STRATEGY.md) - Cost optimization strategy