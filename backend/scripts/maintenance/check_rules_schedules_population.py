#!/usr/bin/env python3
"""
Check rules and schedules array population in street_segments
"""
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

print("=" * 80)
print("RULES AND SCHEDULES ARRAY POPULATION CHECK")
print("=" * 80)

# Get counts
total = db.street_segments.count_documents({})
with_rules = db.street_segments.count_documents({'rules': {'$exists': True, '$ne': []}})
with_schedules = db.street_segments.count_documents({'schedules': {'$exists': True, '$ne': []}})
empty_rules = db.street_segments.count_documents({'rules': []})
empty_schedules = db.street_segments.count_documents({'schedules': []})

print(f"\nTotal segments: {total:,}")
print(f"\nRules Array:")
print(f"  With rules (non-empty): {with_rules:,} ({with_rules/total*100:.1f}%)")
print(f"  Empty rules array: {empty_rules:,} ({empty_rules/total*100:.1f}%)")

print(f"\nSchedules Array:")
print(f"  With schedules (non-empty): {with_schedules:,} ({with_schedules/total*100:.1f}%)")
print(f"  Empty schedules array: {empty_schedules:,} ({empty_schedules/total*100:.1f}%)")

# Check raw data collections
print(f"\n" + "=" * 80)
print("RAW DATA COLLECTIONS")
print("=" * 80)

parking_regs = db.parking_regulations.count_documents({})
street_cleaning = db.street_cleaning_schedules.count_documents({})
meters = db.meters.count_documents({})

print(f"\nParking regulations: {parking_regs:,}")
print(f"Street cleaning schedules: {street_cleaning:,}")
print(f"Meters: {meters:,}")

# Sample segments with rules
print(f"\n" + "=" * 80)
print("SAMPLE SEGMENTS WITH RULES")
print("=" * 80)

with_rules_sample = list(db.street_segments.find({'rules': {'$ne': []}}).limit(3))
for seg in with_rules_sample:
    print(f"\nCNN {seg.get('cnn')} (side {seg.get('side')}):")
    print(f"  Street: {seg.get('street')}")
    print(f"  Rules count: {len(seg.get('rules', []))}")
    for rule in seg.get('rules', [])[:2]:
        print(f"    - Type: {rule.get('type')}, Description: {rule.get('description', 'N/A')[:60]}")

# Sample segments with schedules
print(f"\n" + "=" * 80)
print("SAMPLE SEGMENTS WITH SCHEDULES")
print("=" * 80)

with_schedules_sample = list(db.street_segments.find({'schedules': {'$ne': []}}).limit(3))
if with_schedules_sample:
    for seg in with_schedules_sample:
        print(f"\nCNN {seg.get('cnn')} (side {seg.get('side')}):")
        print(f"  Street: {seg.get('street')}")
        print(f"  Schedules count: {len(seg.get('schedules', []))}")
        for sched in seg.get('schedules', [])[:2]:
            print(f"    - Rate: ${sched.get('rate_per_hour', 'N/A')}, Days: {sched.get('days', 'N/A')}")
else:
    print("\nNo segments found with schedules")

# Check if rebuild preserved rules
print(f"\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if with_rules == 0:
    print("\n⚠️  WARNING: No segments have rules!")
    print("   The rebuild script may have cleared the rules arrays.")
    print("   You need to re-run the join scripts to populate rules.")
elif with_rules < total * 0.5:
    print(f"\n⚠️  WARNING: Only {with_rules/total*100:.1f}% of segments have rules")
    print("   This seems low. You may need to re-run join scripts.")
else:
    print(f"\n✓ Rules population looks good: {with_rules/total*100:.1f}% of segments have rules")

if with_schedules == 0 and meters > 0:
    print("\n⚠️  WARNING: No segments have schedules, but meters exist in database")
    print("   The schedules array population may have failed.")
elif with_schedules > 0:
    print(f"\n✓ Schedules populated: {with_schedules:,} segments have meter schedules")

# Save report
report = {
    'total_segments': total,
    'with_rules': with_rules,
    'with_schedules': with_schedules,
    'empty_rules': empty_rules,
    'empty_schedules': empty_schedules,
    'parking_regulations_count': parking_regs,
    'street_cleaning_count': street_cleaning,
    'meters_count': meters,
    'rules_percentage': round(with_rules/total*100, 2) if total > 0 else 0,
    'schedules_percentage': round(with_schedules/total*100, 2) if total > 0 else 0
}

with open('rules_schedules_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n✓ Report saved to rules_schedules_report.json")
client.close()