#!/usr/bin/env python3
"""
Investigate the regulations that were skipped during ingestion:
- 9 regulations without geometry
- 3 regulations with no segment match
"""
import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
import json

load_dotenv()
app_token = os.getenv('SFMTA_APP_TOKEN')
client = Socrata('data.sfgov.org', app_token)

print("="*70)
print("INVESTIGATING SKIPPED PARKING REGULATIONS")
print("="*70)

# Fetch all parking regulations
print("\nFetching parking regulations...")
regs = client.get('hi6h-neyh', limit=10000)
regs_df = pd.DataFrame.from_records(regs)
print(f"Total regulations: {len(regs_df)}")

# Find regulations without geometry
print("\n" + "="*70)
print("REGULATIONS WITHOUT GEOMETRY (9 expected)")
print("="*70)

no_geometry = []
for idx, row in regs_df.iterrows():
    geo = row.get("shape") or row.get("geometry")
    if not geo or not isinstance(geo, dict):
        no_geometry.append(row.to_dict())

print(f"\nFound {len(no_geometry)} regulations without geometry:\n")

for i, reg in enumerate(no_geometry, 1):
    print(f"{i}. Regulation: {reg.get('regulation', 'N/A')}")
    print(f"   Location: {reg.get('location', 'N/A')}")
    print(f"   Street: {reg.get('street', 'N/A')}")
    print(f"   Supervisor District: {reg.get('supervisor_district', 'N/A')}")
    print(f"   Days: {reg.get('days', 'N/A')}")
    print(f"   Hours: {reg.get('hours', 'N/A')}")
    print(f"   Time Limit: {reg.get('hrlimit', 'N/A')}")
    print(f"   Geometry field exists: {'shape' in reg or 'geometry' in reg}")
    print(f"   Geometry value: {reg.get('shape', reg.get('geometry', 'N/A'))}")
    print()

# Save to JSON for investigation
if no_geometry:
    with open('regulations_without_geometry.json', 'w') as f:
        json.dump(no_geometry, f, indent=2, default=str)
    print(f"✓ Saved to regulations_without_geometry.json\n")

# For the 3 with no segment match, we need to look at regulations that:
# 1. Have geometry
# 2. Might be far from any street segments
# 3. Or have unusual characteristics

print("="*70)
print("POTENTIAL NO-MATCH REGULATIONS (3 expected)")
print("="*70)
print("\nThese are regulations with geometry but might not match any segment:")
print("(Could be due to: distance from streets, unusual geometry, etc.)\n")

# Look for regulations with geometry but potentially problematic
with_geometry = regs_df[regs_df['shape'].notna() | regs_df['geometry'].notna()]
print(f"Total regulations with geometry: {len(with_geometry)}")

# Check for regulations without supervisor_district (might be harder to match)
no_district = with_geometry[with_geometry['supervisor_district'].isna()]
print(f"Regulations with geometry but NO supervisor_district: {len(no_district)}")

if len(no_district) > 0:
    print("\nRegulations without supervisor_district (potential no-match candidates):")
    for idx, row in no_district.head(10).iterrows():
        print(f"  - {row.get('regulation', 'N/A')}")
        print(f"    Location: {row.get('location', 'N/A')}")
        print(f"    Street: {row.get('street', 'N/A')}")
        print()

# Look for regulations with unusual characteristics
print("\nRegulations with unusual characteristics:")

# Check for regulations with very specific/unusual locations
unusual = with_geometry[
    (with_geometry['location'].notna()) & 
    (with_geometry['location'].str.contains('PRIVATE|ALLEY|PATH|PLAZA', case=False, na=False))
]
print(f"\nRegulations on private/alley/path/plaza: {len(unusual)}")
if len(unusual) > 0:
    for idx, row in unusual.head(5).iterrows():
        print(f"  - {row.get('regulation', 'N/A')} at {row.get('location', 'N/A')}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"\nTotal regulations: {len(regs_df)}")
print(f"Without geometry: {len(no_geometry)} (will be skipped)")
print(f"With geometry: {len(regs_df) - len(no_geometry)}")
print(f"Expected to match: {len(regs_df) - len(no_geometry) - 3} (based on ingestion log)")
print(f"Expected no-match: 3")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("1. The 9 regulations without geometry are documented above")
print("2. To find the 3 with no segment match, run the ingestion script")
print("3. The ingestion will create 'skipped_regulation_ids.txt' with all IDs")
print("="*70)