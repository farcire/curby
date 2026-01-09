"""
Check how many meters in the ENTIRE active meter dataset fall within 
Special Events or Evening Meter Area boundaries (itv4-r6g6)
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
from shapely.geometry import Point, shape
import json

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
PARKING_METERS_ID = "8vzz-qzz9"
SPECIAL_EVENT_AREAS_ID = "itv4-r6g6"

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("CHECKING ALL ACTIVE METERS IN SPECIAL EVENT AREAS")
    print("="*80)
    
    # 1. Fetch all active On Street meters
    print("\n1. Fetching all active On Street meters...")
    print("-"*80)
    
    meters = client.get(PARKING_METERS_ID, limit=100000)
    meters_df = pd.DataFrame.from_records(meters)
    
    # Filter for active meters
    meters_df = meters_df[meters_df['active_meter_flag'].isin(['M', 'T'])]
    print(f"✓ Found {len(meters_df)} active meters")
    
    # Filter meters with valid locations
    meters_with_loc = meters_df[
        meters_df['longitude'].notna() & 
        meters_df['latitude'].notna()
    ].copy()
    
    print(f"✓ {len(meters_with_loc)} meters have location data")
    
    # 2. Fetch Special Event Areas
    print("\n\n2. Fetching Special Events/Evening Meter Areas (itv4-r6g6)...")
    print("-"*80)
    
    geo_data = client.get(SPECIAL_EVENT_AREAS_ID, limit=50000)
    geo_df = pd.DataFrame.from_records(geo_data)
    
    print(f"✓ Fetched {len(geo_df)} geo boundary records")
    
    if 'areatype' in geo_df.columns:
        print(f"\nArea types:")
        for area_type in geo_df['areatype'].unique():
            print(f"  - {area_type}")
    
    # 3. Parse geo boundaries
    print("\n\n3. Parsing geo boundary shapes...")
    print("-"*80)
    
    geo_shapes = []
    for idx, row in geo_df.iterrows():
        if 'shape' in row and row['shape']:
            try:
                if isinstance(row['shape'], str):
                    geom_data = json.loads(row['shape'])
                else:
                    geom_data = row['shape']
                
                geom = shape(geom_data)
                area_type = row.get('areatype', 'Unknown')
                geo_shapes.append({
                    'geometry': geom,
                    'areatype': area_type
                })
                
            except Exception as e:
                print(f"  ⚠ Error parsing shape: {e}")
    
    print(f"✓ Successfully parsed {len(geo_shapes)} boundary shapes")
    
    # 4. Check which meters fall within boundaries
    print("\n\n4. Checking ALL active meters against Special Event areas...")
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
                    'area_type': matched_area_type
                })
                
                if matched_area_type not in meters_by_area_type:
                    meters_by_area_type[matched_area_type] = 0
                meters_by_area_type[matched_area_type] += 1
            else:
                meters_outside_boundary.append(meter['post_id'])
                
        except Exception as e:
            pass
    
    # 5. Results
    print("\n\n5. FINAL RESULTS")
    print("="*80)
    
    total_checked = len(meters_in_boundary) + len(meters_outside_boundary)
    pct_inside = (len(meters_in_boundary) / total_checked * 100) if total_checked > 0 else 0
    
    print(f"\n📊 SPECIAL EVENT AREA ANALYSIS (ALL ACTIVE METERS):")
    print(f"  ✓ Total active meters checked: {total_checked}")
    print(f"  ✓ Meters INSIDE Special Event/Evening Meter Areas: {len(meters_in_boundary)}")
    print(f"  ✓ Meters OUTSIDE these areas: {len(meters_outside_boundary)}")
    print(f"\n  📈 {pct_inside:.1f}% of ALL active meters are in Special Event/Evening Meter Areas")
    
    # Breakdown by area type
    if meters_by_area_type:
        print(f"\n📊 Breakdown by Area Type:")
        for area_type, count in sorted(meters_by_area_type.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(meters_in_boundary) * 100)
            print(f"  - {area_type}: {count} meters ({pct:.1f}% of special area meters)")
    
    # Show sample meters in each area
    print(f"\n✅ Sample meters in Special Event/Evening Meter Areas:")
    for area_type in meters_by_area_type.keys():
        area_meters = [m for m in meters_in_boundary if m['area_type'] == area_type]
        print(f"\n  {area_type} ({len(area_meters)} meters):")
        for meter in area_meters[:5]:
            print(f"    - PostID {meter['post_id']}")
    
    print(f"\n\n6. SUMMARY FOR CNN MASTER FILE")
    print("="*80)
    print(f"\n✅ {len(meters_in_boundary)} meters should be flagged as 'special_event_meter' in CNN Master File")
    print(f"\nThese meters will have special handling for:")
    print(f"  - Dynamic pricing during events")
    print(f"  - Extended operating hours")
    print(f"  - Special event policies")
    
    client.close()

if __name__ == "__main__":
    main()