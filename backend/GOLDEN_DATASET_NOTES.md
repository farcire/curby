# Golden Dataset Validation Notes

## Special Cases & Institutional Knowledge

### 1. 72-Hour Time Limit (HV RPP Areas)
**Issue**: Rows with `hrlimit=72` flagged as mismatch when interpreted as "2hr Limit"

**Explanation**: 
- The 72-hour limit applies to RPP permit holders (SF general rule: no car can remain in same location >72 hours)
- For non-permit holders, HV RPP areas have a **2-hour parking limit**
- Since this dataset is for non-permit holders, the 2hr interpretation is correct

**Affected unique_ids**:
- `5ab852445b6d3d9d4a326b41ebfeda08` (Row 113)
- Other HV RPP area regulations with hrlimit=72

**Golden Summary**: "2hr Limit [times] except residential permit" ✅ CORRECT

---

### 2. Restricted Action with Critical Severity
**Issue**: Rows 63-64 flagged for "Restricted" action with "critical" severity

**Explanation**:
- These are atypical regulations (likely metered + permit combinations)
- Conservative interpretation: treat as critical due to potential towing/high fines
- Standard "Restricted" (oversized vehicles) = low/medium severity
- But metered+permit violations can be critical

**Affected unique_ids**:
- `501adb918f9efa39f34083545e32066b` (Row 63)
- `ef2dd6f6a910e42c54a1409ccabe0b59` (Row 64)

**Regulation Type**: "Paid + Permit" (metered parking with RPP exception)
**Golden Severity**: "critical" ✅ CORRECT (conservative interpretation for enforcement)

---

### 3. Day Restrictions Must Be Mentioned
**Pattern**: When source has `days` field populated, it MUST appear in golden_summary

**Examples**:
- Government permits with M-F restriction
- SF Public Works permits with M-F restriction
- Portuguese Consulate permits with M-F restriction

**Correct Format**: "No parking except [entity] Monday-Friday [times]"

---

### 4. Generic Permit References
**Pattern**: Use generic "residential permit" instead of specific area codes

**Examples**:
- ✅ "except residential permit" (generic)
- ❌ "except Area X permit" (too specific)
- ❌ "except Area HV permit" (too specific)

**Rationale**: Simplifies interpretation, focuses on permit requirement rather than specific area

---

### 5. Time Format Conversion
**Pattern**: Source uses 24-hour format, golden_summary uses 12-hour format

**Examples**:
- `1800` → `6pm` ✅
- `2200` → `10pm` ✅
- `2400` → `12am` ✅
- `1600` → `4pm` ✅

**Note**: Validation script incorrectly flags these as mismatches (false positives)

---

## Validation Script Improvements Needed

1. **Disable 24hr→12hr time mismatch check** (too many false positives)
2. **Add exception for 72hr limit in HV RPP areas** (institutional knowledge)
3. **Allow "critical" severity for "Restricted" action** when regulation type is "Paid + Permit"
4. **Keep day restriction check** (this caught real issues)

---

## Key Takeaways for LLM Training

1. **Domain knowledge matters**: 72hr limit interpretation requires SF parking expertise
2. **Context-dependent severity**: Same action type can have different severity based on regulation details
3. **Completeness is critical**: Day restrictions must always be mentioned when present
4. **User-friendly format**: Convert 24hr to 12hr time format for readability