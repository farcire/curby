import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def validate_sides():
    """Validate that blockfaces have proper side assignments and rules."""
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Error: MONGODB_URI not found in .env")
        return
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]
    
    print("\n" + "="*60)
    print("BLOCKFACE SIDE ASSIGNMENT VALIDATION")
    print("="*60)
    
    # Count blockfaces by side
    total = await db.blockfaces.count_documents({})
    with_side_L = await db.blockfaces.count_documents({"side": "L"})
    with_side_R = await db.blockfaces.count_documents({"side": "R"})
    without_side = await db.blockfaces.count_documents({"side": None})
    
    print(f"\n📊 SIDE ASSIGNMENT STATISTICS:")
    print(f"   Total Blockfaces: {total}")
    print(f"   Left Side (L): {with_side_L} ({with_side_L/total*100:.1f}%)")
    print(f"   Right Side (R): {with_side_R} ({with_side_R/total*100:.1f}%)")
    print(f"   No Side (None): {without_side} ({without_side/total*100:.1f}%)")
    
    if without_side > 0:
        print(f"\n   ⚠️  WARNING: {without_side} blockfaces have no side assignment!")
        print(f"       This will prevent proper rule matching.")
    
    # Count rules by type
    print(f"\n📋 RULE DISTRIBUTION BY TYPE:")
    pipeline = [
        {"$unwind": "$rules"},
        {"$group": {
            "_id": "$rules.type",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    rule_counts = await db.blockfaces.aggregate(pipeline).to_list(None)
    
    if rule_counts:
        for item in rule_counts:
            print(f"   {item['_id']}: {item['count']} rules")
    else:
        print("   ⚠️  NO RULES FOUND in blockfaces collection!")
    
    # Check for parking-regulation type specifically
    has_parking_regs = any(item['_id'] == 'parking-regulation' for item in rule_counts)
    if not has_parking_regs:
        print(f"\n   ❌ CRITICAL: No 'parking-regulation' rules found!")
        print(f"      Parking regulations are NOT being joined to blockfaces.")
        
        # Check if they exist in separate collection
        reg_count = await db.parking_regulations.count_documents({})
        if reg_count > 0:
            print(f"      But found {reg_count} regulations in separate 'parking_regulations' collection.")
            print(f"      → These need to be joined to blockfaces during ingestion!")
    
    # Count blockfaces with no rules at all
    no_rules = await db.blockfaces.count_documents({"rules": []})
    print(f"\n📦 BLOCKFACES WITHOUT RULES:")
    print(f"   Blockfaces with 0 rules: {no_rules} ({no_rules/total*100:.1f}%)")
    
    # Sample blockfaces without sides but with rules (problematic)
    print(f"\n🔍 CHECKING FOR PROBLEMATIC BLOCKFACES:")
    problematic = await db.blockfaces.find(
        {
            "side": None,
            "rules": {"$ne": []}
        },
        {"id": 1, "streetName": 1, "cnn": 1, "rules": 1}
    ).limit(3).to_list(None)
    
    if problematic:
        print(f"   ⚠️  Found {len(problematic)} blockfaces without side but with rules:")
        for bf in problematic:
            rule_types = [r.get('type') for r in bf.get('rules', [])]
            print(f"      - {bf.get('id')} on {bf.get('streetName')} (CNN: {bf.get('cnn')})")
            print(f"        Rules: {rule_types}")
    else:
        print(f"   ✓ No blockfaces found with rules but missing side assignment")
    
    # Sample blockfaces WITH sides and rules (expected state)
    print(f"\n✅ SAMPLE PROPERLY-CONFIGURED BLOCKFACES:")
    good_examples = await db.blockfaces.find(
        {
            "side": {"$ne": None},
            "rules": {"$ne": []}
        },
        {"id": 1, "streetName": 1, "side": 1, "rules": 1}
    ).limit(2).to_list(None)
    
    if good_examples:
        for bf in good_examples:
            rule_types = [r.get('type') for r in bf.get('rules', [])]
            print(f"   {bf.get('streetName')} - Side {bf.get('side')}")
            print(f"   Rules: {rule_types}")
    else:
        print(f"   ⚠️  No blockfaces found with both side AND rules!")
    
    # Check CNNs with only one blockface (should usually have two - one per side)
    print(f"\n🔢 CNN BLOCKFACE COVERAGE:")
    pipeline = [
        {"$group": {
            "_id": "$cnn",
            "count": {"$sum": 1},
            "sides": {"$addToSet": "$side"}
        }},
        {"$group": {
            "_id": "$count",
            "cnn_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    cnn_stats = await db.blockfaces.aggregate(pipeline).to_list(None)
    
    for stat in cnn_stats:
        count = stat['_id']
        cnn_count = stat['cnn_count']
        print(f"   {cnn_count} CNNs have {count} blockface(s)")
    
    # Find CNNs with only one blockface
    single_bf_cnns = await db.blockfaces.aggregate([
        {"$group": {
            "_id": "$cnn",
            "count": {"$sum": 1}
        }},
        {"$match": {"count": 1}},
        {"$limit": 5}
    ]).to_list(None)
    
    if single_bf_cnns:
        print(f"\n   ℹ️  Sample CNNs with only 1 blockface:")
        for item in single_bf_cnns[:3]:
            sample_bf = await db.blockfaces.find_one({"cnn": item['_id']}, {"streetName": 1, "side": 1})
            side = sample_bf.get('side', 'None')
            print(f"      CNN {item['_id']}: {sample_bf.get('streetName')} (Side: {side})")
    
    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60 + "\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(validate_sides())