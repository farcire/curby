#!/usr/bin/env python3
"""
Comprehensive Street Cleaning Dataset (yhqp-riqs) Analysis

This script analyzes the yhqp-riqs dataset to answer:
1. How many streets have missing opposite-side cleaning data?
2. Can FullName field identify 2nd/4th week schedules without week1-5 fields?
3. What is the data quality and completeness of all fields?

Generates reports for manual verification and override creation.
"""

import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd
import json
from collections import defaultdict
import re

load_dotenv()

STREET_CLEANING_ID = "yhqp-riqs"
ACTIVE_STREETS_ID = "3psu-pn9h"

def fetch_all_street_cleaning():
    """Fetch complete street cleaning dataset"""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    if not app_token:
        print("ERROR: SFMTA_APP_TOKEN not found")
        sys.exit(1)
    
    client = Socrata("data.sfgov.org", app_token)
    
    print("="*80)
    print("FETCHING STREET CLEANING DATASET (yhqp-riqs)")
    print("="*80)
    
    all_records = []
    offset = 0
    batch_size = 50000
    
    while True:
        print(f"  Fetching batch at offset {offset}...")
        batch = client.get(STREET_CLEANING_ID, limit=batch_size, offset=offset)
        
        if not batch:
            break
        
        all_records.extend(batch)
        print(f"  Retrieved {len(batch)} records (total: {len(all_records)})")
        
        if len(batch) < batch_size:
            break
        
        offset += batch_size
    
    print(f"\n✓ Total records fetched: {len(all_records)}")
    return pd.DataFrame.from_records(all_records)

def analyze_missing_opposite_sides(df):
    """
    Analyze CNNs with missing opposite-side cleaning data.
    Returns list of streets needing manual verification.
    """
    print("\n" + "="*80)
    print("ANALYSIS 1: MISSING OPPOSITE-SIDE CLEANING DATA")
    print("="*80)
    
    # Group by CNN to see which sides exist
    cnn_sides = defaultdict(lambda: {"L": [], "R": [], "corridor": None})
    
    for idx, row in df.iterrows():
        cnn = row.get("cnn")
        side = row.get("cnnrightleft")
        corridor = row.get("corridor") or row.get("streetname")
        
        if cnn and side:
            cnn_sides[cnn]["corridor"] = corridor
            cnn_sides[cnn][side].append(row.to_dict())
    
    # Find CNNs with only one side
    missing_opposite = []
    
    for cnn, data in cnn_sides.items():
        has_left = len(data["L"]) > 0
        has_right = len(data["R"]) > 0
        
        if has_left and not has_right:
            missing_opposite.append({
                "cnn": cnn,
                "corridor": data["corridor"],
                "present_side": "L",
                "missing_side": "R",
                "present_records": len(data["L"]),
                "sample_schedule": data["L"][0] if data["L"] else None
            })
        elif has_right and not has_left:
            missing_opposite.append({
                "cnn": cnn,
                "corridor": data["corridor"],
                "present_side": "R",
                "missing_side": "L",
                "present_records": len(data["R"]),
                "sample_schedule": data["R"][0] if data["R"] else None
            })
    
    # Sort by corridor name for easier manual verification
    missing_opposite.sort(key=lambda x: x["corridor"] or "")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total unique CNNs: {len(cnn_sides)}")
    print(f"   CNNs with BOTH sides: {sum(1 for d in cnn_sides.values() if len(d['L']) > 0 and len(d['R']) > 0)}")
    print(f"   CNNs with ONLY ONE side: {len(missing_opposite)}")
    print(f"   Coverage: {(1 - len(missing_opposite)/len(cnn_sides))*100:.1f}%")
    
    print(f"\n⚠️  STREETS NEEDING MANUAL VERIFICATION: {len(missing_opposite)}")
    print("\nFirst 20 examples:")
    for i, item in enumerate(missing_opposite[:20], 1):
        schedule = item["sample_schedule"]
        day = schedule.get("weekday", "?") if schedule else "?"
        time = f"{schedule.get('fromhour', '?')}-{schedule.get('tohour', '?')}" if schedule else "?"
        print(f"  {i}. CNN {item['cnn']} - {item['corridor']}")
        print(f"     Present: {item['present_side']} side ({day} {time})")
        print(f"     Missing: {item['missing_side']} side")
    
    return missing_opposite

