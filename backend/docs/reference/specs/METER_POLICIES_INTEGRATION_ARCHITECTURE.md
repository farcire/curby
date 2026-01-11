# Meter Operating Schedules Integration Architecture

## Overview
This document describes how to integrate meter operating schedules from the Meter Policies dataset (qq7v-hds4) with PostID and Parking Space ID into the Curby system.

## Data Sources

### Primary Source: Parking Meters (8vzz-qzz9)
- **Purpose**: Physical meter attributes
- **Key Fields**:
  - `post_id` - Unique meter identifier
  - `cap_color` - Vehicle type restriction (Grey, Yellow, Red, etc.)
  - `street_seg_ctrln_id` - CNN for location matching
  - `latitude`, `longitude` - Geographic coordinates
  - `street_name`, `street_num` - Address information
  - `blockface_id` - Link to blockface geometry
- **Coverage**: 38,356 meters

### Supplemental Source: Meter Policies (qq7v-hds4)
- **Purpose**: Operating schedules and time-based rules
- **Key Fields**:
  - `postid` - Links to Parking Meters
  - `parkingspaceid` - **Parking space identifier** (THIS is where parking_space_id comes from!)
  - `scheduletype` - FREE, PRE, OP, ALT, TOW
  - `dayofweek` - Mo, Tu, We, Th, Fr, Sa, Su
  - `starttime` - 24-hour format (e.g., "9:00", "18:00")
  - `endtime` - 24-hour format
  - `timelimitminutes` - Maximum parking duration (for OP schedules)
  - `hourlyrate` - Rate for paid parking
  - `startdate` - Policy validity start (ISO format)
  - `enddate` - Policy validity end (ISO format)
  - `capcolor` - Also in policies, but use Parking Meters as primary
- **Coverage**: 1,545 unique postIDs with 50,000 policy records

## Validation Results

✓ **100% Coverage**: All postIDs in Meter Policies exist in Parking Meters  
✓ **Data Hierarchy Confirmed**: Parking Meters = Primary, Meter Policies = Supplemental  
⚠ **Note**: 96% of meters (36,811) have NO operating policies in the dataset

## Schedule Types

### 1. FREE Schedule
- **Meaning**: No payment required, no time restrictions
- **Important**: Only valid within the [starttime, endtime] window specified
- **Example**: 
  ```
  PostID: 330-06520
  DayOfWeek: We (Wednesday)
  StartTime: 18:00, EndTime: 24:00
  Valid: 2026-01-12 to 2200-12-31
  → Free parking Wednesday 6 PM to midnight
  ```

### 2. PRE (Prepay) Schedule
- **Meaning**: Users can prepay before enforcement begins
- **Critical Rule**: Prepaid time includes free time before enforcement
- **Example Calculation**:
  - Meter enforcement starts at 9:00 AM
  - User prepays at 8:00 AM for 1 hour
  - Meter shows 2 hours paid:
    - 8:00-9:00 AM: Free (before enforcement)
    - 9:00-10:00 AM: Paid (1 hour purchased)
  - User is paid through 10:00 AM
- **Example**:
  ```
  PostID: 568-20380
  DayOfWeek: We
  StartTime: 4:30, EndTime: 8:00
  → Can prepay starting at 4:30 AM, enforcement begins at 8:00 AM
  ```

### 3. OP (Paid Operation) Schedule
- **Meaning**: Standard metered parking with rates and time limits
- **Key Attributes**:
  - `hourlyrate` - Cost per hour
  - `timelimitminutes` - Maximum parking duration
  - Cap color restrictions apply (from Parking Meters dataset)
- **Example**:
  ```
  PostID: 651-07110
  DayOfWeek: Tu
  StartTime: 12:00, EndTime: 15:00
  TimeLimitMinutes: 120 (2 hours)
  HourlyRate: $4.00
  → Paid parking Tuesday noon-3 PM, 2-hour max
  ```

