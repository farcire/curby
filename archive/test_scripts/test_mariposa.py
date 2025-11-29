import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

async def test_mariposa():
    """Test Mariposa Street between Florida and Potrero for side assignment and rules."""
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
    
    print("\n" + "="*70)
    print("TESTING: MARIPOSA STREET (between Florida and Potrero)")
    print("="*70)
    
    # Search for Mariposa Street blockfaces
    query = {
        "$or": [
            {"streetName": {"$regex": "MARIPOSA", "$options": "i"}},
            {"streetName": {"$regex": "MARIPOSA ST", "$options": "i"}}
        ]
    }
    
    blockfaces = await db.blockfaces.find(query).to_list(None)
    
    if not blockfaces:
        print("\n❌ NO BLOCKFACES FOUND for Mariposa Street")
        print("   The street may not be in the ingested area (Mission/SOMA)")
        client.close()
        return
    
    print(f"\n✅ Found {len(blockfaces)} blockface(s) for Mariposa Street\n")
    
    # Filter for the segment between Florida and Potrero
    target_blockfaces = []
    for bf in blockfaces:
        from_street = (bf.get("fromStreet") or "").upper()
        to_street = (bf.get("toStreet") or "").upper()
        
        # Check if this segment is between Florida and Potrero
        is_target = (
            ("FLORIDA" in from_street and "POTRERO" in to_street) or
            ("POTRERO" in from_street and "FLORIDA" in to_street) or
            ("FLORIDA" in to_street and "POTRERO" in from_street) or
            ("POTRERO" in to_street and "FLORIDA" in from_street)
        )
        
        if is_target:
            target_blockfaces.append(bf)
    
    if not target_blockfaces:
        print("⚠️  Could not identify segment between Florida and Potrero")
        print("   Showing ALL Mariposa Street blockfaces:\n")
        target_blockfaces = blockfaces
    else:
        print(f"🎯 Found {len(target_blockfaces)} blockface(s) between Florida and Potrero:\n")
    
    # Analyze each blockface
    for i, bf in enumerate(target_blockfaces, 1):
        print(f"--- Blockface {i} ---")
        print(f"ID: {bf.get('id')}")
        print(f"Street: {bf.get('streetName')}")
        print(f"From: {bf.get('fromStreet', 'N/A')}")
        print(f"To: {bf.get('toStreet', 'N/A')}")
        print(f"CNN: {bf.get('cnn')}")
        print(f"Side: {bf.get('side', 'N/A')} {'⚠️ MISSING SIDE' if not bf.get('side') else ''}")
        
        rules = bf.get('rules', [])
        print(f"Rules: {len(rules)} total")
        
        if rules:
            # Group rules by type
            rule_types = {}
            for rule in rules:
                rule_type = rule.get('type', 'unknown')
                if rule_type not in rule_types:
                    rule_types[rule_type] = []
                rule_types[rule_type].append(rule)
            
            for rule_type, type_rules in rule_types.items():
                print(f"\n  📋 {rule_type}: {len(type_rules)} rule(s)")
                
                for rule in type_rules:
                    if rule_type == "street-sweeping":
                        print(f"     • {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')} (Side: {rule.get('side', 'N/A')})")
                    
                    elif rule_type == "parking-regulation":
                        time_limit = rule.get('timeLimit', 'N/A')
                        permit = rule.get('permitArea', 'N/A')
                        desc = rule.get('description', 'N/A')
                        print(f"     • Time Limit: {time_limit}, Permit: {permit}")
                        print(f"       {desc}")
                    
                    elif rule_type == "meter":
                        post_id = rule.get('postId', 'N/A')
                        active = rule.get('active', 'N/A')
                        schedules = rule.get('schedules', [])
                        print(f"     • Post: {post_id}, Active: {active}, {len(schedules)} schedule(s)")
        else:
            print("  ⚠️  NO RULES ATTACHED TO THIS BLOCKFACE")
        
        # Check if has geometry
        geometry = bf.get('geometry')
        if geometry:
            coords = geometry.get('coordinates', [])
            print(f"\nGeometry: {geometry.get('type')} with {len(coords)} points")
        else:
            print("\n⚠️  NO GEOMETRY")
        
        print()
    
    # Summary statistics
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    with_side = sum(1 for bf in target_blockfaces if bf.get('side'))
    with_rules = sum(1 for bf in target_blockfaces if bf.get('rules'))
    with_parking_regs = sum(
        1 for bf in target_blockfaces 
        if any(r.get('type') == 'parking-regulation' for r in bf.get('rules', []))
    )
    
    print(f"Blockfaces analyzed: {len(target_blockfaces)}")
    print(f"With side assignment: {with_side}/{len(target_blockfaces)} ({with_side/len(target_blockfaces)*100:.0f}%)")
    print(f"With any rules: {with_rules}/{len(target_blockfaces)} ({with_rules/len(target_blockfaces)*100:.0f}%)")
    print(f"With parking regulations: {with_parking_regs}/{len(target_blockfaces)} ({with_parking_regs/len(target_blockfaces)*100:.0f}%)")
    
    # Check what we expect to see
    print("\n✓ EXPECTED RESULTS:")
    print("  • 2 blockfaces (one for each side of Mariposa)")
    print("  • Each should have side='L' or side='R'")
    print("  • Each should have parking-regulation rules")
    print("  • May have street-sweeping rules")
    print("  • May have meter rules if metered")
    
    if len(target_blockfaces) < 2:
        print("\n⚠️  WARNING: Expected 2 blockfaces (both sides), found", len(target_blockfaces))
    
    if with_side < len(target_blockfaces):
        print(f"\n❌ ISSUE: {len(target_blockfaces) - with_side} blockface(s) missing side assignment")
    
    if with_parking_regs == 0:
        print("\n❌ CRITICAL ISSUE: NO parking regulations found!")
        print("   This means regulations are NOT being joined to blockfaces")
        
        # Check if regulations exist in separate collection
        reg_count = await db.parking_regulations.count_documents({
            "$or": [
                {"street_name": {"$regex": "MARIPOSA", "$options": "i"}},
                {"fullname": {"$regex": "MARIPOSA", "$options": "i"}}
            ]
        })
        
        if reg_count > 0:
            print(f"   But found {reg_count} regulation(s) in separate collection")
            print("   → FIX NEEDED: Implement parking regulation join in ingest_data.py")
    elif with_parking_regs == len(target_blockfaces):
        print("\n✅ SUCCESS: All blockfaces have parking regulations!")
    
    print("\n" + "="*70 + "\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_mariposa())