#!/usr/bin/env python3
"""
Analyze Active Streets dataset (3psu-pn9h) to determine if there are cases
where only one side (L or R) has address data.

This will help inform the master CNN reference file design.
"""

import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
from collections import defaultdict

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def analyze_active_streets_sides():
    """Analyze Active Streets for one-sided segments"""
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("Error: SFMTA_APP_TOKEN not found in environment")
        return
    
    client = Socrata("data.sfgov.org", app_token)
    
    # Active Streets dataset
    dataset_id = "3psu-pn9h"
    
    print("="*80)
    print("ACTIVE STREETS (3psu-pn9h) ONE-SIDED SEGMENT ANALYSIS")
    print("="*80)
    
    # First, get a sample record to understand the schema
    print("\n1. Fetching sample record to understand schema...")
    sample = client.get(dataset_id, limit=1)
    if sample:
        df_sample = pd.DataFrame.from_records(sample)
        print("\nAvailable columns:")
        print(df_sample.columns.tolist())
        print("\nSample record:")
        for col in df_sample.columns:
            print(f"  {col}: {df_sample.iloc[0][col]}")
    
    # Fetch all active streets (filter for active=True or blank)
    print("\n2. Fetching all Active Streets records...")
    print("   Filtering for: active='True' OR active is NULL/blank")
    
    # Fetch in batches
    all_records = []
    offset = 0
    batch_size = 50000
    
    while True:
        print(f"   Fetching batch starting at offset {offset}...")
        
        # Query for active streets only
        # Note: We want active='True' OR active is NULL
        batch = client.get(
            dataset_id,
            limit=batch_size,
            offset=offset,
            where="active='True' OR active IS NULL"
        )
        
        if not batch:
            break
        
        all_records.extend(batch)
        print(f"   Retrieved {len(batch)} records (total so far: {len(all_records)})")
        
        if len(batch) < batch_size:
            break
        
        offset += batch_size
    
    print(f"\n✓ Total active streets fetched: {len(all_records)}")
    
    if not all_records:
        print("ERROR: No records retrieved!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame.from_records(all_records)
    
    print("\n3. Analyzing address range fields...")
    
    # Check which address fields exist
    address_fields = ['lf_fadd', 'lf_toadd', 'rt_fadd', 'rt_toadd']
    existing_fields = [f for f in address_fields if f in df.columns]
    
    print(f"\nAddress range fields found: {existing_fields}")
    
    if not all(f in df.columns for f in address_fields):
        print("\n⚠️  WARNING: Not all expected address fields are present!")
        print(f"   Expected: {address_fields}")
        print(f"   Found: {existing_fields}")
    
    # Analyze one-sided segments
    print("\n4. Analyzing one-sided segments...")
    
    # Convert address fields to numeric, treating empty/null as NaN
    for field in existing_fields:
        df[field] = pd.to_numeric(df[field], errors='coerce')
    
    # Determine which sides have data
    df['has_left_data'] = df['lf_fadd'].notna() | df['lf_toadd'].notna()
    df['has_right_data'] = df['rt_fadd'].notna() | df['rt_toadd'].notna()
    
    # Categorize segments
    both_sides = df[df['has_left_data'] & df['has_right_data']]
    left_only = df[df['has_left_data'] & ~df['has_right_data']]
    right_only = df[~df['has_left_data'] & df['has_right_data']]
    neither_side = df[~df['has_left_data'] & ~df['has_right_data']]
    
    # Generate report
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    
    total = len(df)
    print(f"\nTotal active street segments: {total:,}")
    print(f"\nSegments with BOTH L and R address data: {len(both_sides):,} ({len(both_sides)/total*100:.1f}%)")
    print(f"Segments with ONLY L address data: {len(left_only):,} ({len(left_only)/total*100:.1f}%)")
    print(f"Segments with ONLY R address data: {len(right_only):,} ({len(right_only)/total*100:.1f}%)")
    print(f"Segments with NO address data: {len(neither_side):,} ({len(neither_side)/total*100:.1f}%)")
    
    one_sided_total = len(left_only) + len(right_only)
    print(f"\n⚠️  ONE-SIDED SEGMENTS: {one_sided_total:,} ({one_sided_total/total*100:.1f}%)")
    
    # Show examples of one-sided segments
    if len(left_only) > 0:
        print("\n" + "-"*80)
        print("EXAMPLES: LEFT SIDE ONLY (First 10)")
        print("-"*80)
        for idx, row in left_only.head(10).iterrows():
            cnn = row.get('cnn', 'N/A')
            street = row.get('streetname', 'N/A')
            lf = row.get('lf_fadd', 'N/A')
            lt = row.get('lf_toadd', 'N/A')
            print(f"\nCNN {cnn}: {street}")
            print(f"  L side: {lf}-{lt}")
            print(f"  R side: (empty)")
    
    if len(right_only) > 0:
        print("\n" + "-"*80)
        print("EXAMPLES: RIGHT SIDE ONLY (First 10)")
        print("-"*80)
        for idx, row in right_only.head(10).iterrows():
            cnn = row.get('cnn', 'N/A')
            street = row.get('streetname', 'N/A')
            rf = row.get('rt_fadd', 'N/A')
            rt = row.get('rt_toadd', 'N/A')
            print(f"\nCNN {cnn}: {street}")
            print(f"  L side: (empty)")
            print(f"  R side: {rf}-{rt}")
    
    if len(neither_side) > 0:
        print("\n" + "-"*80)
        print("EXAMPLES: NO ADDRESS DATA (First 10)")
        print("-"*80)
        for idx, row in neither_side.head(10).iterrows():
            cnn = row.get('cnn', 'N/A')
            street = row.get('streetname', 'N/A')
            print(f"CNN {cnn}: {street} - No address ranges")
    
    # Save detailed results
    output_file = 'active_streets_sides_analysis.json'
    
    results = {
        'summary': {
            'total_segments': total,
            'both_sides': len(both_sides),
            'left_only': len(left_only),
            'right_only': len(right_only),
            'neither_side': len(neither_side),
            'one_sided_total': one_sided_total,
            'both_sides_pct': round(len(both_sides)/total*100, 2),
            'one_sided_pct': round(one_sided_total/total*100, 2),
            'no_address_pct': round(len(neither_side)/total*100, 2)
        },
        'left_only_examples': left_only.head(20).to_dict('records') if len(left_only) > 0 else [],
        'right_only_examples': right_only.head(20).to_dict('records') if len(right_only) > 0 else [],
        'neither_side_examples': neither_side.head(20).to_dict('records') if len(neither_side) > 0 else []
    }
    
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n\n📄 Detailed results saved to: {output_file}")
    
    # Key insights
    print("\n" + "="*80)
    print("KEY INSIGHTS FOR MASTER FILE DESIGN")
    print("="*80)
    
    if one_sided_total > 0:
        print(f"\n⚠️  CRITICAL: {one_sided_total:,} segments ({one_sided_total/total*100:.1f}%) have address data on only ONE side")
        print("\nIMPLICATIONS:")
        print("  1. Master file MUST support one-sided entries")
        print("  2. Cannot assume both L and R entries exist for every CNN")
        print("  3. Conditional entry creation is REQUIRED")
        print("\nRECOMMENDED APPROACH:")
        print("  • Create L entry ONLY if lf_fadd/lf_toadd exist")
        print("  • Create R entry ONLY if rt_fadd/rt_toadd exist")
        print("  • Expected total entries: ~{:,} (not {:,})".format(
            len(both_sides)*2 + one_sided_total,
            total*2
        ))
    else:
        print("\n✅ ALL segments have address data on BOTH sides")
        print("\nIMPLICATIONS:")
        print("  • Can safely create both L and R entries for every CNN")
        print("  • Expected total entries: {:,} (CNN count × 2)".format(total*2))
    
    if len(neither_side) > 0:
        print(f"\n⚠️  NOTE: {len(neither_side):,} segments have NO address data at all")
        print("  These may be:")
        print("  • Alleys or paths without addresses")
        print("  • Freeway segments")
        print("  • Data quality issues")
        print("  • Should be excluded from master file or flagged")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    analyze_active_streets_sides()