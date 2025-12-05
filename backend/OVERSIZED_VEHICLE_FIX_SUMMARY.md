# Oversized Vehicle Regulation Fix Summary

## Investigation Completed: 18th Street North 2700-2798

### Location Details
- **CNN:** 868000
- **Side:** R (North side)
- **Address Range:** 2700-2798
- **Between:** York St and Bryant St
- **Zip Code:** 94110
- **Display Name:** 18th Street (North side, 2700-2798)

### Current Parking Rules

#### Rule 1: No Oversized Vehicles (NEEDS FIX)
**Current Display:** "time-limit 12am-6am Daily" ❌  
**Should Display:** "No oversize vehicles (>22ft long, >7ft tall) 12am-6am Daily" ✓

**Raw Source Fields:**
```json
{
  "type": "parking-regulation",
  "regulation": "No oversized vehicles",
  "timeLimit": "0",
  "permitArea": NaN,
  "days": "M-Su",
  "hours": "2400-600",
  "fromTime": "12am",
  "toTime": "6am",
  "details": "Oversized vehicles and trailers are those longer than 22 feet or taller than 7 feet",
  "exceptions": "Yes. Typical passenger vehicles are exempt.",
  "side": "R",
  "matchConfidence": 1.0
}
```

**Current Interpretation (INCORRECT):**
```json
{
  "type": "unknown",
  "display": {
    "summary": "No oversized vehicles Oversized vehicles and trailers are those longer than 22 feet or taller than 7 feet",
    "details": "Unable to fully interpret this restriction. Please check signage.",
    "severity": "medium",
    "icon": "info"
  },
  "meta": {
    "fallback": true
  }
}
```

#### Rule 2: Street Cleaning (CORRECT) ✓
**Display:** "Street Cleaning 12am-6am Fri"

---

## Oversized Vehicle Regulation Variations

Based on user feedback, there are 13 variations of oversized vehicle regulations that need two different interpretations:

### Type 1: Length AND Height Restrictions (Variations 1,2,3,4,5,7,8,10,13)
**Display Format:** "No oversize vehicles (>22ft long, >7ft tall) [time] [days]"

**Characteristics:**
- Regulation text contains "No oversized vehicles"
- Details mention "longer than 22 feet or taller than 7 feet"
- May have time restrictions (e.g., "12am-6am") or be 24/7
- May have day restrictions (e.g., "M-Su", "Daily") or apply all days

**Correct Interpretation:**
```json
{
  "type": "no-parking",
  "display": {
    "summary": "No oversize vehicles (>22ft long, >7ft tall) [time] [days]",
    "details": "Oversized vehicles and trailers longer than 22 feet or taller than 7 feet are prohibited. Typical passenger vehicles are exempt.",
    "severity": "high",
    "icon": "ban"
  },
  "logic": {
    "action": "prohibited",
    "vehicle_restrictions": {
      "max_length_ft": 22,
      "max_height_ft": 7
    },
    "exceptions": ["Typical passenger vehicles"]
  }
}
```

### Type 2: Height-Only Restrictions (Variations 6,9,11,12)
**Display Format:** "No parking vehicles >6ft high [time] [days]"

**Characteristics:**
- Regulation text mentions height restriction only
- Typically "vehicles over 6 feet high"
- May have time/day restrictions

**Correct Interpretation:**
```json
{
  "type": "no-parking",
  "display": {
    "summary": "No parking vehicles >6ft high [time] [days]",
    "details": "Vehicles taller than 6 feet are prohibited from parking.",
    "severity": "high",

**Important:** When determining parking eligibility, assume no user has an oversize vehicle, so this restriction will NOT affect parking eligibility. The severity should be "low" and it should not block parking.
    "icon": "ban"
  },
  "logic": {
    "action": "prohibited",
    "vehicle_restrictions": {
      "max_height_ft": 6
    }
  }
}
```

---

## Required Fixes

### 1. Database Update Script
Create a script to:
- Find all segments with oversized vehicle regulations
- Identify which type (Type 1 or Type 2) based on regulation text
- Update the interpretation field with correct display summary
- Parse time/day restrictions from source fields
- Set fallback: false

### 2. Ingestion Pipeline Update
Update `backend/ingest_data_cnn_segments.py` to:
- Add special handling for oversized vehicle regulations
- Detect regulation type from text
- Generate correct interpretation during ingestion
- Prevent fallback interpretation for these known patterns

### 3. Deterministic Parser Update
Update `backend/deterministic_parser.py` to:
- Add pattern matching for "oversized" or "oversize" in regulation text
- Extract height/length restrictions from details field
- Parse time restrictions (handle "2400-600" format)
- Parse day restrictions (handle "M-Su" format)

### 4. Documentation Updates
- Update judge script documentation
- Update worker script documentation
- Add to DATA_QUALITY_FOLLOWUP_TASKS.md: Monitor for new oversized regulation variations

---

## Implementation Priority

1. **Immediate:** Fix existing database records (all affected segments)
2. **High:** Update ingestion pipeline to handle correctly going forward
3. **Medium:** Update deterministic parser for better pattern recognition
4. **Low:** Add monitoring for new variations

---

## Data Quality Note

**Action Item:** Add to DATA_QUALITY_FOLLOWUP_TASKS.md:
```
## Oversized Vehicle Regulations Monitoring

Monitor for new variations of parking regulations containing "oversize", "oversized", 
or height/length vehicle restrictions in any field of the parking regulations dataset.

Known patterns:
- Type 1: Length (>22ft) AND Height (>7ft) restrictions
- Type 2: Height-only (>6ft) restrictions

If new patterns appear, investigate and document interpretation rules.
```

---

*Investigation Date: 2025-12-05*  
*Investigator: Roo (Code Mode)*