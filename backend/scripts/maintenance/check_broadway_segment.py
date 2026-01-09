import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def check_broadway_segment():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.curby
    
    # Find Broadway segment
    segment = await db.street_segments.find_one({
        "streetName": "BROADWAY",
        "cardinalDirection": "North",
        "fromAddress": {"$gte": "100", "$lte": "198"}
    })
    
    if not segment:
        print("Segment not found")
        return
    
    print("=" * 80)
    print(f"BROADWAY (North, {segment.get('fromAddress')}-{segment.get('toAddress')})")
    print("=" * 80)
    
    # Check rules
    rules = segment.get('rules', [])
    print(f"\n📋 RULES ({len(rules)} total):")
    for i, rule in enumerate(rules, 1):
        print(f"\n  Rule {i}:")
        print(f"    Type: {rule.get('type')}")
        print(f"    Days: {rule.get('activeDays')} -> {rule.get('displayDays')}")
        print(f"    Time: {rule.get('startTimeMin')}-{rule.get('endTimeMin')} -> {rule.get('displayTime')}")
        print(f"    Description: {rule.get('description')}")
    
    # Check meters
    meters = segment.get('meters', [])
    schedules = segment.get('schedules', [])
    print(f"\n💰 METERS: {len(meters)} meters, {len(schedules)} schedules")
    if meters:
        print(f"  First meter: {meters[0].get('post_id')}")
    
    # Check interpretation
    interp = segment.get('interpretation', {})
    print(f"\n🔍 INTERPRETATION:")
    print(f"  Version: {interp.get('version')}")
    print(f"  Generated: {interp.get('generated_at')}")
    print(f"  Rules Display: {interp.get('rules_display')}")
    meter_info = interp.get('meter_info', {})
    print(f"  Meter Info:")
    print(f"    has_meters: {meter_info.get('has_meters')}")
    print(f"    meter_count: {meter_info.get('meter_count')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_broadway_segment())