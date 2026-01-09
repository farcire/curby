#!/usr/bin/env python3
"""
Analyze supervisor_district field to determine if it can be used as a pre-filter
for parking regulation matching optimization.

Hypothesis: Pre-filter segments by supervisor_district before spatial matching
to reduce comparisons from 7,783 × 34,324 = 267M to much less.

Strategy:
1. Group segments by supervisor_district
2. For each regulation, only check segments in matching district(s)
3. For regulations with NULL district, check all segments (fallback)
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()
app_token = os.getenv('SFMTA_APP_TOKEN')
client = Socrata('data.sfgov.org', app_token)

print("="*70)
print("SUPERVISOR DISTRICT OPTIMIZATION FEASIBILITY ANALYSIS")
print("="*70)

# Fetch parking regulations
print("\n📥 Fetching parking regulations dataset...")
regs = client.get('hi6h-neyh', limit=10000)
regs_df = pd.DataFrame.from_records(regs)
print(f"   Fetched {len(regs_df)} parking regulations")

# Fetch active streets
print("\n📥 Fetching active streets dataset...")
streets = client.get('3psu-pn9h', limit=20000)
streets_df = pd.DataFrame.from_records(streets)
print(f"   Fetched {len(streets_df)} streets")

print("\n" + "="*70)
print("1. FIELD AVAILABILITY CHECK")
print("="*70)

reg_has_field = 'supervisor_district' in regs_df.columns
street_has_field = 'supervisor_district' in streets_df.columns

print(f"\n✓ Parking Regulations has 'supervisor_district': {reg_has_field}")
print(f"✓ Active Streets has 'supervisor_district': {street_has_field}")

if not reg_has_field or not street_has_field:
    print("\n❌ OPTIMIZATION NOT POSSIBLE - Missing required field")
    exit(1)

print("\n" + "="*70)
print("2. DATA COMPLETENESS ANALYSIS")
print("="*70)

# Analyze parking regulations
reg_total = len(regs_df)
reg_with_district = regs_df['supervisor_district'].notna().sum()
reg_null_district = reg_total - reg_with_district
reg_coverage = (reg_with_district / reg_total) * 100

print(f"\n📊 Parking Regulations:")
print(f"   Total: {reg_total:,}")
print(f"   With supervisor_district: {reg_with_district:,} ({reg_coverage:.1f}%)")
print(f"   NULL supervisor_district: {reg_null_district:,} ({100-reg_coverage:.1f}%)")

# Analyze streets
street_total = len(streets_df)
street_with_district = streets_df['supervisor_district'].notna().sum()
street_null_district = street_total - street_with_district
street_coverage = (street_with_district / street_total) * 100

print(f"\n📊 Active Streets:")
print(f"   Total: {street_total:,}")
print(f"   With supervisor_district: {street_with_district:,} ({street_coverage:.1f}%)")
print(f"   NULL supervisor_district: {street_null_district:,} ({100-street_coverage:.1f}%)")

print("\n" + "="*70)
print("3. MULTI-DISTRICT REGULATION ANALYSIS")
print("="*70)

# Check if regulations can span multiple districts
multi_district_count = 0
multi_district_examples = []

for idx, row in regs_df[regs_df['supervisor_district'].notna()].iterrows():
    district_val = str(row['supervisor_district']).strip()
    # Check for delimiters that might indicate multiple districts
    if any(delim in district_val for delim in [',', ';', '/', '&', ' and ', '-']):
        multi_district_count += 1
        if len(multi_district_examples) < 5:
            multi_district_examples.append(district_val)

print(f"\n📊 Multi-district regulations:")
print(f"   Found: {multi_district_count} ({multi_district_count/reg_with_district*100:.1f}% of non-NULL)")

if multi_district_examples:
    print(f"\n   Examples:")
    for ex in multi_district_examples:
        print(f"     • '{ex}'")

print("\n" + "="*70)
print("4. DISTRICT VALUE DISTRIBUTION")
print("="*70)

print("\n📊 Top supervisor_district values in Parking Regulations:")
reg_districts = regs_df['supervisor_district'].value_counts().head(12)
for district, count in reg_districts.items():
    print(f"   District {district}: {count:,} regulations")

print("\n📊 Top supervisor_district values in Active Streets:")
street_districts = streets_df['supervisor_district'].value_counts().head(12)
for district, count in street_districts.items():
    print(f"   District {district}: {count:,} streets")

# Check for district overlap
reg_district_set = set(regs_df['supervisor_district'].dropna().unique())
street_district_set = set(streets_df['supervisor_district'].dropna().unique())
common_districts = reg_district_set & street_district_set

print(f"\n📊 District overlap:")
print(f"   Unique districts in regulations: {len(reg_district_set)}")
print(f"   Unique districts in streets: {len(street_district_set)}")
print(f"   Common districts: {len(common_districts)}")
print(f"   Common: {sorted(common_districts)}")

print("\n" + "="*70)
print("5. PERFORMANCE OPTIMIZATION CALCULATION")
print("="*70)

segments_per_street = 2  # L and R sides
total_segments = street_total * segments_per_street
current_comparisons = reg_total * total_segments

print(f"\n📊 Current approach (no optimization):")
print(f"   Regulations: {reg_total:,}")
print(f"   Segments: {total_segments:,} ({street_total:,} streets × 2 sides)")
print(f"   Total comparisons: {current_comparisons:,}")

# Calculate optimized comparisons
# Group streets by district
streets_by_district = streets_df[streets_df['supervisor_district'].notna()].groupby('supervisor_district').size()
segments_by_district = streets_by_district * 2  # L and R sides

# Calculate comparisons with optimization
optimized_comparisons = 0

# For regulations with district
for district in reg_districts.index:
    if pd.notna(district):
        regs_in_district = reg_districts[district]
        segments_in_district = segments_by_district.get(district, 0)
        optimized_comparisons += regs_in_district * segments_in_district

# For regulations with NULL district (must check all segments)
optimized_comparisons += reg_null_district * total_segments

reduction = current_comparisons - optimized_comparisons
reduction_pct = (reduction / current_comparisons) * 100

print(f"\n📊 With supervisor_district pre-filtering:")
print(f"   Comparisons (with district filter): {optimized_comparisons:,}")
print(f"   Reduction: {reduction:,} ({reduction_pct:.1f}%)")
print(f"   Estimated speedup: {current_comparisons/optimized_comparisons:.1f}x faster")

print("\n" + "="*70)
print("6. FEASIBILITY ASSESSMENT")
print("="*70)

feasible = True
warnings = []
recommendations = []

if reg_coverage < 70:
    warnings.append(f"Only {reg_coverage:.1f}% of regulations have supervisor_district")
    if reg_coverage < 50:
        feasible = False

if street_coverage < 70:
    warnings.append(f"Only {street_coverage:.1f}% of streets have supervisor_district")
    if street_coverage < 50:
        feasible = False

if reduction_pct < 50:
    warnings.append(f"Only {reduction_pct:.1f}% reduction in comparisons")
    if reduction_pct < 30:
        feasible = False

if multi_district_count > 0:
    recommendations.append(f"Handle {multi_district_count} multi-district regulations by parsing delimiters")

if len(common_districts) < len(reg_district_set):
    missing = reg_district_set - street_district_set
    warnings.append(f"Some regulation districts not in streets: {missing}")

print(f"\n{'✅ OPTIMIZATION IS FEASIBLE' if feasible else '❌ OPTIMIZATION NOT RECOMMENDED'}")

if warnings:
    print(f"\n⚠️  Warnings:")
    for w in warnings:
        print(f"   • {w}")

if recommendations:
    print(f"\n💡 Recommendations:")
    for r in recommendations:
        print(f"   • {r}")

if feasible:
    print(f"\n📈 Expected Performance Improvement:")
    print(f"   • {reduction_pct:.1f}% fewer comparisons")
    print(f"   • {current_comparisons/optimized_comparisons:.1f}x faster execution")
    print(f"   • Estimated time: 60-80 min → {60//(current_comparisons/optimized_comparisons)}-{80//(current_comparisons/optimized_comparisons)} min")
    
    print(f"\n🔧 Implementation Strategy:")
    print(f"   1. Pre-process: Group segments by supervisor_district")
    print(f"   2. For each regulation:")
    print(f"      a. If has supervisor_district: only check segments in that district")
    print(f"      b. If NULL supervisor_district: check all segments (fallback)")
    print(f"      c. If multi-district: check segments in all listed districts")
    print(f"   3. Maintain same spatial matching logic within filtered set")

print("\n" + "="*70)