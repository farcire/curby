#!/usr/bin/env python3
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

total = db.street_segments.count_documents({})
with_rules = db.street_segments.count_documents({'rules': {'$exists': True, '$ne': []}})
with_from = db.street_segments.count_documents({'fromStreet': {'$exists': True, '$ne': None}})
with_to = db.street_segments.count_documents({'toStreet': {'$exists': True, '$ne': None}})
with_cardinal = db.street_segments.count_documents({'cardinalDirection': {'$exists': True, '$ne': None}})
with_cleaning = db.street_segments.count_documents({'streetCleaningAggregation': {'$exists': True}})
with_regs = db.street_segments.count_documents({'nonMeteredRegulationAggregation': {'$exists': True}})
with_schedules = db.street_segments.count_documents({'schedules': {'$exists': True, '$ne': []}})

print(f"\nTotal segments: {total}")
print(f"With rules: {with_rules} ({with_rules/total*100:.1f}%)")
print(f"With fromStreet: {with_from} ({with_from/total*100:.1f}%)")
print(f"With toStreet: {with_to} ({with_to/total*100:.1f}%)")
print(f"With cardinalDirection: {with_cardinal} ({with_cardinal/total*100:.1f}%)")
print(f"With streetCleaningAggregation: {with_cleaning} ({with_cleaning/total*100:.1f}%)")
print(f"With nonMeteredRegulationAggregation: {with_regs} ({with_regs/total*100:.1f}%)")
print(f"With schedules: {with_schedules} ({with_schedules/total*100:.1f}%)")

# Show a sample
sample = db.street_segments.find_one({'rules': {'$ne': []}})
if sample:
    print(f"\nSample segment (CNN {sample.get('cnn')}, side {sample.get('side')}):")
    print(f"  fromStreet: {sample.get('fromStreet')}")
    print(f"  toStreet: {sample.get('toStreet')}")
    print(f"  cardinalDirection: {sample.get('cardinalDirection')}")
    print(f"  rules count: {len(sample.get('rules', []))}")
    print(f"  has streetCleaningAggregation: {bool(sample.get('streetCleaningAggregation'))}")
    print(f"  has nonMeteredRegulationAggregation: {bool(sample.get('nonMeteredRegulationAggregation'))}")

client.close()