import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from sodapy import Socrata
import pandas as pd
import json

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SFMTA_DOMAIN = "data.sfgov.org"
STREET_CLEANING_SCHEDULES_ID = "yhqp-riqs"
PARKING_REGULATIONS_ID = "hi6h-neyh"
STREETS_DATASET_ID = "3psu-pn9h"

async def inspect_cnn_961000():
    """Investigate all raw data for CNN 961000"""
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    mongodb_uri = os.getenv("MONGODB_URI")
    
    print("=" * 80)
    print("INVESTIGATING CNN 961000 - RAW DATASET ANALYSIS")
    print("=" * 80)
    
    # ==========================================
    # 1. Check MongoDB for existing data
    # ==========================================
    print("\n" + "=" * 80)
    print("1. MONGODB DATA FOR CNN 961000")
    print("=" * 80)
    
    if mongodb_uri:
        client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
        try:
            db = client.get_default_database()
        except:
            db = client["curby"]
        
        # Check street_segments collection
        print("\n--- Street Segments Collection ---")
        segments = await db.street_segments.find({"cnn": "961000"}).to_list(length=100)
        print(f"Found {len(segments)} segments for CNN 961000")
        
        for i, seg in enumerate(segments):
            print(f"\nSegment {i+1}:")
            print(f"  CNN: {seg.get('cnn')}")
            print(f"  Side: {seg.get('side')}")
            print(f"  Street Name: {seg.get('streetName')}")
            print(f"  From Street: {seg.get('fromStreet')}")
            print(f"  To Street: {seg.get('toStreet')}")
            print(f"  From Address: {seg.get('fromAddress')}")
            print(f"  To Address: {seg.get('toAddress')}")
            print(f"  Cardinal Direction: {seg.get('cardinalDirection')}")
            print(f"  Display Name: {seg.get('displayName')}")
            print(f"  Number of Rules: {len(seg.get('rules', []))}")
            print(f"  Number of Schedules: {len(seg.get('schedules', []))}")
            
            # Show rules
            if seg.get('rules'):
                print(f"\n  Rules:")
                for j, rule in enumerate(seg.get('rules', [])):
                    print(f"    Rule {j+1}:")
                    print(f"      Type: {rule.get('type')}")
                    print(f"      Description: {rule.get('description')}")
                    if rule.get('type') == 'street-sweeping':
                        print(f"      Day: {rule.get('day')}")
                        print(f"      Time: {rule.get('startTime')} - {rule.get('endTime')}")
                        print(f"      Blockside: {rule.get('blockside')}")
                        print(f"      Limits: {rule.get('limits')}")
                    else:
                        print(f"      Regulation: {rule.get('regulation')}")
                        print(f"      Days: {rule.get('days')}")
                        print(f"      Hours: {rule.get('hours')}")
                        print(f"      From Time: {rule.get('fromTime')}")
                        print(f"      To Time: {rule.get('toTime')}")
                        print(f"      Time Limit: {rule.get('timeLimit')}")
                        print(f"      Permit Area: {rule.get('permitArea')}")
        
        client.close()
    
    # ==========================================
    # 2. Query Socrata for raw street data
    # ==========================================
    print("\n" + "=" * 80)
    print("2. RAW ACTIVE STREETS DATA (Socrata)")
    print("=" * 80)
    
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("\n--- Active Streets Dataset ---")
    streets_results = client.get(STREETS_DATASET_ID, cnn="961000", limit=10)
    print(f"Found {len(streets_results)} records")
    
    for i, record in enumerate(streets_results):
        print(f"\nRecord {i+1}:")
        print(f"  CNN: {record.get('cnn')}")
        print(f"  Street Name: {record.get('streetname')}")
        print(f"  Street Type: {record.get('st_type')}")
        print(f"  Layer: {record.get('layer')}")
        print(f"  Zip Code: {record.get('zip_code')}")
        print(f"  Left From Address: {record.get('lf_fadd')}")
        print(f"  Left To Address: {record.get('lf_toadd')}")
        print(f"  Right From Address: {record.get('rt_fadd')}")
        print(f"  Right To Address: {record.get('rt_toadd')}")
        print(f"  Geometry Type: {record.get('line', {}).get('type') if record.get('line') else 'None'}")
        
        # Show all available fields
        print(f"\n  All Available Fields:")
        for key in sorted(record.keys()):
            if key not in ['line', 'shape']:  # Skip geometry fields for readability
                print(f"    {key}: {record.get(key)}")
    
    # ==========================================
    # 3. Query Socrata for street cleaning
    # ==========================================
    print("\n" + "=" * 80)
    print("3. RAW STREET CLEANING DATA (Socrata)")
    print("=" * 80)
    
    print("\n--- Street Cleaning Schedules Dataset ---")
    cleaning_results = client.get(STREET_CLEANING_SCHEDULES_ID, cnn="961000", limit=100)
    print(f"Found {len(cleaning_results)} records")
    
    for i, record in enumerate(cleaning_results):
        print(f"\nRecord {i+1}:")
        print(f"  CNN: {record.get('cnn')}")
        print(f"  CNN Right/Left: {record.get('cnnrightleft')}")
        print(f"  Weekday: {record.get('weekday')}")
        print(f"  From Hour: {record.get('fromhour')}")
        print(f"  To Hour: {record.get('tohour')}")
        print(f"  Week: {record.get('week')}")
        print(f"  Blockside: {record.get('blockside')}")
        print(f"  Limits: {record.get('limits')}")
        print(f"  Corridor: {record.get('corridor')}")
        print(f"  Holidays: {record.get('holidays')}")
        
        # Show all available fields
        print(f"\n  All Available Fields:")
        for key in sorted(record.keys()):
            print(f"    {key}: {record.get(key)}")
    
    # ==========================================
    # 4. Query Socrata for parking regulations
    # ==========================================
    print("\n" + "=" * 80)
    print("4. RAW PARKING REGULATIONS DATA (Socrata)")
    print("=" * 80)
    
    print("\n--- Parking Regulations Dataset ---")
    # Note: Parking regulations don't have CNN field, need to search by geometry proximity
    # For now, let's get a sample and see the structure
    print("Note: Parking regulations are matched by geometry, not CNN directly")
    print("Fetching sample records to show structure...")
    
    sample_regs = client.get(PARKING_REGULATIONS_ID, limit=5)
    print(f"\nSample of {len(sample_regs)} parking regulation records:")
    
    for i, record in enumerate(sample_regs):
        print(f"\nSample Record {i+1}:")
        print(f"  Regulation: {record.get('regulation')}")
        print(f"  Days: {record.get('days')}")
        print(f"  Hours: {record.get('hours')}")
        print(f"  From Time: {record.get('from_time')}")
        print(f"  To Time: {record.get('to_time')}")
        print(f"  HR Limit: {record.get('hrlimit')}")
        print(f"  RPP Area 1: {record.get('rpparea1')}")
        print(f"  RPP Area 2: {record.get('rpparea2')}")
        print(f"  Reg Details: {record.get('regdetails')}")
        print(f"  Exceptions: {record.get('exceptions')}")
        print(f"  Geometry Type: {record.get('shape', {}).get('type') if record.get('shape') else 'None'}")
        
        # Show all available fields
        print(f"\n  All Available Fields:")
        for key in sorted(record.keys()):
            if key not in ['shape', 'geometry']:  # Skip geometry for readability
                print(f"    {key}: {record.get(key)}")
        break  # Just show one detailed example
    
    # ==========================================
    # 5. Export to JSON for detailed analysis
    # ==========================================
    print("\n" + "=" * 80)
    print("5. EXPORTING DATA TO JSON FILES")
    print("=" * 80)
    
    output_dir = os.path.join(os.path.dirname(__file__), "cnn_961000_investigation")
    os.makedirs(output_dir, exist_ok=True)
    
    # Export streets data
    streets_file = os.path.join(output_dir, "streets_961000.json")
    with open(streets_file, 'w') as f:
        json.dump(streets_results, f, indent=2)
    print(f"✓ Exported streets data to: {streets_file}")
    
    # Export cleaning data
    cleaning_file = os.path.join(output_dir, "cleaning_961000.json")
    with open(cleaning_file, 'w') as f:
        json.dump(cleaning_results, f, indent=2)
    print(f"✓ Exported cleaning data to: {cleaning_file}")
    
    # Export sample regulations
    regs_file = os.path.join(output_dir, "sample_regulations.json")
    with open(regs_file, 'w') as f:
        json.dump(sample_regs, f, indent=2)
    print(f"✓ Exported sample regulations to: {regs_file}")
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    print(f"\nAll data exported to: {output_dir}/")
    print("\nKey Findings:")
    print(f"  - Active Streets records: {len(streets_results)}")
    print(f"  - Street Cleaning records: {len(cleaning_results)}")
    print(f"  - Parking regulations are matched by geometry (not CNN)")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(inspect_cnn_961000())