def analyze_fullname_vs_week_fields(df):
    """
    Analyze if FullName field contains week-of-month info
    vs. using week1-5 fields.
    """
    print("\n" + "="*80)
    print("ANALYSIS 2: FULLNAME vs WEEK1-5 FIELDS")
    print("="*80)
    
    # Check what fields exist
    available_fields = df.columns.tolist()
    
    print(f"\n📋 Available Fields in Dataset:")
    print(f"   Total fields: {len(available_fields)}")
    
    # Check for FullName or similar
    name_fields = [f for f in available_fields if 'name' in f.lower() or 'full' in f.lower()]
    print(f"\n   Name-related fields: {name_fields}")
    
    # Check for week fields
    week_fields = [f for f in available_fields if 'week' in f.lower()]
    print(f"   Week-related fields: {week_fields}")
    
    # Analyze week1-5 fields if they exist
    week_field_analysis = {}
    for week_num in range(1, 6):
        field_name = f"week{week_num}ofmon"
        if field_name in available_fields:
            # Count how many records use this week
            week_count = df[field_name].value_counts()
            week_field_analysis[field_name] = week_count.to_dict()
    
    if week_field_analysis:
        print(f"\n📊 Week1-5 Field Usage:")
        for field, counts in week_field_analysis.items():
            print(f"   {field}: {counts}")
    
    # Analyze FullName field if it exists
    fullname_patterns = {}
    if 'fullname' in [f.lower() for f in available_fields]:
        fullname_field = [f for f in available_fields if f.lower() == 'fullname'][0]
        print(f"\n📊 FullName Field Analysis:")
        
        # Sample some FullName values
        sample_fullnames = df[fullname_field].dropna().head(50).tolist()
        
        # Look for week-of-month patterns
        week_patterns = {
            '1st': 0, '2nd': 0, '3rd': 0, '4th': 0, '5th': 0,
            'first': 0, 'second': 0, 'third': 0, 'fourth': 0, 'fifth': 0
        }
        
        for name in sample_fullnames:
            name_lower = str(name).lower()
            for pattern in week_patterns.keys():
                if pattern in name_lower:
                    week_patterns[pattern] += 1
        
        print(f"   Sample size: {len(sample_fullnames)}")
        print(f"   Week-of-month patterns found: {sum(week_patterns.values())}")
        print(f"   Pattern breakdown: {week_patterns}")
        
        # Show examples
        print(f"\n   Sample FullName values:")
        for i, name in enumerate(sample_fullnames[:10], 1):
            print(f"     {i}. {name}")
    
    # Compare week fields vs FullName
    print(f"\n🔍 COMPARISON:")
    
    if week_field_analysis:
        total_with_week_fields = sum(
            counts.get('Y', 0) + counts.get('1', 0) + counts.get(1, 0)
            for counts in week_field_analysis.values()
        )
        print(f"   Records using week1-5 fields: {total_with_week_fields}")
    
    # Create detailed report
    report = {
        "available_fields": available_fields,
        "name_fields": name_fields,
        "week_fields": week_fields,
        "week_field_analysis": week_field_analysis,
        "fullname_patterns": fullname_patterns
    }
    
    return report

def analyze_field_completeness(df):
    """Analyze completeness of all important fields"""
    print("\n" + "="*80)
    print("ANALYSIS 3: FIELD COMPLETENESS")
    print("="*80)
    
    important_fields = [
        'cnn', 'cnnrightleft', 'corridor', 'streetname', 'weekday',
        'fromhour', 'tohour', 'limits', 'holidays',
        'week1ofmon', 'week2ofmon', 'week3ofmon', 'week4ofmon', 'week5ofmon',
        'lf_fadd', 'lf_toadd', 'blockside'
    ]
    
    completeness = {}
    
    print(f"\n📊 Field Completeness (out of {len(df)} records):")
    print(f"\n{'Field':<20} {'Non-Null':<12} {'Null':<12} {'Completeness':<15}")
    print("-" * 60)
    
    for field in important_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            null_count = df[field].isna().sum()
            completeness_pct = (non_null / len(df)) * 100
            
            completeness[field] = {
                'non_null': int(non_null),
                'null': int(null_count),
                'completeness_pct': completeness_pct
            }
            
            print(f"{field:<20} {non_null:<12} {null_count:<12} {completeness_pct:>6.1f}%")
        else:
            print(f"{field:<20} {'FIELD NOT FOUND':<40}")
            completeness[field] = {'exists': False}
    
    return completeness

