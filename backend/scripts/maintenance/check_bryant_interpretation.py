#!/usr/bin/env python3
from pymongo import MongoClient
import os, json
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

# Find Bryant St segment (2101-2199)
seg = db.street_segments.find_one({
    'streetName': 'BRYANT ST',
    'fromAddress': {'$lte': 2101},
    'toAddress': {'$gte': 2199}
})

if seg:
    print('Found segment:')
    print(f"CNN: {seg.get('cnn')}, Side: {seg.get('side')}")
    print(f"Address: {seg.get('fromAddress')}-{seg.get('toAddress')}")
    print(f"\nHas interpretation: {bool(seg.get('interpretation'))}")
    
    if seg.get('interpretation'):
        interp = seg['interpretation']
        rules_display = interp.get('rules_display', [])
        print(f"\nRules display count: {len(rules_display)}")
        print(f"Rules display content:")
        for i, rule in enumerate(rules_display[:10]):
            print(f"  {i+1}. {rule}")
    
    print(f"\nRaw rules count: {len(seg.get('rules', []))}")
    if seg.get('rules'):
        print("\nFirst 3 raw rules:")
        for i, rule in enumerate(seg['rules'][:3]):
            print(f"  {i+1}. Type: {rule.get('type')}, Description: {rule.get('description', 'N/A')}")
else:
    print('Segment not found')
    
client.close()