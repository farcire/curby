"""
Analyze CNNs with missing street cleaning on one side.
Check if the opposite side has blockface geometry but no parking rules.
This could indicate a systematic data gap pattern.
"""
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from collections import defaultdict

async def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    mongodb_uri = os.getenv("MONGODB_URI")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client["curby"]
    
    print("=== Analyzing Missing Side Pattern ===\n")
    
    # Get all street cleaning schedules
    all_schedules = await db.street_cleaning_schedules.find({}).to_list(None)
    
    # Group by CNN to find which sides have cleaning data
    cnn_cleaning_sides = defaultdict(set)
    for sched in all_schedules:
        cnn = sched.get('cnn')
        side = sched.get('cnnrightleft')
        if cnn and side:
            cnn_cleaning_sides[cnn].add(side)
    
    # Find CNNs with only one side having cleaning data
    cnns_missing_side = []
    for cnn, sides in cnn_cleaning_sides.items():
        if len(sides) == 1:
            has_side = list(sides)[0]
            missing_side = 'R' if has_side == 'L' else 'L'
            cnns_missing_side.append({
                'cnn': cnn,
                'has_cleaning': has_side,
                'missing_cleaning': missing_side
            })
    
    print(f"Found {len(cnns_missing_side)} CNNs with street cleaning on only one side\n")
    
    # Now check segments for these CNNs
    print("Analyzing segments for CNNs with missing cleaning data...\n")
    
    pattern_found = 0
    examples = []
    
    for item in cnns_missing_side[:100]:  # Check first 100
        cnn = item['cnn']
        missing_side = item['missing_cleaning']
        
        # Get both segments for this CNN
        segments = await db.street_segments.find({'cnn': cnn}).to_list(None)
        
        if len(segments) != 2:
            continue
        
        # Find the segment with missing cleaning
        missing_segment = None
        has_segment = None
        
        for seg in segments:
            if seg.get('side') == missing_side:
                missing_segment = seg
            else:
                has_segment = seg
        
        if not missing_segment or not has_segment:
            continue
        
        # Check if missing side has blockface but no rules
        has_blockface = missing_segment.get('blockfaceGeometry') is not None
        has_rules = len(missing_segment.get('rules', [])) > 0
        
        if has_blockface and not has_rules:
            pattern_found += 1
            
            if len(examples) < 20:
                examples.append({
                    'cnn': cnn,
                    'street': missing_segment.get('streetName'),
                    'missing_side': missing_side,
                    'from_addr': missing_segment.get('fromAddress'),
                    'to_addr': missing_segment.get('toAddress'),
                    'has_blockface': has_blockface,
                    'has_rules': has_rules,
                    'cardinal': missing_segment.get('cardinalDirection'),
                    'other_side_rules': len(has_segment.get('rules', []))
                })
    
    print(f"Pattern Analysis Results:")
    print(f"  CNNs with missing cleaning on one side: {len(cnns_missing_side)}")
    print(f"  Of those, segments with blockface but NO rules: {pattern_found}")
    print(f"  Percentage: {(pattern_found/len(cnns_missing_side)*100):.1f}%\n")
    
    if examples:
        print(f"First {len(examples)} examples of missing side with blockface but no rules:\n")
        for ex in examples:
            print(f"CNN {ex['cnn']}: {ex['street']} {ex['missing_side']} ({ex['from_addr']}-{ex['to_addr']})")
            print(f"  Cardinal: {ex['cardinal']}")
            print(f"  Has blockface: {ex['has_blockface']}")
            print(f"  Has rules: {ex['has_rules']}")
            print(f"  Other side has {ex['other_side_rules']} rules")
            print()
    
    # Special check for 19th Street
    print("\n=== Special Check: 19th Street ===\n")
    segments_19th = await db.street_segments.find({
        'streetName': {'$regex': '19TH', '$options': 'i'},
        'fromAddress': {'$regex': '^27'}
    }).to_list(None)
    
    for seg in segments_19th:
        print(f"CNN {seg.get('cnn')}: {seg.get('streetName')} {seg.get('side')} ({seg.get('fromAddress')}-{seg.get('toAddress')})")
        print(f"  Cardinal: {seg.get('cardinalDirection')}")
        print(f"  Has blockface: {seg.get('blockfaceGeometry') is not None}")
        print(f"  Rules: {len(seg.get('rules', []))}")
        for rule in seg.get('rules', []):
            print(f"    - {rule.get('type')}: {rule.get('blockside')} {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())