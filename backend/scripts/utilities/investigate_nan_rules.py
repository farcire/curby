plsimport asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def investigate_nan_rules():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client.curby
    
    # Get a segment with rules missing descriptions
    segment = await db.street_segments.find_one({
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
    
    if segment:
        print("=" * 80)
        print("SEGMENT WITH PROBLEMATIC RULES")
        print("=" * 80)
        print(f"CNN: {segment.get('cnn')}")
        print(f"Side: {segment.get('side')}")
        print(f"Street: {segment.get('streetName')}")
        
        # Find rules without descriptions
        rules_without_desc = [r for r in segment.get('rules', []) if not r.get('description')]
        
        print(f"\nProblematic Rules: {len(rules_without_desc)}")
        
        for i, rule in enumerate(rules_without_desc[:2], 1):
            print(f"\n--- Rule {i} (FULL DETAILS) ---")
            print(json.dumps(rule, indent=2, default=str))
            
            # Analyze what's wrong
            print(f"\nAnalysis:")
            print(f"  - Type: {rule.get('type')}")
            print(f"  - Days field: {repr(rule.get('days'))}")
            print(f"  - Hours field: {repr(rule.get('hours'))}")
            print(f"  - Regulation: {repr(rule.get('regulation'))}")
            print(f"  - Has activeDays: {bool(rule.get('activeDays'))}")
            print(f"  - activeDays value: {rule.get('activeDays')}")
            print(f"  - Has startTimeMin: {rule.get('startTimeMin') is not None}")
            print(f"  - Has endTimeMin: {rule.get('endTimeMin') is not None}")
            
            # Check if this is a data quality issue
            if str(rule.get('days')).lower() == 'nan' or not rule.get('days'):
                print(f"  ⚠️  ISSUE: Missing or NaN days field")
            if str(rule.get('hours')).lower() == 'nan' or not rule.get('hours'):
                print(f"  ⚠️  ISSUE: Missing or NaN hours field")
            if not rule.get('activeDays'):
                print(f"  ⚠️  ISSUE: activeDays array is empty")
    
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    
    # Count by rule type
    pipeline = [
        {"$unwind": "$rules"},
        {
            "$match": {
                "$or": [
                    {"rules.description": {"$exists": False}},
                    {"rules.description": None},
                    {"rules.description": ""}
                ]
            }
        },
        {
            "$group": {
                "_id": "$rules.type",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    results = await db.street_segments.aggregate(pipeline).to_list(None)
    
    print("\nRules without descriptions by type:")
    for result in results:
        print(f"  {result['_id']}: {result['count']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(investigate_nan_rules())