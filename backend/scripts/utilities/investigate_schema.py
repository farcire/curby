#!/usr/bin/env python3
"""Investigate current schema and No Parking handling"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json

async def main():
    load_dotenv()
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=10000)
    db = client.curby
    
    # 1. Check segment with rules
    print("=== SEGMENT WITH RULES (CNN 797000 L) ===")
    segment = await db.street_segments.find_one({'cnn': '797000', 'side': 'L'})
    
    if segment:
        print(f'Total rules: {len(segment.get("rules", []))}')
        print()
        
        if segment.get('rules'):
            print('First rule (full structure):')
            print(json.dumps(segment['rules'][0], indent=2))
            print()
            
            # Check for different rule types
            rule_types = {}
            for rule in segment['rules']:
                rtype = rule.get('type', 'unknown')
                rule_types[rtype] = rule_types.get(rtype, 0) + 1
            
            print('Rule types in this segment:')
            for rtype, count in rule_types.items():
                print(f'  {rtype}: {count}')
    
    # 2. Check raw parking regulation with NO PARKING
    print()
    print("=== RAW NO PARKING REGULATION ===")
    reg = await db.parking_regulations.find_one({
        'regulation': {'$regex': 'NO PARKING', '$options': 'i'}
    })
    if reg:
        print(json.dumps({
            'regulation': reg.get('regulation'),
            'days': reg.get('days'),
            'hours': reg.get('hours'),
            'from_time': reg.get('from_time'),
            'to_time': reg.get('to_time'),
            'hrlimit': reg.get('hrlimit'),
            'has_geometry': 'shape' in reg or 'geometry' in reg
        }, indent=2))
    
    # 3. Check what collections we have
    print()
    print("=== MONGODB COLLECTIONS ===")
    collections = await db.list_collection_names()
    for coll in sorted(collections):
        count = await db[coll].count_documents({})
        print(f'{coll}: {count:,} documents')
    
    # 4. Sample from blockfaces collection (if it exists)
    if 'blockfaces' in collections:
        print()
        print("=== BLOCKFACES COLLECTION SAMPLE ===")
        bf = await db.blockfaces.find_one({})
        if bf:
            print('Keys in blockfaces document:')
            print(list(bf.keys()))
            print()
            print('Sample blockface:')
            print(json.dumps({
                'cnn': bf.get('cnn'),
                'side': bf.get('side'),
                'has_rules': len(bf.get('rules', [])) > 0,
                'rule_count': len(bf.get('rules', []))
            }, indent=2))
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())