def generate_manual_verification_list(missing_opposite, output_file="street_cleaning_manual_verification.csv"):
    """Generate CSV for manual verification of missing opposite sides"""
    print("\n" + "="*80)
    print("GENERATING MANUAL VERIFICATION LIST")
    print("="*80)
    
    # Prepare data for CSV
    verification_data = []
    
    for item in missing_opposite:
        schedule = item["sample_schedule"]
        
        verification_data.append({
            "CNN": item["cnn"],
            "Street/Corridor": item["corridor"],
            "Present_Side": item["present_side"],
            "Missing_Side": item["missing_side"],
            "Present_Day": schedule.get("weekday") if schedule else "",
            "Present_Time": f"{schedule.get('fromhour')}-{schedule.get('tohour')}" if schedule else "",
            "Present_Limits": schedule.get("limits") if schedule else "",
            "Verification_Status": "",  # Empty for manual entry
            "Opposite_Side_Schedule": "",  # Empty for manual entry
            "Notes": ""  # Empty for manual entry
        })
    
    # Save to CSV
    df_verify = pd.DataFrame(verification_data)
    df_verify.to_csv(output_file, index=False)
    
    print(f"\n✓ Generated verification list: {output_file}")
    print(f"  Total streets to verify: {len(verification_data)}")
    print(f"\n📋 Instructions:")
    print(f"  1. Open {output_file} in Excel/Google Sheets")
    print(f"  2. For each street, physically verify if opposite side has cleaning")
    print(f"  3. Fill in 'Verification_Status' (CONFIRMED_MISSING / HAS_CLEANING / UNKNOWN)")
    print(f"  4. If HAS_CLEANING, fill in 'Opposite_Side_Schedule'")
    print(f"  5. Use this to create manual overrides")
    
    return output_file

def main():
    """Main analysis function"""
    print("\n" + "="*80)
    print("STREET CLEANING DATASET COMPREHENSIVE ANALYSIS")
    print("="*80)
    print(f"Dataset: yhqp-riqs (Street Sweeping Schedule)")
    print(f"Purpose: Generate reports for manual verification and data quality assessment")
    print("="*80)
    
    # Fetch data
    df = fetch_all_street_cleaning()
    
    # Analysis 1: Missing opposite sides
    missing_opposite = analyze_missing_opposite_sides(df)
    
    # Analysis 2: FullName vs week1-5 fields
    field_report = analyze_fullname_vs_week_fields(df)
    
    # Analysis 3: Field completeness
    completeness = analyze_field_completeness(df)
    
    # Generate manual verification list
    verification_file = generate_manual_verification_list(missing_opposite)
    
    # Save comprehensive report
    report = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "total_records": len(df),
        "missing_opposite_sides": {
            "count": len(missing_opposite),
            "streets": missing_opposite
        },
        "field_analysis": field_report,
        "field_completeness": completeness
    }
    
    report_file = "street_cleaning_analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n📄 Generated Files:")
    print(f"  1. {verification_file} - Manual verification list (CSV)")
    print(f"  2. {report_file} - Comprehensive analysis report (JSON)")
    
    print(f"\n📊 KEY FINDINGS:")
    print(f"  • Streets with missing opposite-side data: {len(missing_opposite)}")
    print(f"  • These require manual verification for override creation")
    print(f"  • Field completeness analysis saved to JSON report")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"  1. Review {verification_file} and verify streets physically")
    print(f"  2. Create manual overrides for confirmed missing data")
    print(f"  3. Review field analysis to determine if FullName can replace week1-5 fields")

if __name__ == "__main__":
    main()