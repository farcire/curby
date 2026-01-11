# KING ST CNN Investigation Summary

## Problem
Could not find KING ST segments by searching street_segments collection by street name.

## Root Cause
The `streets` collection (from SF Data Active/Retired Streets dataset) contains the master CNN list with street names, but the `street_segments` collection uses different field names:
- streets collection: `street`, `cnn`, `lf_fadd`, `rt_fadd`, etc.
- street_segments collection: `streetName`, `cnn`, `fromAddress`, `toAddress`, etc.

## Solution
1. Query the `streets` collection to find CNNs by street name
2. Use those CNNs to query the `street_segments` collection for detailed parking data

## KING ST CNNs Found (15 total)
From the `streets` collection query:

```python
cursor = db.streets.find({'street': 'KING'})
```

Results:
- CNN 7834201: Right side 300-398, 4TH ST to 5TH ST (NorthWest)
- CNN 7834101: Left side 301-399, 4TH ST to 5TH ST (SouthEast)
- CNN 7833201: Right side 200-298, 3RD ST to 4TH ST
- CNN 7833101: Left side 201-299, 3RD ST to 4TH ST
- CNN 7832201: Right side 100-198, 2ND ST to 3RD ST
- CNN 7832101: Left side 101-199, 2ND ST to 3RD ST
- CNN 7831201: Right side 2-98, EMBARCADERO to 2ND ST
- CNN 7831101: Left side 1-99, EMBARCADERO to 2ND ST
- CNN 7835001: Both sides 400-499, 5TH ST to BERRY ST
- CNN 7837000: Both sides 600-699, 7TH ST to DIVISION ST
- CNN 7834000, 7835000, 7836000, 7836001, 7836002: Various segments with nan addresses

## Key Learnings
1. **Always check the `streets` collection first** when searching by street name
2. The `streets` collection has the authoritative CNN-to-street-name mapping
3. The `street_segments` collection has the detailed parking/meter/regulation data
4. Field names differ between collections (lowercase vs camelCase)
5. CNNs are stored as strings, not integers

## Query Pattern
```python
# Step 1: Find CNN in streets collection
street_doc = await db.streets.find_one({'street': 'KING', 'lf_fadd': '301', 'lf_toadd': '399'})
cnn = street_doc['cnn']

# Step 2: Get detailed data from street_segments
segment_doc = await db.street_segments.find_one({'cnn': cnn, 'side': 'L'})
```
