#!/usr/bin/env python3
"""
Analyze what % of segments have meters, street cleaning, and non-meter regulations
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

print("=" * 80)
print("SEGMENT COVERAGE ANALYSIS")
print("=" * 80)

# Total segments
total = db.street_segments.count_documents({})
print(f"\nTotal segments: {total:,}")

# Segments with meters
with_meters = db.street_segments.count_documents({'meters': {'$exists': True, '$ne': []}})
meters_pct = (with_meters / total * 100) if total > 0 else 0

# Segments with street cleaning rules
with_cleaning = db.street_segments.count_documents({'rules.type': 'street-sweeping'})
cleaning_pct = (with_cleaning / total * 100) if total > 0 else 0

# Segments with non-meter regulations (parking-regulation, time-limit, no-parking, rpp-zone)
non_meter_types = ['parking-regulation', 'time-limit', 'no-parking', 'rpp-zone']
with_regulations = db.street_segments.count_documents({
    'rules.type': {'$in': non_meter_types}
})
regulations_pct = (with_regulations / total * 100) if total > 0 else 0

# Segments with any rules
with_any_rules = db.street_segments.count_documents({'rules': {'$ne': []}})
any_rules_pct = (with_any_rules / total * 100) if total > 0 else 0

print("\n" + "=" * 80)
print("COVERAGE BREAKDOWN")
print("=" * 80)

print(f"\n📍 Segments with METERS:")
print(f"   {with_meters:,} segments ({meters_pct:.1f}%)")

print(f"\n🧹 Segments with STREET CLEANING:")
print(f"   {with_cleaning:,} segments ({cleaning_pct:.1f}%)")

print(f"\n🚫 Segments with NON-METER REGULATIONS:")
print(f"   {with_regulations:,} segments ({regulations_pct:.1f}%)")

print(f"\n📋 Segments with ANY RULES:")
print(f"   {with_any_rules:,} segments ({any_rules_pct:.1f}%)")

# Breakdown by rule type
print("\n" + "=" * 80)
print("DETAILED RULE TYPE BREAKDOWN")
print("=" * 80)

rule_types = [
    'street-sweeping',
    'parking-regulation',
    'time-limit',
    'no-parking',
    'rpp-zone',
    'metered'
]

for rule_type in rule_types:
    count = db.street_segments.count_documents({'rules.type': rule_type})
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {rule_type:25s}: {count:6,} segments ({pct:5.1f}%)")

# Overlaps
print("\n" + "=" * 80)
print("OVERLAPS")
print("=" * 80)

meters_and_cleaning = db.street_segments.count_documents({
    'meters': {'$ne': []},
    'rules.type': 'street-sweeping'
})

meters_and_regs = db.street_segments.count_documents({
    'meters': {'$ne': []},
    'rules.type': {'$in': non_meter_types}
})

cleaning_and_regs = db.street_segments.count_documents({
    'rules.type': {'$all': ['street-sweeping', {'$in': non_meter_types}]}
})

print(f"\nSegments with BOTH meters AND street cleaning: {meters_and_cleaning:,}")
print(f"Segments with BOTH meters AND non-meter regulations: {meters_and_regs:,}")
print(f"Segments with BOTH street cleaning AND non-meter regulations: {cleaning_and_regs:,}")

# Segments with nothing
with_nothing = db.street_segments.count_documents({
    'meters': [],
    'rules': []
})
nothing_pct = (with_nothing / total * 100) if total > 0 else 0

print(f"\n⚠️  Segments with NO meters, NO rules: {with_nothing:,} ({nothing_pct:.1f}%)")

print("\n" + "=" * 80)
client.close()