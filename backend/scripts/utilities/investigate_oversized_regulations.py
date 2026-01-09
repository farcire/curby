"""
Investigate all "No oversized vehicles" regulations to understand their variations
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

async def investigate_oversized_regulations():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.curby
    
    print("=" * 100)
    print("INVESTIGATING ALL 'NO OVERSIZED VEHICLES' REGULATIONS")
    print("=" * 100)
    print()
    
    # Find all segments with "No oversized vehicles" regulation
    print("Finding all segments with 'No oversized vehicles' regulation...")
    
    segments_with_oversized = []
    async for doc in db.street_segments.find({
        "rules.regulation": {"$regex": "oversized", "$options": "i"}
    }):
        segments_with_oversized.append(doc)
    
    print(f"Found {len(segments_with_oversized)} segments")
    print()
    
    # Collect unique variations of the regulation
    unique_regulations = {}
    
    for seg in segments_with_oversized:
        rules = seg.get('rules', [])
        
        for rule in rules:
            regulation_text = rule.get('regulation', '')
            
            if 'oversized' in regulation_text.lower():
                # Create a key based on all the relevant fields
                key_fields = {
                    'regulation': rule.get('regulation'),
                    'days': rule.get('days'),
                    'hours': rule.get('hours'),
                    'fromTime': rule.get('fromTime'),
                    'toTime': rule.get('toTime'),
                    'timeLimit': rule.get('timeLimit'),
                    'details': rule.get('details'),
                    'exceptions': rule.get('exceptions')
                }
                
                key = json.dumps(key_fields, sort_keys=True)
                
                if key not in unique_regulations:
                    unique_regulations[key] = {
                        'fields': key_fields,
                        'count': 0,
                        'examples': []
                    }
                
                unique_regulations[key]['count'] += 1
                
                if len(unique_regulations[key]['examples']) < 3:
                    unique_regulations[key]['examples'].append({
                        'cnn': seg.get('cnn'),
                        'side': seg.get('side'),
                        'street': seg.get('streetName'),
                        'display': seg.get('displayName')
                    })
    
    print(f"Found {len(unique_regulations)} unique variations of the regulation")
    print()
    print("=" * 100)
    
    # Display each unique variation
    for i, (key, data) in enumerate(sorted(unique_regulations.items(), key=lambda x: x[1]['count'], reverse=True), 1):
        print(f"\nVARIATION #{i} (appears {data['count']} times)")
        print("-" * 100)
        
        fields = data['fields']
        print(f"Regulation: {fields.get('regulation')}")
        print(f"Days: {fields.get('days')}")
        print(f"Hours: {fields.get('hours')}")
        print(f"From Time: {fields.get('fromTime')}")
        print(f"To Time: {fields.get('toTime')}")
        print(f"Time Limit: {fields.get('timeLimit')}")
        print(f"Details: {fields.get('details')}")
        print(f"Exceptions: {fields.get('exceptions')}")
        
        print(f"\nExample locations:")
        for ex in data['examples']:
            print(f"  - CNN {ex['cnn']}, Side {ex['side']}: {ex['display']}")
        
        print()
    
    print("=" * 100)
    print()
    
    # Save to file
    output = {
        'total_segments': len(segments_with_oversized),
        'unique_variations': len(unique_regulations),
        'variations': []
    }
    
    for key, data in sorted(unique_regulations.items(), key=lambda x: x[1]['count'], reverse=True):
        output['variations'].append({
            'count': data['count'],
            'fields': data['fields'],
            'examples': data['examples']
        })
    
    with open('backend/oversized_regulations_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Analysis saved to: backend/oversized_regulations_analysis.json")
    print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(investigate_oversized_regulations())