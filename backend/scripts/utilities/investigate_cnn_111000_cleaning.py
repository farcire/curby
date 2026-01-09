#!/usr/bin/env python3
"""
Investigate CNN 111000 (01st Street) street cleaning data discrepancy.
User reports visual check shows:
- R side: Street Cleaning 12:01am - 6am Wednesday
- L side: 12:01am-6am Thursday

But our data shows different information.
"""

import json
import requests

def check_datasf_source():
    """Query DataSF directly for CNN 111000 street cleaning data"""
    print("=== Querying DataSF for CNN 111000 Street Cleaning ===\n")
    
    # DataSF Street Sweeping Schedule endpoint
    url = "https://data.sfgov.org/resource/yhqp-riqs.json"
    
    # Query for CNN 111000
    params = {
        "$where": "cnn = '111000'",
        "$limit": 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"Found {len(data)} records for CNN 111000 in DataSF\n")
        
        for record in data:
            print(f"CNN: {record.get('cnn')}")
            print(f"Street Name: {record.get('streetname')}")
            print(f"Block Side: {record.get('blockside')}")
            print(f"Week Day: {record.get('weekday')}")
            print(f"From Hour: {record.get('fromhour')}")
            print(f"To Hour: {record.get('tohour')}")
            print(f"CNN LF: {record.get('cnnlf')}")
            print(f"CNN RT: {record.get('cnnrt')}")
            print(f"Limits: {record.get('lf_fadd')} - {record.get('lf_toadd')}")
            print(f"Corridor: {record.get('corridor')}")
            print("-" * 60)
        
        return data
    except Exception as e:
        print(f"Error querying DataSF: {e}")
        return []

def check_local_data():
    """Check our local segments_with_sweeping_rules.json"""
    print("\n=== Checking Local Data (segments_with_sweeping_rules.json) ===\n")
    
    try:
        with open('segments_with_sweeping_rules.json', 'r') as f:
            segments = json.load(f)
        
        cnn_111000 = [s for s in segments if s.get('cnn') == '111000']
        
        print(f"Found {len(cnn_111000)} segments for CNN 111000 in local data\n")
        
        for seg in cnn_111000:
            print(f"Side: {seg.get('side')}")
            print(f"Display: {seg.get('display_name')}")
            print(f"Blockside: {seg.get('blockside')}")
            
            schedules = seg.get('street_cleaning_schedules', [])
            print(f"Schedules: {len(schedules)}")
            for sched in schedules:
                print(f"  - {sched.get('description')}")
                print(f"    Day: {sched.get('day')}, Time: {sched.get('startTime')}-{sched.get('endTime')}")
            print("-" * 60)
        
        return cnn_111000
    except Exception as e:
        print(f"Error reading local data: {e}")
        return []

def check_meter_data():
    """Check if CNN 111000 has meter data"""
    print("\n=== Checking for Meter Data ===\n")
    
    # Query DataSF for meters on CNN 111000
    url = "https://data.sfgov.org/resource/8vzz-qzz9.json"
    
    params = {
        "$where": "cnn = '111000'",
        "$limit": 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"Found {len(data)} meters for CNN 111000\n")
        
        for meter in data:
            print(f"Meter ID: {meter.get('post_id')}")
            print(f"Street: {meter.get('street_name')}")
            print(f"Address: {meter.get('street_num')}")
            print(f"Cap Color: {meter.get('cap_color')}")
            print(f"Rate Area: {meter.get('rate_area')}")
            print(f"Meter Type: {meter.get('meter_type')}")
            
            # Check for operation schedule
            if 'active_meter_flag' in meter:
                print(f"Active: {meter.get('active_meter_flag')}")
            
            print("-" * 60)
        
        return data
    except Exception as e:
        print(f"Error querying meters: {e}")
        return []

def main():
    print("=" * 80)
    print("CNN 111000 (01st Street) Investigation")
    print("User Report: R side Wed 12:01am-6am, L side Thu 12:01am-6am")
    print("=" * 80)
    print()
    
    # Check DataSF source
    datasf_cleaning = check_datasf_source()
    
    # Check local data
    local_data = check_local_data()
    
    # Check meter data
    meter_data = check_meter_data()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"DataSF Street Cleaning Records: {len(datasf_cleaning)}")
    print(f"Local Data Segments: {len(local_data)}")
    print(f"Meters Found: {len(meter_data)}")
    
    if len(datasf_cleaning) > 0:
        print("\n✓ DataSF has street cleaning data for CNN 111000")
        print("  This suggests the data exists in the source but may not have been")
        print("  properly ingested or processed into our local database.")
    else:
        print("\n✗ No street cleaning data found in DataSF for CNN 111000")
        print("  This could indicate a data quality issue at the source.")
    
    if len(meter_data) > 0:
        print(f"\n✓ CNN 111000 is a metered location ({len(meter_data)} meters)")
        print("  Metered locations may have different or conflicting parking rules")
        print("  that could affect street cleaning schedule display.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()