# Regulation Display Text Examples

**Date**: December 31, 2024  
**Purpose**: Concrete examples of how regulations are displayed to users

---

## 📋 COMPLETE DISPLAY EXAMPLES BY TYPE

### 1. Time-Limited Parking

#### With RPP Exception (Most Common - 83.4%)
```
Input:
  regulation: "Time limited"
  hrlimit: "2"
  days: "MON-FRI"
  hours: "800-1800"
  rpparea1: "W"
  exceptions: "Yes. RPP holders are exempt from time limits."

Output Display:
  "2hr limit Weekdays 8am-6pm except permit"
```

#### Without RPP (5.8%)
```
Input:
  regulation: "Time limited"
  hrlimit: "4"
  days: "MON-FRI"
  hours: "700-1800"
  rpparea1: null
  exceptions: "None. Regulation applies to all vehicles."

Output Display:
  "4hr limit Weekdays 7am-6pm"
```

#### Government Permit (0.7%)
```
Input:
  regulation: "Government permit"
  hrlimit: "2"
  days: "MON-FRI"
  hours: "800-1800"
  exceptions: "Government permit holders exempt"

Output Display:
  "2hr limit Weekdays 8am-6pm except government permit"
```

#### All Day Limit
```
Input:
  regulation: "Time limited"
  hrlimit: "2"
  days: "DAILY"
  hours: null
  rpparea1: "X"

Output Display:
  "2hr limit Daily except permit"
```

---

### 2. No Parking

#### No Parking Any Time (2.3%)
```
Input:
  regulation: "No parking any time"
  days: null
  hours: null

Output Display:
  "No Parking"
```

#### Limited No Parking with Time (0.3%)
```
Input:
  regulation: "Limited No Parking"
  days: "MON-SUN"
  hours: "300-600"

Output Display:
  "No Parking M-Su 3am-6am"
```

#### No Parking with Permit Exception
```
Input:
  regulation: "Limited No Parking"
  days: "MON-FRI"
  hours: "800-1800"
  rpparea1: "Y"
  exceptions: "RPP holders are exempt"

Output Display:
  "No Parking M-F 8am-6pm except permit"
```

#### No Overnight Parking (0.2%)
```
Input:
  regulation: "No overnight parking"
  days: "MON,THU"
  hours: "0-400"

Output Display:
  "No Parking M, Th 12am-4am"
```

#### No Parking Time Only
```
Input:
  regulation: "No overnight parking"
  days: null
  hours: "1800-600"

Output Display:
  "No Parking 6pm-6am"
```

---

### 3. Street Cleaning

#### Standard Street Cleaning
```
Input:
  weekday: "Thursday"
  fromhour: "0"
  tohour: "6"

Output Display:
  "Street Cleaning Th 12am-6am"
```

#### Different Day/Time
```
Input:
  weekday: "Monday"
  fromhour: "8"
  tohour: "10"

Output Display:
  "Street Cleaning M 8am-10am"
```

---

### 4. Metered Parking

#### With Time Limit
```
Input:
  schedule_type: "OP"
  days_applied: "Mo-Sa"
  from_time: "900"
  to_time: "1800"
  time_limit_minutes: 120
  rate: "4.00"

Output Display:
  "2hr Meter M-Sa 9am-6pm ($4.00/hr)"
```

#### Without Time Limit
```
Input:
  schedule_type: "OP"
  days_applied: "Mo-Sa"
  from_time: "900"
  to_time: "1800"
  time_limit_minutes: null
  rate: "4.00"

Output Display:
  "Meter M-Sa 9am-6pm ($4.00/hr)"
```

#### Different Rate
```
Input:
  schedule_type: "OP"
  days_applied: "Mo-Fr"
  from_time: "800"
  to_time: "1800"
  time_limit_minutes: 240
  rate: "2.50"

Output Display:
  "4hr Meter Weekdays 8am-6pm ($2.50/hr)"
```

---

### 5. No Oversized Vehicles (6.8%)

```
Input:
  regulation: "No oversized vehicles"

Output Display:
  "No oversized vehicles"

Note: Informational only - does NOT affect eligibility for standard cars
```

---

### 6. Paid/Pay + Permit (SKIPPED - 0.7%)

#### Paid + Permit
```
Input:
  regulation: "Paid + Permit"
  hrlimit: "2"
  days: "MON-FRI"
  hours: "900-1800"
  rpparea1: "HV"

Output Display:
  SKIPPED (returns None)
  
Reason: Meter dataset provides complete information for this location
```

#### Pay or Permit
```
Input:
  regulation: "Pay or Permit"
  hrlimit: "2"
  days: "MON-SAT"
  hours: "900-2100"
  rpparea1: "HV"

Output Display:
  SKIPPED (returns None)
  
Reason: Meter dataset provides complete information for this location
```

