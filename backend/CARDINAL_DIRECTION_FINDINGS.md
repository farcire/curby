# Cardinal Direction & Address Range Findings

## Issue Summary
When displaying street segments like "18TH ST (L)", we need to show either:
1. Cardinal direction (N, S, E, W, etc.)
2. Address range (odd/even numbers)

## Current State - 18TH ST Example

### What We Have:
```json
{
  "streetName": "18TH ST",
  "side": "L",
  "fromStreet": "York St",
  "toStreet": "Bryant St",
  "fromAddress": null,  ❌ MISSING
  "toAddress": null,    ❌ MISSING
  "rules": [
    {
      "type": "street-sweeping",
      "day": "Thu",
      "startTime": "0",
      "endTime": "6",
      "side": "L",
      "cardinalDirection": null  ❌ MISSING
    }
  ]
}
```

### What We Need:
```json
{
  "streetName": "18TH ST",
  "side": "L",
  "fromStreet": "York St",
  "toStreet": "Bryant St",
  "fromAddress": "3401",  ✅ ODD numbers
  "toAddress": "3449",
  "rules": [
    {
      "type": "street-sweeping",
      "cardinalDirection": "N"  ✅ North side
    }
  ]
}
```

## SF Data Conventions

### L/R to Odd/Even Mapping:
- **L (Left) side** = Typically ODD addresses (3401, 3403, 3405...)
- **R (Right) side** = Typically EVEN addresses (3400, 3402, 3404...)

### Cardinal Directions:
Street cleaning data includes cardinal directions (N, S, E, W, NE, NW, SE, SW) that indicate which physical side of the street.

## Root Cause

### 1. Address Ranges Not Ingested
The `fromAddress` and `toAddress` fields from the Active Streets dataset (`lf_fadd`, `lf_toadd`, `rt_fadd`, `rt_toadd`) were not properly mapped during ingestion.

**Source Data (Active Streets - 3psu-pn9h)**:
- `lf_fadd`: Left from address (e.g., 3401)
- `lf_toadd`: Left to address (e.g., 3449)
- `rt_fadd`: Right from address (e.g., 3400)
- `rt_toadd`: Right to address (e.g., 3448)

### 2. Cardinal Direction Not Preserved
The street cleaning dataset (`yhqp-riqs`) has a `corridor` field that contains cardinal direction, but it wasn't mapped to the rules during ingestion.

**Source Data (Street Cleaning - yhqp-riqs)**:
- `corridor`: Contains values like "N", "S", "E", "W", "NE", "NW", "SE", "SW"

## Solution

### Option 1: Re-ingest with Address Ranges (RECOMMENDED)
Modify the ingestion script to properly map address ranges:

```python
# For L (Left) side segments
segment["fromAddress"] = str(active_street.get("lf_fadd", ""))
segment["toAddress"] = str(active_street.get("lf_toadd", ""))

# For R (Right) side segments  
segment["fromAddress"] = str(active_street.get("rt_fadd", ""))
segment["toAddress"] = str(active_street.get("rt_toadd", ""))
```

### Option 2: Add Cardinal Direction from Street Cleaning
Preserve the `corridor` field when merging street cleaning data:

```python
rule = {
    "type": "street-sweeping",
    "day": cleaning_record.get("weekday"),
    "startTime": cleaning_record.get("fromhour"),
    "endTime": cleaning_record.get("tohour"),
    "cardinalDirection": cleaning_record.get("corridor"),  # ADD THIS
    "side": cleaning_record.get("cnnrightleft")
}
```

### Option 3: Display Logic (TEMPORARY WORKAROUND)
Until re-ingestion, use the side indicator:
- Display "18TH ST (L side)" or "18TH ST (Left)"
- Note: L typically = odd addresses, R typically = even addresses

## Recommended Display Format

### With Address Range:
```
18TH ST (3401-3449)  # Shows it's odd numbers
```

### With Cardinal Direction:
```
18TH ST (N side)  # Shows it's north side
```

### Combined:
```
18TH ST (N side, 3401-3449)  # Best - shows both
```

### Current Fallback:
```
18TH ST (L)  # What we have now - less user-friendly
```

## Next Steps

1. ✅ **Identified the issue**: Address ranges and cardinal directions not ingested
2. ✅ **Documented findings**: Complete analysis of missing data fields
3. ⏭️ **Update ingestion script**: Add address range mapping
4. ⏭️ **Update ingestion script**: Preserve cardinal direction from street cleaning
5. ⏭️ **Re-run ingestion**: For Mission neighborhood
6. ⏭️ **Verify results**: Query API to confirm address ranges and cardinal directions
7. ⏭️ **Update frontend**: Display address ranges or cardinal directions instead of just "L/R"

## Implementation Status

### Analysis Complete ✅
- Identified missing `fromAddress` and `toAddress` fields from Active Streets dataset
- Identified missing `cardinalDirection` field from Street Cleaning dataset
- Documented L/R to odd/even address mapping convention
- Documented source data fields and their locations

### Ready for Implementation ⏭️
- Ingestion script modifications needed in `ingest_mission_only.py`
- Frontend display updates needed in `BlockfaceDetail.tsx` and `MapView.tsx`

## Files to Modify

1. **`ingest_mission_only.py`** - Add address range and cardinal direction mapping
2. **`frontend/src/components/BlockfaceDetail.tsx`** - Update display logic to show address ranges
3. **`frontend/src/components/MapView.tsx`** - Update popup to show cardinal direction

## Example Query to Verify After Fix

```bash
curl "http://localhost:8000/api/v1/blockfaces?lat=37.7604&lng=-122.4087&radius_meters=200" | \
  jq '.[] | select(.streetName == "18TH ST") | select(.side == "L") | 
  {streetName, side, fromAddress, toAddress, cardinal: .rules[0].cardinalDirection}'
```

Expected output after fix:
```json
{
  "streetName": "18TH ST",
  "side": "L",
  "fromAddress": "3401",
  "toAddress": "3449",
  "cardinal": "N"
}