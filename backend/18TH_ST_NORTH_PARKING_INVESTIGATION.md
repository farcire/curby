# Parking Investigation: 18th Street North 2700-2798

## Location Information

**Street:** 18th Street  
**Side:** North (Right side of centerline)  
**Address Range:** 2700-2798  
**From Street:** York St  
**To Street:** Bryant St  
**Zip Code:** 94110  
**CNN:** 868000  
**Side Code:** R  

**Display Name:** 18th Street (North side, 2700-2798)

---

## Parking Regulations

### Total Rules: 2
- **Parking Regulations:** 1
- **Street Sweeping:** 1
- **Meter Schedules:** 0

---

## PARKING REGULATION #1: No Oversized Vehicles

### Type
`parking-regulation`

### Raw Source Fields
```
regulation: "No oversized vehicles"
timeLimit: "0"
permitArea: NaN
days: "M-Su"
hours: "2400-600"
fromTime: "12am"
toTime: "6am"
details: "Oversized vehicles and trailers are those longer than 22 feet or taller than 7 feet"
exceptions: "Yes. Typical passenger vehicles are exempt."
side: "R"
matchConfidence: 1.0
```

### Interpretation
- **Type:** unknown
- **Summary:** "No oversized vehicles Oversized vehicles and trailers are those longer than 22 feet or taller than 7 feet"
- **Details:** "Unable to fully interpret this restriction. Please check signage."
- **Severity:** medium
- **Icon:** info
- **Fallback:** true (indicates this is a fallback interpretation)
- **Interpreted At:** 2025-11-30T21:31:04.148642

### Human-Readable Summary
**No oversized vehicles allowed from 12:00 AM to 6:00 AM, Monday through Sunday**

- **Restriction:** Oversized vehicles and trailers prohibited
- **Definition:** Vehicles longer than 22 feet OR taller than 7 feet
- **Time:** 12:00 AM - 6:00 AM (midnight to 6am)
- **Days:** Every day (Monday-Sunday)
- **Exceptions:** Typical passenger vehicles are exempt
- **Match Confidence:** 100%

---

## STREET SWEEPING RULE

### Type
`street-sweeping`

### Raw Source Fields
```
day: "Fri"
startTime: "0"
endTime: "6"
activeDays: [4]  (Friday = day 4)
startTimeMin: 0
endTimeMin: 360
description: "Street Cleaning Friday 12:00 AM-6:00 AM"
blockside: "North"
side: "R"
limits: "York St  -  Bryant St"
```

### Human-Readable Summary
**Street Cleaning: Friday 12:00 AM - 6:00 AM**

- **Day:** Friday only
- **Time:** 12:00 AM - 6:00 AM (midnight to 6am)
- **Side:** North side
- **Limits:** Between York St and Bryant St

---

## Geometry Information

### Centerline Geometry
- **Type:** LineString
- **Coordinates:** 2 points
  - Start: [-122.409156755, 37.761817316]
  - End: [-122.410118191, 37.76175942]

### Blockface Geometry
- **Type:** LineString  
- **Coordinates:** 2 points
  - Start: [-122.4091597604685, 37.761867225589846]
  - End: [-122.4101211964685, 37.761809329589845]

---

## Summary

For **18th Street North side (2700-2798)** between York St and Bryant St:

1. **No Oversized Vehicles:** Vehicles longer than 22 feet or taller than 7 feet are prohibited from 12:00 AM to 6:00 AM every day. Typical passenger vehicles are exempt.

2. **Street Cleaning:** No parking on Fridays from 12:00 AM to 6:00 AM for street cleaning.

3. **No Parking Meters:** This location does not have parking meters.

---

## Data Quality Notes

- The parking regulation interpretation shows as "fallback: true", indicating the AI system was unable to fully parse the regulation and is using a fallback interpretation.
- The original regulation text and all source fields are preserved in the database.
- Match confidence for the parking regulation is 100%, indicating high confidence in the spatial join.
- Street sweeping data appears to be ingesting correctly with proper day/time information.

---

## Database Record ID
`_id: 692a6915e8c1eda6d61d9a49`

---

*Investigation completed: 2025-12-05*