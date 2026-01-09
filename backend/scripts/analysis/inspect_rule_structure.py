import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def inspect_rules():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.curby
    
    # Get one segment with rules
    segment = await db.street_segments.find_one({"rules": {"$exists": True, "$ne": []}})
    
    if segment:
        print("=" * 80)
        print("SAMPLE SEGMENT")
        print("=" * 80)
        print(f"Segment ID: {segment.get('id')}")
        print(f"CNN: {segment.get('cnn')}")
        print(f"Side: {segment.get('side')}")
        print(f"Street: {segment.get('streetName')}")
        print(f"Total Rules: {len(segment.get('rules', []))}")
        
        print("\n" + "=" * 80)
        print("RULE STRUCTURE (First 3 rules)")
        print("=" * 80)
        
        rules = segment.get('rules', [])[:3]
        for i, rule in enumerate(rules, 1):
            print(f"\n--- Rule {i} ---")
            print(json.dumps(rule, indent=2, default=str))
        
        print("\n" + "=" * 80)
        print("AVAILABLE FIELDS IN RULES")
        print("=" * 80)
        
        if rules:
            all_fields = set()
            for rule in segment.get('rules', []):
                all_fields.update(rule.keys())
            
            print("Fields found across all rules:")
            for field in sorted(all_fields):
                print(f"  - {field}")
    else:
        print("No segments with rules found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(inspect_rules())