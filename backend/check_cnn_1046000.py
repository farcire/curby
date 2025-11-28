#!/usr/bin/env python3
"""
Check CNN 1046000 data
"""
import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import json

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client.curby
    
    print("="*70)
    print("CHECKING CNN 1046000 - 20th St between Bryant and York")
    print("="*70)
    
    # Query for CNN 1046000
    segments = await db.street_segments.find({
        "cnn": "1046000"
    }).to_list(length=10)
    
    if not segments:
        print("\n❌ No segments found for CNN 1046000")
        print("\nChecking if it exists in raw streets collection...")
        
        street = await db.streets.find_one({"cnn": "1046000"})
        if street:
            print("✅ Found in streets collection:")
            print(f"   Street: {street.get('streetname')}")
            print(f"   Zip: {street.get('zip_code')}")
        else:
            print("❌ Not found in streets collection either")
    else:
        print(f"\n✅ Found {len(segments)} segment(s) for CNN 1046000\n")
        
        for seg in segments:
            side = seg.get('side')
            print(f"\n{'='*70}")
            print(f"CNN 1046000 - {side} SIDE")
            print('='*70)
            
            print(f"Street: {seg.get('streetName')}")
            print(f"From: {seg.get('fromStreet')} → To: {seg.get('toStreet')}")
            
            # Check rules
            rules = seg.get('rules', [])
            print(f"\nRules: {len(rules)} total")
            
            if rules:
                for i, rule in enumerate(rules, 1):
                    rule_type = rule.get('type')
                    print(f"\n  {i}. {rule_type.upper()}")
                    
                    if rule_type == 'street-sweeping':
                        print(f"     Day: {rule.get('day')}")
                        print(f"     Time: {rule.get('startTime')} - {rule.get('endTime')}")
                    
                    elif rule_type == 'parking-regulation':
                        print(f"     Regulation: {rule.get('regulation')}")
                        permit = rule.get('permitArea')
                        if permit:
                            print(f"     🅿️  RPP AREA: {permit}")
                        time_limit = rule.get('timeLimit')
                        if time_limit:
                            print(f"     Time Limit: {time_limit} hours")
                        if rule.get('days'):
                            print(f"     Days: {rule.get('days')}")
                        if rule.get('hours'):
                            print(f"     Hours: {rule.get('hours')}")
            else:
                print("  ⚠️  No rules attached to this segment")
    
    print("\n" + "="*70)
    print("EXPECTED (from visual verification):")
    print("="*70)
    print("South side (R): RPP Area W, 1hr parking 8am-6pm, Sweeping Tue 9-11am")
    print("North side (L): No RPP, Sweeping Thu 9-11am")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())