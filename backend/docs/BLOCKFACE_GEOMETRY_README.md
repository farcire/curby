# Blockface Geometry Integration - Quick Start

## Overview

This implementation adds blockface geometries to the CNN Master dataset by using parking meter locations to calibrate typical offset distances from street centerlines to parking edges.

## Prerequisites

```bash
# Install required packages
pip install sodapy shapely numpy python-dotenv

# Set up environment variables
echo "SOCRATA_APP_TOKEN=your_token_here" > .env
```

## Quick Start

### Step 1: Calibrate Offsets (One-time)

```bash
cd backend
python calibrate_blockface_offsets.py
```

**What it does:**
- Analyzes ~30,000 parking meters
- Calculates distance from meters to CNN centerlines
- Generates statistical model of typical offsets

**Output:**
- `blockface_offset_calibration.json` - Calibration model
- `blockface_offset_raw_data.json` - Raw measurements

**Expected time:** 5-10 minutes

**Expected results:**
```
L Side: -10.12m offset (n=14,227)
R Side: +10.05m offset (n=14,226)
```

### Step 2: Generate Blockface Geometries

```bash
python generate_blockface_geometries.py
```

**What it does:**
- Loads calibration model from Step 1
- Fetches all Active Streets (16,374 CNNs)
- Generates parallel lines at calibrated offsets
- Creates 32,748 entries (CNN_L + CNN_R)

**Output:**
- `cnn_master_with_blockfaces.json` - Complete CNN Master with blockface geometries

**Expected time:** 10-15 minutes

**Expected results:**
```
CNN Master Entries: 32,748
With Blockface Geometry: 32,650 (99.7%)
File size: ~700 MB
```

## Verification

### Check Calibration Model

```bash
# View calibration statistics
cat blockface_offset_calibration.json | python -m json.tool | head -30
```

Expected structure:
```json
{
  "metadata": {
    "created_at": "2024-12-30T...",
    "total_samples": 28453,
    "version": "1.0"
  },
  "by_side": {
    "L": {
      "mean": -10.45,
      "median": -10.12,
      "std": 2.34,
      "count": 14227
    },
    "R": {
      "mean": 10.38,
      "median": 10.05,
      "std": 2.28,
      "count": 14226
    }
  }
}
```

### Check Generated Geometries

```bash
# Count entries with blockfaces
cat cnn_master_with_blockfaces.json | grep -c '"blockface"'

# Should output: ~32650
```

### Validate Sample Entry

```python
import json

# Load CNN Master
with open('cnn_master_with_blockfaces.json', 'r') as f:
    cnn_master = json.load(f)

# Check first entry
entry = cnn_master[0]
print(f"ID: {entry['id']}")
print(f"CNN: {entry['cnn']}")
print(f"Side: {entry['side']}")
print(f"Has centerline: {'geometry' in entry}")
print(f"Has blockface: {'blockface' in entry}")

if 'blockface' in entry:
    bf = entry['blockface']
    print(f"Blockface offset: {bf['offset_meters']:.2f}m")
    print(f"Confidence: {bf['geometry_confidence']}")
    print(f"Source: {bf['geometry_source']}")
```

## Troubleshooting

### Issue: "Calibration model not found"

**Solution:**
```bash
# Run calibration first
python calibrate_blockface_offsets.py
```

### Issue: "No offset data collected"

**Possible causes:**
1. Socrata API token not set
2. Network connectivity issues
3. Dataset IDs changed

**Solution:**
```bash
# Check environment
echo $SOCRATA_APP_TOKEN

# Test API connection
python -c "from sodapy import Socrata; print('API OK')"
```

### Issue: Low sample count (<10,000)

**Possible causes:**
1. API rate limiting
2. Incomplete data fetch

**Solution:**
```bash
# Check raw data file
wc -l blockface_offset_raw_data.json

# Re-run with verbose output
python calibrate_blockface_offsets.py 2>&1 | tee calibration.log
```

### Issue: Geometry generation failures (>5%)

**Possible causes:**
1. Very short street segments
2. Complex geometries
3. Invalid coordinates

