#!/usr/bin/env python3
"""
Investigate fromStreet field accuracy in street_segments
"""
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

# Sample segments to check fromStreet values
print("=" * 80)
print("INVESTIGATING fromStreet FIELD ACCURACY")
print("=" * 80)

# Get sample segments with fromStreet
samples = list(db.street_segments.find({'fromStreet': {'$exists': True, '$ne': None}}).limit(20))

print(f"\nFound {len(samples)} segments with fromStreet populated")
print("\nSample Analysis:")
print("-" * 80)

for seg in samples[:10]:
    cnn = seg.get('cnn')
    side = seg.get('side')
    from_street = seg.get('fromStreet')
    to_street = seg.get('toStreet')
    street_name = seg.get('street')
    
    # Check what's in the streets collection for this CNN
    street_doc = db.streets.find_one({'cnn': cnn})
    
    # Check what's in intersections collection
    intersection_doc = db.intersections.find_one({'cnn': cnn})
    
    print(f"\nCNN {cnn} (side {side}):")
    print(f"  Current fromStreet: {from_street}")
    print(f"  Current toStreet: {to_street}")
    print(f"  Street name: {street_name}")
    
    if street_doc:
        print(f"  Streets collection:")
        print(f"    f_st: {street_doc.get('f_st')}")
        print(f"    t_st: {street_doc.get('t_st')}")
        print(f"    street: {street_doc.get('street')}")
    
    if intersection_doc:
        print(f"  Intersections collection:")
        print(f"    from_st: {intersection_doc.get('from_st')}")
        print(f"    limits: {intersection_doc.get('limits')}")

# Check for segments where fromStreet doesn't match expected sources
print("\n" + "=" * 80)
print("CHECKING DATA SOURCE CONSISTENCY")
print("=" * 80)

# Compare with streets collection
mismatches = []
for seg in samples:
    cnn = seg.get('cnn')
    from_street = seg.get('fromStreet')
    
    street_doc = db.streets.find_one({'cnn': cnn})
    if street_doc:
        f_st = street_doc.get('f_st')
        if f_st and from_street != f_st:
            mismatches.append({
                'cnn': cnn,
                'segment_fromStreet': from_street,
                'streets_f_st': f_st
            })

if mismatches:
    print(f"\nFound {len(mismatches)} mismatches between segment.fromStreet and streets.f_st:")
    for m in mismatches[:5]:
        print(f"  CNN {m['cnn']}: '{m['segment_fromStreet']}' vs '{m['streets_f_st']}'")
else:
    print("\n✓ All sampled segments match streets.f_st")

# Save detailed report
report = {
    'total_with_fromStreet': db.street_segments.count_documents({'fromStreet': {'$exists': True, '$ne': None}}),
    'total_segments': db.street_segments.count_documents({}),
    'sample_analysis': []
}

for seg in samples[:10]:
    cnn = seg.get('cnn')
    street_doc = db.streets.find_one({'cnn': cnn})
    intersection_doc = db.intersections.find_one({'cnn': cnn})
    
    report['sample_analysis'].append({
        'cnn': cnn,
        'side': seg.get('side'),
        'segment': {
            'fromStreet': seg.get('fromStreet'),
            'toStreet': seg.get('toStreet'),
            'street': seg.get('street')
        },
        'streets_collection': {
            'f_st': street_doc.get('f_st') if street_doc else None,
            't_st': street_doc.get('t_st') if street_doc else None,
            'street': street_doc.get('street') if street_doc else None
        } if street_doc else None,
        'intersections_collection': {
            'from_st': intersection_doc.get('from_st') if intersection_doc else None,
            'limits': intersection_doc.get('limits') if intersection_doc else None
        } if intersection_doc else None
    })

with open('fromstreet_investigation.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n✓ Detailed report saved to fromstreet_investigation.json")
client.close()