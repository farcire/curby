"""
Validate Mission Neighborhood Data Merge

This script checks the results of the Mission ingestion and shows
how the data layers have merged together.
"""

import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from collections import Counter

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    print("="*80)
    print("MISSION NEIGHBORHOOD DATA MERGE VALIDATION")
    print("="*80)
    
    # Get total count
    total_count = await db.blockfaces.count_documents({})
    print(f"\nTotal Blockface Segments: {total_count}")
    
    if total_count == 0:
        print("\n⚠️  No blockfaces found! The ingestion may not have run yet.")
        print("Run: python3 ingest_mission_only.py")
        client.close()
        return
    
    # Get all blockfaces
    blockfaces = await db.blockfaces.find({}).to_list(length=10000)
    
    print("\n" + "="*80)
    print("DATA LAYER COVERAGE")
    print("="*80)
    
    # Count data layers
    layer_distribution = Counter()
    with_cleaning = 0
    with_regs = 0
    with_meters = 0
    with_blockface_geo = 0
    
    for bf in blockfaces:
        layers = bf.get('data_layers', [])
        layer_distribution[len(layers)] += 1
        
        if 'street_cleaning' in layers:
            with_cleaning += 1
        if 'parking_regulations' in layers:
            with_regs += 1
        if 'parking_meters' in layers:
            with_meters += 1
        if 'blockface_geometry' in layers:
            with_blockface_geo += 1
    
    print(f"\nSegments by Number of Data Layers:")
    for count in sorted(layer_distribution.keys(), reverse=True):
        pct = (layer_distribution[count] / total_count * 100)
        print(f"  {count} layers: {layer_distribution[count]:4d} segments ({pct:5.1f}%)")
    
    print(f"\nData Layer Coverage:")
    print(f"  Active Streets (foundation):  {total_count:4d} ({100.0:5.1f}%)")
    print(f"  Blockface Geometry:           {with_blockface_geo:4d} ({with_blockface_geo/total_count*100:5.1f}%)")
    print(f"  Street Cleaning:              {with_cleaning:4d} ({with_cleaning/total_count*100:5.1f}%)")
    print(f"  Parking Regulations:          {with_regs:4d} ({with_regs/total_count*100:5.1f}%)")
    print(f"  Parking Meters:               {with_meters:4d} ({with_meters/total_count*100:5.1f}%)")
    
    # Find examples of fully merged segments
    print("\n" + "="*80)
    print("SAMPLE MERGED SEGMENTS")
    print("="*80)
    
    # Find segment with all layers
    fully_merged = [bf for bf in blockfaces if len(bf.get('data_layers', [])) >= 4]
    
    if fully_merged:
        sample = fully_merged[0]
        print(f"\n✓ Fully Merged Segment Example:")
        print(f"  Street: {sample.get('streetName')} ({sample.get('side')} side)")
        print(f"  CNN: {sample.get('cnn')}")
        print(f"  Address Range: {sample.get('fromAddress')}-{sample.get('toAddress')}")
        print(f"  Zip Code: {sample.get('zip_code')}")
        print(f"  Data Layers: {', '.join(sample.get('data_layers', []))}")
        print(f"  Total Rules: {len(sample.get('rules', []))}")
        print(f"  Meter Schedules: {len(sample.get('schedules', []))}")
        
        # Show rules
        if sample.get('rules'):
            print(f"\n  Rules:")
            for i, rule in enumerate(sample.get('rules', [])[:3], 1):
                print(f"    {i}. {rule.get('type')}: {rule.get('description', rule.get('regulation', 'N/A'))}")
    
    # Find Balmy Street example
    print("\n" + "="*80)
    print("BALMY STREET EXAMPLE (Residential)")
    print("="*80)
    
    balmy_segments = [bf for bf in blockfaces if 'BALMY' in bf.get('streetName', '').upper()]
    
    if balmy_segments:
        print(f"\nFound {len(balmy_segments)} segments on Balmy Street:")
        for bf in balmy_segments[:2]:
            print(f"\n  {bf.get('streetName')} - {bf.get('side')} side")
            print(f"    CNN: {bf.get('cnn')}")
            print(f"    Address Range: {bf.get('fromAddress')}-{bf.get('toAddress')}")
            print(f"    Data Layers: {', '.join(bf.get('data_layers', []))}")
            print(f"    Rules: {len(bf.get('rules', []))}")
            
            # Show what's merged
            for rule in bf.get('rules', []):
                if rule.get('type') == 'street-sweeping':
                    print(f"      ✓ Street Cleaning: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                elif rule.get('type') == 'parking-regulation':
                    print(f"      ✓ Parking Reg: {rule.get('regulation')}")
    else:
        print("\n  No Balmy Street segments found")
    
    # Find Valencia Street example
    print("\n" + "="*80)
    print("VALENCIA STREET EXAMPLE (Commercial)")
    print("="*80)
    
    valencia_segments = [bf for bf in blockfaces if 'VALENCIA' in bf.get('streetName', '').upper()]
    
    if valencia_segments:
        print(f"\nFound {len(valencia_segments)} segments on Valencia Street:")
        # Show one with lots of data
        valencia_with_data = sorted(valencia_segments, key=lambda x: len(x.get('rules', [])), reverse=True)
        if valencia_with_data:
            bf = valencia_with_data[0]
            print(f"\n  {bf.get('streetName')} - {bf.get('side')} side (Most Complex)")
            print(f"    CNN: {bf.get('cnn')}")
            print(f"    Address Range: {bf.get('fromAddress')}-{bf.get('toAddress')}")
            print(f"    Data Layers: {', '.join(bf.get('data_layers', []))}")
            print(f"    Total Rules: {len(bf.get('rules', []))}")
            print(f"    Meter Schedules: {len(bf.get('schedules', []))}")
            
            # Show merged data
            cleaning_rules = [r for r in bf.get('rules', []) if r.get('type') == 'street-sweeping']
            parking_rules = [r for r in bf.get('rules', []) if r.get('type') == 'parking-regulation']
            
            if cleaning_rules:
                print(f"\n    Street Cleaning ({len(cleaning_rules)} schedules):")
                for rule in cleaning_rules[:2]:
                    print(f"      • {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
            
            if parking_rules:
                print(f"\n    Parking Regulations ({len(parking_rules)} rules):")
                for rule in parking_rules[:3]:
                    print(f"      • {rule.get('regulation')} {rule.get('days', '')} {rule.get('hours', '')}")
            
            if bf.get('schedules'):
                print(f"\n    Parking Meters ({len(bf.get('schedules'))} meters):")
                for sched in bf.get('schedules')[:2]:
                    print(f"      • Post {sched.get('postId')}: {len(sched.get('schedules', []))} rate schedules")
    else:
        print("\n  No Valencia Street segments found")
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())