---

## 🎯 REAL-WORLD SCENARIO EXAMPLES

### Scenario 1: Residential Street with RPP
**Location**: 19th Street, Mission District

**Regulations Present**:
1. Street Cleaning: Thu 12am-6am
2. Time Limit: 2hr limit Weekdays 8am-6pm except permit
3. No Oversized Vehicles

**Display to User**:
```
✓ Street Cleaning Th 12am-6am
✓ 2hr limit Weekdays 8am-6pm except permit
ℹ No oversized vehicles
```

**User Impact**:
- Cannot park during street cleaning (Thu 12am-6am)
- Can park with 2hr limit on weekdays 8am-6pm (no permit)
- Oversized vehicle restriction is informational only

---

### Scenario 2: Commercial Street with Meters
**Location**: Market Street, Downtown

**Regulations Present**:
1. Metered Parking: M-Sa 9am-6pm ($4.00/hr, 2hr limit)
2. No Parking: 3am-6am (street cleaning)

**Display to User**:
```
✓ 2hr Meter M-Sa 9am-6pm ($4.00/hr)
✓ No Parking 3am-6am
```

**User Impact**:
- Must pay meter M-Sa 9am-6pm, 2hr max
- Cannot park 3am-6am any day

---

### Scenario 3: Mixed Use Area with Paid + Permit
**Location**: Hayes Valley

**Regulations in Dataset**:
1. Paid + Permit: 2hr, M-Sa 9am-9pm, RPP Area HV
2. Street Cleaning: Th 12am-6am

**What Gets Displayed**:
```
✓ Street Cleaning Th 12am-6am
✓ 2hr Meter M-Sa 9am-9pm ($3.50/hr)  [from meter dataset]
```

**Note**: The "Paid + Permit" regulation is SKIPPED because the meter dataset provides the complete information including:
- Operating hours
- Rate
- Time limit
- RPP exemption (handled by meter logic)

---

### Scenario 4: Government Building Area
**Location**: Near City Hall

**Regulations Present**:
1. Time Limit: 2hr limit Weekdays 8am-6pm except government permit
2. No Parking: 10pm-6am

**Display to User**:
```
✓ 2hr limit Weekdays 8am-6pm except government permit
✓ No Parking 10pm-6am
```

**User Impact**:
- Can park with 2hr limit weekdays 8am-6pm (no government permit)
- Cannot park 10pm-6am any day

---

## 📊 DISPLAY FORMAT RULES SUMMARY

### Time Format
- **Simplified**: `8am` not `8:00 AM`
- **Lowercase period**: `am`/`pm` not `AM`/`PM`
- **Minutes only when needed**: `8:30am` but `8am`

### Day Format
- **Minimal abbreviations**: `M, Tu, W, Th, F, Sa, Su`
- **Smart overrides**: `Daily`, `Weekdays`, `Weekends`
- **Ranges**: `M-F` not `Monday-Friday`

### Duration Format
- **No space**: `2hr` not `2 hr`
- **Singular unit**: `hr` not `hrs`
- **Minutes for < 60**: `30min` not `0.5hr`

### Exception Suffix Format
- **Lowercase**: `except permit` not `Except Permit`
- **Consistent**: Always same format
- **Specific**: `except government permit` for government

---

## 🔍 SKIP LOGIC VERIFICATION

### Why Skip Paid/Permit Regulations?

**Reason 1: Meter Dataset is Complete**
- Meter dataset includes operating hours, rates, time limits
- Meter dataset includes RPP exemption information
- Displaying both would be redundant

**Reason 2: Spatial Overlap**
- All 61 Paid/Permit regulations have geometry
- These geometries overlap with meter locations
- Meters provide the authoritative information

**Reason 3: User Experience**
- Showing "Paid + Permit" AND meter info is confusing
- Meter display already includes all relevant details
- Simpler display = better UX

### Example of Overlap

**Parking Regulation Record (SKIPPED)**:
```
ObjectID: 12822
Regulation: "Paid + Permit"
RPP Area: HV
Days: M-Sa
Hours: 900-2100
Time Limit: 2hr
```

**Meter Record (DISPLAYED)**:
```
Post ID: 123456
Street: Hayes St
RPP Area: HV
Schedule: M-Sa 9am-9pm
Rate: $3.50/hr
Time Limit: 2hr
Cap Color: GREY (general parking)
```

**What User Sees**:
```
2hr Meter M-Sa 9am-9pm ($3.50/hr)
```

This single line conveys all the information from both records!

---

## ✅ VALIDATION CHECKLIST

- [x] All regulation types have display examples
- [x] Real-world scenarios documented
- [x] Skip logic explained with examples
- [x] Format rules clearly defined
- [x] User impact described for each scenario

---

**Last Updated**: December 31, 2024