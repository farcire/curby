# Address Range Implementation for CNN Segments

## Overview
We've successfully integrated address range data from the Active Streets dataset into our CNN-based street segment model. Each segment now stores the address ranges for its respective side (Left or Right).

## Data Source
**Dataset**: Active Streets (3psu-pn9h)
**Fields Used**:
- `lf_fadd` - Left side "from" address
- `lf_toadd` - Left side "to" address  
- `rt_fadd` - Right side "from" address
- `rt_toadd` - Right side "to" address

## Implementation Details

### 1. Model Updates (`backend/models.py`)
Added two new fields to the `StreetSegment` model:
```python
fromAddress: Optional[str] = None  # Starting address (lf_fadd for L, rt_fadd for R)
toAddress: Optional[str] = None    # Ending address (lf_toadd for L, rt_toadd for R)
```

### 2. Ingestion Updates (`backend/ingest_data_cnn_segments.py`)
Modified segment creation to populate address ranges based on side:

**For LEFT segments:**
- `fromAddress` = `lf_fadd` (left from address)
- `toAddress` = `lf_toadd` (left to address)

**For RIGHT segments:**
- `fromAddress` = `rt_fadd` (right from address)
- `toAddress` = `rt_toadd` (right to address)

## Example Data Structure

### Sample CNN: 799000 (17th Street)
From the Active Streets inspection:
```json
{
  "cnn": "799000",
  "lf_fadd": "3401",
  "lf_toadd": "3449",
  "rt_fadd": "3400",
  "rt_toadd": "3440",
  "street": "17TH",
  "st_type": "ST"
}
```

### Resulting Segments in Database

**Left Segment (CNN: 799000, Side: L)**
```json
{
  "cnn": "799000",
  "side": "L",
  "streetName": "17TH ST",
  "fromAddress": "3401",
  "toAddress": "3449",
  "centerlineGeometry": {...},
  "rules": [...],
  "schedules": [...]
}
```

**Right Segment (CNN: 799000, Side: R)**
```json
{
  "cnn": "799000",
  "side": "R",
  "streetName": "17TH ST",
  "fromAddress": "3400",
  "toAddress": "3440",
  "centerlineGeometry": {...},
  "rules": [...],
  "schedules": [...]
}
```

## Benefits

1. **Address-Based Queries**: Can now query segments by address range
2. **User-Friendly Display**: Can show "3401-3449 17th St (Left side)" to users
3. **Address Validation**: Can verify if a specific address falls within a segment's range
4. **RPP Integration**: Address ranges enable better matching with RPP parcels dataset
5. **Complete Coverage**: Every CNN segment now has its address range stored

## Usage in API

The address ranges are now available in API responses and can be used for:
- Displaying address ranges to users
- Validating user-entered addresses
- Matching addresses to specific street segments
- Integrating with address-based datasets (like RPP parcels)

## Next Steps

To use this data in the API, you may want to:
1. Add address range fields to API response models
2. Implement address-based search/filtering
3. Use address ranges for RPP area lookups
4. Display address ranges in the frontend UI

## Files Modified

1. `backend/models.py` - Added `fromAddress` and `toAddress` fields
2. `backend/ingest_data_cnn_segments.py` - Populated address ranges during ingestion
3. `backend/inspect_active_streets.py` - Script to inspect Active Streets dataset structure
4. `backend/active_streets_inspection.txt` - Output showing available fields

## Re-ingestion Required

To populate these fields in the database, you'll need to re-run the ingestion:
```bash
cd backend
python3 ingest_data_cnn_segments.py
```

This will create fresh segments with address ranges included.