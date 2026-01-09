"""
Check if all meters without schedules fall within the geo boundaries of 
itv4-r6g6 (Special Events or Evening Meter Area)
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
from shapely.geometry import Point, shape
import json

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METER_OPERATING_SCHEDULES_ID = "6cqg-dxku"
PARKING_METERS_ID = "8vzz-qzz9"
SPECIAL_EVENT_AREAS_ID = "itv4-r6g6"  # Special Events or Evening Meter Area

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("CHECKING METERS WITHOUT SCHEDULES IN SPECIAL EVENT AREAS")
    print("="*80)
    
    # 1. Get meters without schedules
    print("\n1. Identifying meters without schedules...")
    print("-"*80)
    
    # Fetch schedules
    schedules = client.get(METER_OPERATING_SCHEDULES_ID, limit=100000)
    schedules_df = pd.DataFrame.from_records(schedules)
    schedule_postids = set(schedules_df['post_id'].unique())
    print(f"✓ Found {len(schedule_postids)} unique postIDs with schedules")
    
    # Fetch active On Street meters
    meters = client.get(PARKING_METERS_ID, limit=100000)
    meters_df = pd.DataFrame.from_records(meters)
    meters_df = meters_df[meters_df['active_meter_flag'].isin(['M', 'T'])]
    print(f"✓ Found {len(meters_df)} active meters")
    
    # Find meters without schedules
    meters_without_schedules = meters_df[~meters_df['post_id'].isin(schedule_postids)]
    print(f"\n📊 {len(meters_without_schedules)} meters do NOT have operating schedules")
    
    # Check for location data
    if 'longitude' not in meters_without_schedules.columns or 'latitude' not in meters_without_schedules.columns:
        print("❌ ERROR: Meters dataset missing longitude/latitude columns")
        return
    
    # Filter meters with valid locations
    meters_with_loc = meters_without_schedules[
        meters_without_schedules['longitude'].notna() & 
        meters_without_schedules['latitude'].notna()
    ].copy()
    
    print(f"✓ {len(meters_with_loc)} meters have location data")
    
    # 2. Fetch Special Event Areas
    print("\n\n2. Fetching Special Events/Evening Meter Areas (itv4-r6g6)...")
    print("-"*80)
    
    try:
        geo_data = client.get(SPECIAL_EVENT_AREAS_ID, limit=50000)
        geo_df = pd.DataFrame.from_records(geo_data)
        
        print(f"✓ Fetched {len(geo_df)} geo boundary records")
        print(f"\nColumns: {list(geo_df.columns)}")
        
        # Show area types
        if 'areatype' in geo_df.columns:
            print(f"\nArea types in dataset:")
            for area_type in geo_df['areatype'].unique():
                count = len(geo_df[geo_df['areatype'] == area_type])
                print(f"  - {area_type}: {count} record(s)")
        
    except Exception as e:
        print(f"❌ ERROR fetching geo boundaries: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Parse geo boundaries
    print("\n\n3. Parsing geo boundary shapes...")
    print("-"*80)
    
    geo_shapes = []
    for idx, row in geo_df.iterrows():
        if 'shape' in row and row['shape']:
            try:
                # Parse the shape geometry
                if isinstance(row['shape'], str):
                    geom_data = json.loads(row['shape'])
                else:
                    geom_data = row['shape']
                
                geom = shape(geom_data)
                area_type = row.get('areatype', 'Unknown')
                geo_shapes.append({
                    'geometry': geom,
                    'areatype': area_type,
                    'bounds': geom.bounds  # (minx, miny, maxx, maxy)
                })
                
            except Exception as e:
                print(f"  ⚠ Error parsing shape for {row.get('areatype', 'Unknown')}: {e}")
    
    print(f"✓ Successfully parsed {len(geo_shapes)} boundary shapes")
    for gs in geo_shapes:
        bounds = gs['bounds']
        print(f"  - {gs['areatype']}: Bounds ({bounds[0]:.4f}, {bounds[1]:.4f}) to ({bounds[2]:.4f}, {bounds[3]:.4f})")
    
    # 4. Check which meters fall within boundaries
    print("\n\n4. Checking if meters fall within Special Event/Evening Meter Areas...")
    print("-"*80)
    
    meters_in_boundary = []
    meters_outside_boundary = []
    meters_by_area_type = {}
    
    for idx, meter in meters_with_loc.iterrows():
        try:
            lon = float(meter['longitude'])
            lat = float(meter['latitude'])
            point = Point(lon, lat)
            
            in_boundary = False
            matched_area_type = None
            
            for gs in geo_shapes:
                if gs['geometry'].contains(point):
                    in_boundary = True
                    matched_area_type = gs['areatype']
                    break
            
            if in_boundary:
                meters_in_boundary.append({
                    'post_id': meter['post_id'],
                    'street_name': meter.get('street_name', 'N/A'),
                    'street_num': meter.get('street_num', 'N/A'),
                    'area_type': matched_area_type,
                    'lon': lon,
                    'lat': lat
                })
                
                # Count by area type
                if matched_area_type not in meters_by_area_type:
                    meters_by_area_type[matched_area_type] = 0
                meters_by_area_type[matched_area_type] += 1
            else:
                meters_outside_boundary.append({
                    'post_id': meter['post_id'],
                    'street_name': meter.get('street_name', 'N/A'),
                    'street_num': meter.get('street_num', 'N/A'),
                    'lon': lon,
                    'lat': lat
                })
                
        except Exception as e:
            print(f"  ⚠ Error checking meter {meter.get('post_id', 'Unknown')}: {e}")
    
    # 5. Results
    print("\n\n5. RESULTS")
    print("="*80)
    
    total_checked = len(meters_in_boundary) + len(meters_outside_boundary)
    pct_inside = (len(meters_in_boundary) / total_checked * 100) if total_checked > 0 else 0
    
    print(f"\n📊 GEO BOUNDARY ANALYSIS:")
    print(f"  ✓ {len(meters_in_boundary)} meters WITHOUT schedules are INSIDE Special Event/Evening Meter Areas")
    print(f"  ✓ {len(meters_outside_boundary)} meters WITHOUT schedules are OUTSIDE these areas")
    print(f"\n  📈 {pct_inside:.1f}% of meters without schedules fall within the geo boundaries")
    
    # Breakdown by area type
    if meters_by_area_type:
        print(f"\n📊 Breakdown by Area Type:")
        for area_type, count in sorted(meters_by_area_type.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(meters_in_boundary) * 100)
            print(f"  - {area_type}: {count} meters ({pct:.1f}%)")
    
    # Show sample meters inside boundaries
    if meters_in_boundary:
        print(f"\n✅ Sample meters INSIDE Special Event/Evening Meter Areas:")
        for meter in meters_in_boundary[:10]:
            print(f"  - PostID {meter['post_id']}: {meter['street_num']} {meter['street_name']} ({meter['area_type']})")
    
    # Show sample meters outside boundaries
    if meters_outside_boundary:
        print(f"\n⚠ Sample meters OUTSIDE Special Event/Evening Meter Areas:")
        for meter in meters_outside_boundary[:10]:
            print(f"  - PostID {meter['post_id']}: {meter['street_num']} {meter['street_name']}")
    
    # 6. Final Answer
    print("\n\n6. FINAL ANSWER")
    print("="*80)
    
    if len(meters_outside_boundary) == 0:
        print(f"\n✅ YES - ALL {len(meters_in_boundary)} meters without schedules fall within")
        print(f"   the Special Events or Evening Meter Area boundaries (itv4-r6g6)")
    elif pct_inside >= 95:
        print(f"\n✅ MOSTLY YES - {pct_inside:.1f}% of meters without schedules fall within")
        print(f"   the Special Events or Evening Meter Area boundaries")
        print(f"   Only {len(meters_outside_boundary)} meters are outside these areas")
    else:
        print(f"\n❌ NO - Only {pct_inside:.1f}% of meters without schedules fall within")
        print(f"   the Special Events or Evening Meter Area boundaries")
        print(f"   {len(meters_outside_boundary)} meters are outside these areas")
    
    client.close()

if __name__ == "__main__":
    main()