**Solution:**
- Review validation output
- Check specific CNNs with failures
- May be acceptable for edge cases

## Understanding the Output

### Calibration Model Structure

```json
{
  "metadata": {
    "created_at": "ISO timestamp",
    "total_samples": 28453,
    "version": "1.0"
  },
  "by_side": {
    "L": {
      "mean": -10.45,      // Average offset (meters)
      "median": -10.12,    // Median offset (more robust)
      "std": 2.34,         // Standard deviation
      "min": -18.50,       // Minimum offset
      "max": -4.20,        // Maximum offset
      "count": 14227,      // Number of samples
      "percentile_25": -11.80,  // 25th percentile
      "percentile_75": -8.90    // 75th percentile
    },
    "R": { /* similar structure */ }
  },
  "global": {
    "mean": 0.03,         // Should be near zero
    "median": 0.02,
    "std": 10.25,
    "count": 28453
  }
}
```

### CNN Master Entry Structure

```json
{
  "id": "3285000_L",
  "cnn": "3285000",
  "side": "L",
  
  // Street information
  "streetname_gc": "MISSION ST",
  "from_addr": 2301,
  "to_addr": 2399,
  
  // Centerline geometry (from Active Streets)
  "geometry": [
    [-122.4186, 37.7555],
    [-122.4187, 37.7556],
    // ... more coordinates
  ],
  
  // Blockface geometry (generated)
  "blockface": {
    "geometry": [
      [-122.4185, 37.7555],
      [-122.4186, 37.7556],
      // ... parallel to centerline
    ],
    "geometry_source": "meter_calibrated",
    "geometry_confidence": 0.85,
    "offset_meters": -10.12,  // Negative = left side
    "offset_source": "calibrated",
    "created_at": "2024-12-30T...",
    "updated_at": "2024-12-30T..."
  }
}
```

## Performance Expectations

| Operation | Time | Output Size |
|-----------|------|-------------|
| Calibration | 5-10 min | ~2 MB |
| Generation | 10-15 min | ~700 MB |
| Total | 15-25 min | ~702 MB |

## Next Steps

After generating blockface geometries:

1. **Review Results**
   ```bash
   # Check validation summary
   tail -50 generation.log
   ```

2. **Integrate with Existing Data**
   - Merge with meters, regulations, schedules
   - See: [`BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md`](BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md)

3. **Deploy to MongoDB**
   ```bash
   # Future: Deploy script
   python deploy_cnn_master_with_blockfaces.py
   ```

4. **Update API**
   - Modify endpoints to serve blockface geometries
   - Update spatial queries to use blockface edges

5. **Update Frontend**
   - Render blockface edges on map
   - Show parking spaces more accurately

## Files Generated

| File | Size | Description |
|------|------|-------------|
| `blockface_offset_calibration.json` | ~2 KB | Statistical model |
| `blockface_offset_raw_data.json` | ~2 MB | Raw measurements |
| `cnn_master_with_blockfaces.json` | ~700 MB | Complete CNN Master |

## Maintenance

### When to Re-run

**Calibration:**
- Quarterly (when meter locations change significantly)
- After major street network updates
- When new meters are installed

**Generation:**
- After re-calibration
- When Active Streets dataset updates
- Before major deployments

### Monitoring

Track these metrics over time:
- Sample count (should stay >25,000)
- Offset statistics (should be stable)
- Generation success rate (should be >99%)
- File sizes (should be consistent)

## Support

For issues or questions:
1. Check [`BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md`](BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md)
2. Review script output logs
3. Examine raw data files
4. Check Socrata API status

## References

- **Integration Guide**: [`BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md`](BLOCKFACE_GEOMETRY_INTEGRATION_GUIDE.md)
- **CNN Master Design**: [`CNN_MASTER_FILE_DESIGN.md`](CNN_MASTER_FILE_DESIGN.md)
- **Architecture**: [`CNN_MASTER_REFERENCE_ARCHITECTURE.md`](CNN_MASTER_REFERENCE_ARCHITECTURE.md)

---

**Last Updated:** December 30, 2024  
**Version:** 1.0