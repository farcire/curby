"""
Diagnose null fields in street_segments collection
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.curby

# Sample 100 documents to check for null fields
sample_size = 100
samples = list(db.street_segments.find().limit(sample_size))

print(f"Analyzing {len(samples)} street segments for null fields...\n")

# Count nulls for each field
null_counts = defaultdict(int)
total_docs = len(samples)

for doc in samples:
    for key, value in doc.items():
        if value is None or value == 'None' or (isinstance(value, str) and value.strip() == ''):
            null_counts[key] += 1

# Print results sorted by null count
print("Fields with null values:")
print("=" * 60)
for field, count in sorted(null_counts.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_docs) * 100
    print(f"{field:30s}: {count:3d}/{total_docs} ({percentage:5.1f}%)")

# Show a sample document with all fields
print("\n" + "=" * 60)
print("Sample document structure:")
print("=" * 60)
if samples:
    sample = samples[0]
    for key in sorted(sample.keys()):
        value = sample.get(key)
        if isinstance(value, (list, dict)):
            print(f"{key:30s}: {type(value).__name__} (length: {len(value)})")
        else:
            print(f"{key:30s}: {value}")

# Check streets collection for available fields
print("\n" + "=" * 60)
print("Checking streets collection for street name fields:")
print("=" * 60)
street_sample = db.streets.find_one()
if street_sample:
    print("Fields containing 'street' or 'name':")
    for key in sorted(street_sample.keys()):
        if 'street' in key.lower() or 'name' in key.lower():
            print(f"  {key}: {street_sample.get(key)}")
else:
    print("No streets found in collection")

client.close()