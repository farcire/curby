#!/usr/bin/env python3
"""Find a segment with valid meter schedules for display testing"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from generate_interpretation_layer import InterpretationGenerator

load_dotenv()

async def find_valid_meter_segment():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client.curby
    
    # Find segments with meters that have valid schedule data
    cursor = db.street_segments.find({
        'meters': {'$exists': True, '$ne': []},
        'schedules': {'$exists': True, '$ne': []}
    })
    
    generator = InterpretationGenerator()
    
    async for segment in cursor:
        schedules = segment.get('schedules', [])
        
        # Check if any schedule has valid data
        has_valid = False
        for sched in schedules:
            if (sched.get('days_applied') and 
                sched.get('from_time') and 
                sched.get('to_time')):
                has_valid = True
                break
        
        if has_valid:
            print('='*80)
            print(f"Found: {segment.get('street')} ({segment.get('cardinalDirection')})")
            print(f"CNN: {segment.get('cnn')}")
            print(f"Address: {segment.get('fromAddress')}-{segment.get('toAddress')}")
            print('='*80)
            
            # Generate interpretation
            interpretation = generator.generate_interpretation(segment)
            
            print(f"\n=== RULES DISPLAY ===\n")
            for i, rule in enumerate(interpretation.get('rules_display', []), 1):
                print(f"{i}. {rule}")
            
            print(f"\n=== NEXT RESTRICTION ===")
            next_rest = interpretation.get('next_restriction')
            if next_rest:
                print(f"{next_rest.get('display')} (in {next_rest.get('days_until')} days)")
            else:
                print("None")
            
            print(f"\n=== SAMPLE SCHEDULES ===")
            for i, sched in enumerate(schedules[:3], 1):
                print(f"\nSchedule {i}:")
                print(f"  Type: {sched.get('schedule_type')}")
                print(f"  Days: {sched.get('days_applied')}")
                print(f"  Time: {sched.get('from_time')} - {sched.get('to_time')}")
                print(f"  Limit: {sched.get('time_limit_minutes')} min")
                print(f"  Rate: ${sched.get('rate_per_hour')}/hr")
            
            break
    
    client.close()

if __name__ == "__main__":
    asyncio.run(find_valid_meter_segment())