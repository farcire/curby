from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

async def check_18th_street():
    # Use the MongoDB URI directly
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    # Find 18th Street L segment between York and Bryant
    query = {
        "streetName": {"$regex": "18TH", "$options": "i"},
        "side": "L",
        "fromStreet": {"$regex": "YORK", "$options": "i"},
        "toStreet": {"$regex": "BRYANT", "$options": "i"}
    }
    
    segment = await db.street_segments.find_one(query)
    
    if segment:
        print("=" * 80)
        print(f"18TH ST - L Side (York St → Bryant St)")
        print("=" * 80)
        print(f"\nCNN: {segment.get('cnn')}")
        print(f"Side: {segment.get('side')}")
        print(f"\n📍 ADDRESS RANGE:")
        print(f"  From Address: {segment.get('fromAddress')}")
        print(f"  To Address: {segment.get('toAddress')}")
        
        from_addr = segment.get('fromAddress', '')
        if from_addr:
            is_odd = int(from_addr) % 2 == 1
            print(f"  → {'ODD numbers' if is_odd else 'EVEN numbers'}")
        
        # Check street cleaning for cardinal direction
        rules = segment.get('rules', [])
        cleaning_rules = [r for r in rules if r.get('type') == 'street-sweeping']
        
        if cleaning_rules:
            print(f"\n🧹 STREET CLEANING (with cardinal direction):")
            for rule in cleaning_rules:
                cardinal = rule.get('cardinalDirection', 'N/A')
                print(f"  Day: {rule.get('day')}")
                print(f"  Time: {rule.get('startTime')} - {rule.get('endTime')}")
                print(f"  Cardinal Direction: {cardinal}")
                print(f"  → This indicates the {cardinal} side of the street")
        
        # Check all rules
        print(f"\n📋 ALL RULES ({len(rules)} total):")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}:")
            print(f"    Type: {rule.get('type')}")
            if rule.get('description'):
                print(f"    Description: {rule.get('description')}")
            if rule.get('cardinalDirection'):
                print(f"    Cardinal Direction: {rule.get('cardinalDirection')}")
        
        print("\n" + "=" * 80)
        print("CONCLUSION:")
        print("=" * 80)
        from_addr = segment.get('fromAddress', '')
        if from_addr:
            is_odd = int(from_addr) % 2 == 1
            print(f"✅ L (Left) side = {'ODD' if is_odd else 'EVEN'} addresses ({from_addr}-{segment.get('toAddress')})")
        
        if cleaning_rules and cleaning_rules[0].get('cardinalDirection'):
            cardinal = cleaning_rules[0].get('cardinalDirection')
            print(f"✅ Cardinal Direction: {cardinal} side (from street cleaning data)")
            print(f"\n💡 RECOMMENDATION: Display as '18TH ST ({cardinal} side)' or '18TH ST (L/{cardinal})'")
    else:
        print("18th St L segment not found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_18th_street())