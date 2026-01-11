# Non-Metered Parking Regulation - Complete Display Guide

**Date**: December 31, 2024  
**Dataset**: Parking Regulations (hi6h-neyh) - 7,783 records  
**Status**: ✅ COMPLETE ANALYSIS

---

## 📊 REGULATION TYPE BREAKDOWN

| Regulation Type | Count | % | Action |
|----------------|-------|---|--------|
| Time limited | 6,889 | 88.5% | Format with duration/days/time |
| No oversized vehicles | 531 | 6.8% | Display as-is (informational) |
| No parking any time | 178 | 2.3% | "No Parking" |
| Pay or Permit | 58 | 0.7% | SKIP (meter data) |
| Government permit | 53 | 0.7% | Format with "except Government Permit" |
| Limited No Parking | 27 | 0.3% | "No Parking" + days/time |
| No overnight parking | 17 | 0.2% | "No Parking" + time |
| Paid + Permit | 3 | 0.0% | SKIP (meter data) |

---

## ✅ DISPLAY FORMATS (FINAL)

### 1. Time-Limited Parking (88.5%)

**With RPP** (83.4% of time limits):
```
Format: [Duration] limit [Days] [Time] for non-permit holders
Example: 2hr limit Weekdays 8am-6pm for non-permit holders

Trigger:
- Has rpparea1/2/3, OR
- Exceptions contains "RPP holders are exempt"
```

**Without RPP** (5.8% of time limits):
```
Format: [Duration] limit [Days] [Time]
Example: 4hr limit M-F 7am-6pm

Trigger:
- No RPP areas AND
- Exceptions = "None. Regulation applies to all vehicles." OR blank
```

**Government Permit** (0.7%):
```
Format: [Duration] limit [Days] [Time] except Government Permit
Example: 2hr limit Weekdays 8am-6pm except Government Permit

Trigger:
- Regulation contains "Government permit"
```

### 2. No Parking (Consolidated)

**No Parking Any Time** (2.3%):
```
Display: "No Parking"
(No days/time - applies always)
```

**Limited No Parking** (0.3%):
```
With Permit Exception:
  Format: No Parking [Days] [Time] for non-permit holders
  Example: No Parking M-F 8am-6pm for non-permit holders
  Trigger: Exceptions or details contains "permit"

Without Exception:
  Format: No Parking [Days] [Time]
  Example: No Parking M-Su 3am-6am
  Trigger: No permit mention
```

**No Overnight Parking** (0.2%):
```
With Days:
  Format: No Parking [Days] [Time]
  Example: No Parking M, Th 12am-4am

Without Days:
  Format: No Parking [Time]
  Example: No Parking 6pm-6am
```

**No Stopping**:
```
Display: "No Parking"
(Treat same as "No parking any time")
```

### 3. No Oversized Vehicles (6.8%)

```
Display: "No oversized vehicles"

Eligibility Impact: NONE
- Default Curby user has standard car
- This is informational only
- Does NOT affect parking eligibility
```

### 4. Paid/Pay + Permit (0.7%)

```
Action: SKIP - Do not display

Rationale:
- These are metered locations
- Meter dataset provides complete information
- Exception: "RPP holders are exempt from meters/payment"
- Displaying would duplicate meter data
```

---

## 🎯 EXCEPTION FIELD LOGIC

### Standard Exception Texts

**1. "Yes. RPP holders are exempt from time limits."**
- Add suffix: "for non-permit holders"
- Applies to: Time-limited parking

**2. "Yes. RPP holders are exempt from meters."** or **"...from payment."**
- Regulation type: "Paid + Permit" or "Pay or Permit"
- Action: SKIP (meter dataset handles this)

**3. "None. Regulation applies to all vehicles."**
- No suffix needed
- Universal rule

**4. Contains "permit" (e.g., "Portuguese Consulate permit")**
- Add suffix: "for non-permit holders"
- Applies to: Limited No Parking with special permits

**5. Blank or missing**
- Check RPP areas (rpparea1/2/3)
- If has RPP: "for non-permit holders"
- If no RPP: No suffix

---

## 🔧 IMPLEMENTATION LOGIC

### Exception Suffix Determination

```python
def get_exception_suffix(rule: Dict) -> str:
    """
    Determine exception suffix for display.
    
    Returns:
        "for non-permit holders" or ""
    """
    regulation = rule.get('regulation', '').lower()
    exceptions = rule.get('exceptions', '')
    details = rule.get('regdetails', '')
    
    # Skip meter-related regulations
    if 'paid' in regulation or 'pay' in regulation:
        return None  # Signal to skip this rule
    
    # Check for RPP areas
    has_rpp = bool(
        rule.get('rpparea1') or 
        rule.get('rpparea2') or 
        rule.get('rpparea3')
    )
    
    # Check exception text
    has_rpp_exception = (
        'RPP holders are exempt' in exceptions or
        'permit' in exceptions.lower() or
        'permit' in details.lower()
    )
    
    # Government permit special case
    if 'government' in regulation:
        return "except Government Permit"
    
    # Standard RPP exception
    if has_rpp or has_rpp_exception:
        return "for non-permit holders"
    
    return ""
```

### Rule Type Mapping

```python
def map_regulation_to_display_type(regulation: str) -> str:
    """Map regulation text to display type"""
    reg_lower = regulation.lower()
    
    if 'time limit' in reg_lower:
        return 'time-limit'
    elif 'no parking' in reg_lower or 'no stopping' in reg_lower:
        return 'no-parking'
    elif 'overnight' in reg_lower:
        return 'no-parking'  # Treat as no-parking with time
    elif 'oversized' in reg_lower:
        return 'oversized-vehicle'
    elif 'paid' in reg_lower or 'pay' in reg_lower:
        return 'SKIP'  # Meter data
    elif 'government' in reg_lower:
        return 'government-permit'
    else:
        return 'parking-regulation'
```

---

## 📋 COMPLETE DISPLAY EXAMPLES

### Time-Limited
```
2hr limit Weekdays 8am-6pm for non-permit holders
4hr limit M-F 7am-6pm
2hr limit Weekdays 8am-6pm except Government Permit
```

### No Parking
```
No Parking
No Parking M-Su 3am-6am
No Parking M-F 6am-10am
No Parking M-F 8am-6pm for non-permit holders
No Parking M, Th 12am-4am
No Parking 6pm-6am
No Parking 10pm-6am
```

### Informational
```
No oversized vehicles
```

### Skip (Meter Data)
```
(Paid + Permit - not displayed)
(Pay or Permit - not displayed)
```

---

## 🎯 ELIGIBILITY IMPACT

### Default Curby User Profile
- ✅ Standard car (not oversized)
- ✅ No permits (not RPP, not Government)
- ✅ Willing to pay for meters

### Regulations That DON'T Affect Eligibility
- "No oversized vehicles" → User has standard car
- Time limits with RPP → User can still park (just with time limit)

### Regulations That DO Affect Eligibility
- "No Parking" → Cannot park
- Street Cleaning (when active) → Cannot park
- Government Permit only → Cannot park (no permit)
- RPP-only zones (no time limit for non-permit) → Cannot park

**Eligibility Logic Location**: Backend legality checker (separate from display formatter)

---

## ✅ READY FOR IMPLEMENTATION

All regulation types analyzed and display formats defined!

**Next**: Update regulation_normalizer.py with complete logic for all types.