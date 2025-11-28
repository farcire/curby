"""
Check raw data for 18th Street CNN 868000 to see blockside field
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import asyncio
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.curby

async def check_18th_street():
    """Check raw data for 18th Street"""
    
    print("Checking CNN 868000 (18th Street) raw data")
    print("=" * 80)
    
    # Get both sides
    cursor = db.street_segments.find({"cnn": "868000"})
    segments = await cursor.to_list(length=10)
    
    for seg in segments:
        side = seg.get('side')
        print(f"\n{'='*80}")
        print(f"CNN 868000 - Side {side}")
        print(f"{'='*80}")
        print(f"Street: {seg.get('streetName')}")
        print(f"From: {seg.get('fromStreet')} to {seg.get('toStreet')}")
        print(f"Addresses: {seg.get('fromAddress')} - {seg.get('toAddress')}")
        
        # Check rules structure
        rules = seg.get('rules', [])
        print(f"\nRules ({len(rules)} total):")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Type: {rule.get('type')}")
            
            # Print ALL fields in the rule to see what's available
            print(f"    All fields in rule:")
            for key, value in rule.items():
                if key not in ['type']:
                    print(f"      {key}: {value}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_18th_street())