### 4. ALT & TOW Schedules
- **ALT**: Alternative schedule (7.9% of policies)
- **TOW**: Tow-away zone (2.6% of policies)
- Further investigation needed for these types

## Cap Color Vehicle Restrictions

**Sources**:
- **Parking Meters dataset** (`cap_color` field) - General meter cap color
- **Meter Policies dataset** (`capcolor` field) - **Policy-specific cap color for OP schedules**

| Cap Color | Restriction | Count (Meters) | Percentage |
|-----------|-------------|----------------|------------|
| Grey | Standard passenger vehicles | 25,691 | 67.0% |
| Yellow | **Commercial vehicles only** | 4,574 | 11.9% |
| Red | **Vehicles with 6+ wheels only** | 1,404 | 3.7% |
| Black | Special restriction | 2,948 | 7.7% |
| Green | Special restriction | 1,466 | 3.8% |
| Blue | Special restriction | 171 | 0.4% |
| Other | Purple, Brown, White | 69 | 0.2% |

**Critical Understanding**:
- **Meter-level cap color**: From Parking Meters dataset - general meter attribute
- **Policy-level cap color**: From Meter Policies dataset - **only populated for OP (paid operation) schedules**
- **FREE and PRE schedules**: Have NO cap color in policies (empty field) because they don't have vehicle restrictions
- **OP schedules**: Have cap color specified (e.g., Yellow, Red) to indicate vehicle type restrictions during paid hours

**Example**: PostID 218-40030
- Monday 7:00-12:00 OP: Yellow (commercial vehicles only)
- Monday 12:00-15:00 OP: Yellow (commercial vehicles only)
- Monday 15:00-18:00 OP: Yellow (commercial vehicles only)
- Monday 18:00-24:00 FREE: (no cap color - no restriction)
- Monday 0:00-4:30 FREE: (no cap color - no restriction)

## Policy Validity

**Critical Rule**: Only policies where the queried date falls within [startdate, enddate] are valid.

Example:
```python
def is_policy_valid(policy, query_date):
    """Check if policy is active for the queried date"""
    start = parse_date(policy['startdate'])
    end = parse_date(policy['enddate'])
    return start <= query_date <= end
```

Most policies have:
- `startdate`: 2026-01-12T00:00:00.000
- `enddate`: 2200-12-31T00:00:00.000

This indicates long-term active policies.

## Integration Implementation

### Step 1: Load Parking Meters (Primary)
```python
meters_df = fetch_data_as_dataframe(PARKING_METERS_ID, app_token)

# Extract key fields
for _, meter in meters_df.iterrows():
    meter_data = {
        'post_id': meter['post_id'],
        'cap_color': meter['cap_color'],  # Vehicle restriction
        'cnn': meter['street_seg_ctrln_id'],
        'location': {
            'type': 'Point',
            'coordinates': [float(meter['longitude']), float(meter['latitude'])]
        },
        'street_num': meter['street_num'],
        'street_name': meter['street_name'],
        'blockface_id': meter['blockface_id']
    }
```

### Step 2: Load Meter Policies (Supplemental)
```python
policies_df = fetch_data_as_dataframe(METER_POLICIES_ID, app_token)

# Group policies by postID
policies_by_post = {}
for _, policy in policies_df.iterrows():
    post_id = policy['postid']
    
    if post_id not in policies_by_post:
        policies_by_post[post_id] = {
            'parking_space_id': policy['parkingspaceid'],  # From policies!
            'policies': []
        }
    
    policies_by_post[post_id]['policies'].append({
        'schedule_type': policy['scheduletype'],  # FREE, PRE, OP
        'day_of_week': policy['dayofweek'],       # Mo, Tu, We, etc.
        'start_time': policy['starttime'],         # 24-hour format
        'end_time': policy['endtime'],
        'time_limit_minutes': policy['timelimitminutes'],
        'hourly_rate': policy['hourlyrate'],
        'start_date': policy['startdate'],         # Validity period
        'end_date': policy['enddate'],
        'cap_color': policy['capcolor']            # Also in policies
    })
```

