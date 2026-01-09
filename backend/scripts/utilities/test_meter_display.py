#!/usr/bin/env python3
"""Test meter schedule display formatting"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from generate_interpretation_layer import InterpretationGenerator

load_dotenv()

async def test_meter_display():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client.curby
    
    # Find a segment with meters and schedules
    segment = await db.street_segments.find_one({
        'meters': {'$exists': True, '$ne': []},
        'schedules': {'$exists': True, '$ne': []}
    })
    
    if segment:
        print('='*80)
        print(f"Testing: {segment.get('street')} ({segment.get('cardinalDirection')})")
        print(f"CNN: {segment.get('cnn')}")
        print('='*80)
        
        meters = segment.get('meters', [])
        schedules = segment.get('schedules', [])
        rules = segment.get('rules', [])
        
        print(f"\nMeters: {len(meters)}")
        print(f"Schedules: {len(schedules)}")
        print(f"Rules: {len(rules)}")
        
        # Check schedule data
        print(f"\n--- Sample Schedules ---")
        for i, sched in enumerate(schedules[:3], 1):
            print(f"\nSchedule {i}:")
            print(f"  Type: {sched.get('schedule_type')}")
            print(f"  Days: {sched.get('days_applied')}")
            print(f"  From: {sched.get('from_time')}")
            print(f"  To: {sched.get('to_time')}")
            print(f"  Limit: {sched.get('time_limit_minutes')}")
            print(f"  Rate: {sched.get('rate_per_hour')}")
        
        # Generate interpretation
        print(f"\n--- Generating Interpretation ---")
        generator = InterpretationGenerator()
        interpretation = generator.generate_interpretation(segment)
        
        print(f"\n=== RULES DISPLAY OUTPUT ===")
        rules_display = interpretation.get('rules_display', [])
        if rules_display:
            for i, rule_display in enumerate(rules_display, 1):
                print(f"{i}. {rule_display}")
        else:
            print("(empty)")
        
        print(f"\n=== NEXT RESTRICTION ===")
        next_rest = interpretation.get('next_restriction')
        if next_rest:
            print(f"Display: {next_rest.get('display')}")
            print(f"Days until: {next_rest.get('days_until')}")
        else:
            print("None")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_meter_display())