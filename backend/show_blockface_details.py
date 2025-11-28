import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def show_details():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    # Get 20th Street blockfaces first
    print("=" * 80)
    print("20TH STREET BLOCKFACES")
    print("=" * 80)
    
    street_20th = await db.blockfaces.find({
        "streetName": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    for bf in street_20th:
        print(f"\n{'='*80}")
        print(f"Street: {bf.get('streetName')}")
        print(f"CNN: {bf.get('cnn')}")
        print(f"Side: {bf.get('side')}")
        print(f"Blockface ID: {bf.get('id')}")
        
        # Try to get street range if available
        geometry = bf.get('geometry')
        if geometry:
            print(f"Geometry Type: {geometry.get('type', 'Unknown')}")
        
        rules = bf.get('rules', [])
        print(f"\nTotal Rules: {len(rules)}")
        
        # Group by rule type
        rule_types = {}
        for rule in rules:
            rule_type = rule.get('type', 'unknown')
            if rule_type not in rule_types:
                rule_types[rule_type] = []
            rule_types[rule_type].append(rule)
        
        for rule_type, type_rules in rule_types.items():
            print(f"\n{rule_type.upper()} ({len(type_rules)} rules):")
            for i, rule in enumerate(type_rules, 1):
                print(f"  Rule #{i}:")
                for key, value in rule.items():
                    if key != 'type':
                        if isinstance(value, str) and len(value) > 100:
                            print(f"    {key}: {value[:100]}...")
                        else:
                            print(f"    {key}: {value}")
    
    # Now show a few other streets with parking regulations for comparison
    print("\n\n" + "=" * 80)
    print("OTHER STREETS WITH PARKING REGULATIONS (Sample)")
    print("=" * 80)
    
    # Get a few streets with parking regulations
    sample_blockfaces = await db.blockfaces.find({
        "rules.type": "parking-regulation",
        "streetName": {"$regex": "MISSION|VALENCIA|BRYANT", "$options": "i"}
    }).limit(3).to_list(None)
    
    for bf in sample_blockfaces:
        print(f"\n{'='*80}")
        print(f"Street: {bf.get('streetName')}")
        print(f"CNN: {bf.get('cnn')}")
        print(f"Side: {bf.get('side')}")
        
        rules = bf.get('rules', [])
        parking_regs = [r for r in rules if r.get('type') == 'parking-regulation']
        
        print(f"\nParking Regulations: {len(parking_regs)}")
        for i, rule in enumerate(parking_regs, 1):
            print(f"  Regulation #{i}:")
            for key, value in rule.items():
                if key != 'type':
                    if isinstance(value, str) and len(value) > 100:
                        print(f"    {key}: {value[:100]}...")
                    else:
                        print(f"    {key}: {value}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(show_details())