### Step 3: Merge and Attach to Street Segments
```python
# When attaching meters to street segments
for segment in all_segments:
    if segment['cnn'] == meter_cnn and segment['side'] == meter_side:
        meter_info = {
            'post_id': post_id,
            'parking_space_id': policies_by_post.get(post_id, {}).get('parking_space_id'),
            'cap_color': meter_data['cap_color'],  # From Parking Meters
            'location': meter_data['location'],
            'policies': policies_by_post.get(post_id, {}).get('policies', [])
        }
        segment['meters'].append(meter_info)
```

## Query-Time Logic

When a user queries parking availability at a specific date/time:

```python
def get_active_policy(meter, query_datetime):
    """Get the active policy for a meter at query time"""
    query_date = query_datetime.date()
    query_time = query_datetime.time()
    query_day = query_datetime.strftime('%a')[:2]  # Mo, Tu, We, etc.
    
    for policy in meter['policies']:
        # 1. Check date validity
        if not (policy['start_date'] <= query_date <= policy['end_date']):
            continue
        
        # 2. Check day of week
        if policy['day_of_week'] != query_day:
            continue
        
        # 3. Check time window
        if not (policy['start_time'] <= query_time <= policy['end_time']):
            continue
        
        # 4. Apply schedule type logic
        if policy['schedule_type'] == 'FREE':
            return {
                'status': 'free',
                'restrictions': None,
                'time_limit': None
            }
        
        elif policy['schedule_type'] == 'PRE':
            return {
                'status': 'prepay_allowed',
                'enforcement_start': policy['start_time'],
                'note': 'Prepaid time includes free time before enforcement'
            }
        
        elif policy['schedule_type'] == 'OP':
            return {
                'status': 'paid',
                'rate': policy['hourly_rate'],
                'time_limit': policy['time_limit_minutes'],
                'vehicle_restriction': meter['cap_color']
            }
    
    return {'status': 'no_policy', 'note': 'No active policy for this time'}
```

## Data Model Updates

### Update models.py

```python
class MeterPolicy(BaseModel):
    schedule_type: str  # 'FREE', 'PRE', 'OP', 'ALT', 'TOW'
    day_of_week: str    # 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'
    start_time: str     # 24-hour format: "9:00", "18:00"
    end_time: str       # 24-hour format
    start_date: str     # ISO format: "2026-01-12T00:00:00.000"
    end_date: str       # ISO format
    time_limit_minutes: Optional[int] = None  # For OP schedules
    hourly_rate: Optional[str] = None         # For OP schedules
    cap_color: Optional[str] = None           # Also in policies

class Meter(BaseModel):
    post_id: str
    parking_space_id: Optional[str] = None  # From Meter Policies!
    cap_color: str                          # From Parking Meters (primary)
    location: Dict                          # GeoJSON Point
    policies: List[MeterPolicy] = []        # Operating schedules
```

## Summary

✓ **Parking Space ID**: Comes from Meter Policies dataset (`parkingspaceid` field)  
✓ **Cap Color**: Comes from Parking Meters dataset (primary source)  
✓ **PostID**: Join key between both datasets  
✓ **100% Coverage**: All meter policies reference valid parking meters  
✓ **Multiple Policies**: Single meter can have multiple policies by day/time  
✓ **Date Validation**: Only policies within [startdate, enddate] are valid  
✓ **Time Windows**: Each schedule type applies only during its [starttime, endtime]  

## Implementation Priority

1. Update `ingest_data_cnn_segments.py` to load Meter Policies
2. Extract `parkingspaceid` from policies (not from meters!)
3. Group policies by `postid`
4. Validate policies by date range before attaching
5. Attach both `parking_space_id` and `policies` array to each meter
6. Use `cap_color` from Parking Meters as the authoritative source