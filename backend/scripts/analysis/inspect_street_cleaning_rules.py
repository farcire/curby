import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def inspect_street_cleaning():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.curby
    
    # Get segments with street cleaning rules
    cursor = db.street_segments.find({"rules.type": "street-cleaning"}).limit(3)
    
    segments = await cursor.to_list(length=3)
    
    if segments:
        for seg_idx, segment in enumerate(segments, 1):
            print("=" * 80)
            print(f"SEGMENT {seg_idx}")
            print("=" * 80)
            print(f"CNN: {segment.get('cnn')}")
            print(f"Side: {segment.get('side')}")
            print(f"Street: {segment.get('streetName')}")
            
            # Find street cleaning rules
            cleaning_rules = [r for r in segment.get('rules', []) if r.get('type') == 'street-cleaning']
            print(f"Street Cleaning Rules: {len(cleaning_rules)}")
            
            for i, rule in enumerate(cleaning_rules, 1):
                print(f"\n--- Street Cleaning Rule {i} ---")
                print(f"Type: {rule.get('type')}")
                print(f"Description: {rule.get('description')}")
                print(f"Display Days: {rule.get('displayDays')}")
                print(f"Display Time: {rule.get('displayTime')}")
                print(f"Active Days: {rule.get('activeDays')}")
                print(f"Start Time Min: {rule.get('startTimeMin')}")
                print(f"End Time Min: {rule.get('endTimeMin')}")
            
            print()
    else:
        print("No segments with street cleaning rules found")
    
    # Check for rules WITHOUT descriptions
    print("\n" + "=" * 80)
    print("CHECKING FOR RULES WITHOUT DESCRIPTIONS")
    print("=" * 80)
    
    count_without_desc = await db.street_segments.count_documents({
        "rules": {
            "$elemMatch": {
                "$or": [
                    {"description": {"$exists": False}},
                    {"description": None},
                    {"description": ""}
                ]
            }
        }
    })
    
    print(f"Segments with rules missing descriptions: {count_without_desc}")
    
    if count_without_desc > 0:
        # Get a sample
        sample = await db.street_segments.find_one({
            "rules": {
                "$elemMatch": {
                    "$or": [
                        {"description": {"$exists": False}},
                        {"description": None},
                        {"description": ""}
                    ]
                }
            }
        })
        
        if sample:
            print(f"\nSample segment: CNN {sample.get('cnn')}, Side {sample.get('side')}")
            print("Rules without descriptions:")
            for rule in sample.get('rules', []):
                if not rule.get('description'):
                    print(f"  - Type: {rule.get('type')}, Days: {rule.get('days')}, Hours: {rule.get('hours')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(inspect_street_cleaning())