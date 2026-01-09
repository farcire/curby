#!/usr/bin/env python3
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

# Get counts
results = {
    "total_segments": db.street_segments.count_documents({}),
    "with_rules": db.street_segments.count_documents({'rules': {'$exists': True, '$ne': []}}),
    "with_fromStreet": db.street_segments.count_documents({'fromStreet': {'$exists': True, '$ne': None}}),
    "with_toStreet": db.street_segments.count_documents({'toStreet': {'$exists': True, '$ne': None}}),
    "with_cardinalDirection": db.street_segments.count_documents({'cardinalDirection': {'$exists': True, '$ne': None}}),
    "with_streetCleaningAggregation": db.street_segments.count_documents({'streetCleaningAggregation': {'$exists': True}}),
    "with_nonMeteredRegulationAggregation": db.street_segments.count_documents({'nonMeteredRegulationAggregation': {'$exists': True}}),
    "with_schedules": db.street_segments.count_documents({'schedules': {'$exists': True, '$ne': []}}),
}

# Get a sample document
sample = db.street_segments.find_one({'rules': {'$ne': []}})
if sample:
    results["sample_segment"] = {
        "cnn": sample.get('cnn'),
        "side": sample.get('side'),
        "fromStreet": sample.get('fromStreet'),
        "toStreet": sample.get('toStreet'),
        "cardinalDirection": sample.get('cardinalDirection'),
        "rules_count": len(sample.get('rules', [])),
        "has_streetCleaningAggregation": bool(sample.get('streetCleaningAggregation')),
        "has_nonMeteredRegulationAggregation": bool(sample.get('nonMeteredRegulationAggregation')),
        "has_schedules": bool(sample.get('schedules'))
    }

# Write to file
with open('population_status.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Results written to population_status.json")
client.close()