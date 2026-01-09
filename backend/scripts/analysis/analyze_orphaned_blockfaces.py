"""
Analyze Orphaned Blockface Records

This script examines the blockface geometry dataset (pep9-66vw) to:
1. Identify records missing CNN IDs
2. Analyze what metadata is available for fuzzy matching
3. Quantify the opportunity for data recovery
4. Show examples of orphaned records with rich metadata
"""

import os
import sys
from dotenv import load_dotenv
import pandas as pd
from sodapy import Socrata
import json

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SFMTA_DOMAIN = "data.sfgov.org"
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"

def fetch_blockface_data():
    """Fetch the blockface geometry dataset."""
    app_token = os.getenv("SFMTA_APP_TOKEN")
    
    print(f"Fetching blockface dataset {BLOCKFACE_GEOMETRY_ID}...")
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(BLOCKFACE_GEOMETRY_ID, limit=50000)
        df = pd.DataFrame.from_records(results)
        print(f"✓ Fetched {len(df)} blockface records")
        return df
    except Exception as e:
        print(f"ERROR fetching dataset: {e}")
        return pd.DataFrame()

def analyze_dataset(df):
    """Analyze the blockface dataset structure and missing data."""
    
    print("\n" + "="*80)
    print("BLOCKFACE DATASET ANALYSIS")
    print("="*80)
    
    # 1. Show all available columns
    print("\n1. AVAILABLE COLUMNS:")
    print("-" * 80)
    for i, col in enumerate(df.columns, 1):
        non_null = df[col].notna().sum()
        pct = (non_null / len(df)) * 100
        print(f"  {i:2d}. {col:30s} - {non_null:5d}/{len(df):5d} non-null ({pct:5.1f}%)")
    
    # 2. Analyze records with/without CNN
    print("\n2. CNN ID COVERAGE:")
    print("-" * 80)
    has_cnn = df['cnn_id'].notna().sum() if 'cnn_id' in df.columns else 0
    missing_cnn = len(df) - has_cnn
    
    print(f"  Records WITH CNN ID:    {has_cnn:5d} ({has_cnn/len(df)*100:5.1f}%)")
    print(f"  Records WITHOUT CNN ID: {missing_cnn:5d} ({missing_cnn/len(df)*100:5.1f}%)")
    
    # 3. Analyze orphaned records (no CNN but has geometry)
    print("\n3. ORPHANED RECORDS (No CNN but has geometry):")
    print("-" * 80)
    
    orphaned = df[df['cnn_id'].isna() & df['shape'].notna()] if 'cnn_id' in df.columns and 'shape' in df.columns else pd.DataFrame()
    
    if not orphaned.empty:
        print(f"  Total orphaned records: {len(orphaned)}")
        
        # Check what metadata orphaned records have
        metadata_fields = ['name', 'popupinfo', 'street_nam', 'blockface_',
                          'sfpark_id', 'globalid']
        
        print("\n  Metadata availability in orphaned records:")
        for field in metadata_fields:
            if field in orphaned.columns:
                has_data = orphaned[field].notna().sum()
                pct = (has_data / len(orphaned)) * 100
                print(f"    {field:20s}: {has_data:5d}/{len(orphaned):5d} ({pct:5.1f}%)")
        
        # 4. Show examples of orphaned records with rich metadata
        print("\n4. EXAMPLE ORPHANED RECORDS WITH RICH METADATA:")
        print("-" * 80)
        
        # Find orphaned records that have popupinfo
        rich_orphans = orphaned[orphaned['popupinfo'].notna()] if 'popupinfo' in orphaned.columns else pd.DataFrame()
        
        if not rich_orphans.empty:
            print(f"\n  Showing up to 10 examples from {len(rich_orphans)} orphaned records with popupinfo:\n")
            
            for idx, (_, row) in enumerate(rich_orphans.head(10).iterrows(), 1):
                print(f"  Example {idx}:")
                print(f"    Name: {row.get('name', 'N/A')}")
                
                # Parse popupinfo field
                popup = row.get('popupinfo', '')
                if popup and isinstance(popup, str):
                    print(f"    PopupInfo: {popup[:200]}...")  # Show first 200 chars
                
                if 'street_nam' in row and pd.notna(row['street_nam']):
                    print(f"    Street: {row['street_nam']}")
                if 'blockface_' in row and pd.notna(row['blockface_']):
                    print(f"    Blockface ID: {row['blockface_']}")
                if 'sfpark_id' in row and pd.notna(row['sfpark_id']):
                    print(f"    SFPark ID: {row['sfpark_id']}")
                if 'globalid' in row and pd.notna(row['globalid']):
                    print(f"    GlobalID: {row['globalid']}")
                
                # Show if it has geometry
                has_geo = 'Yes' if pd.notna(row.get('shape')) else 'No'
                print(f"    Has Geometry: {has_geo}")
                print()
        else:
            print("  No orphaned records found with name field populated")
    else:
        print("  No orphaned records found")
    
    # 5. Potential for fuzzy matching
    print("\n5. FUZZY MATCHING POTENTIAL:")
    print("-" * 80)
    
    if not orphaned.empty:
        # Count how many orphaned records have enough data for fuzzy matching
        matchable = orphaned[
            orphaned['name'].notna() | 
            (orphaned['street_name'].notna() if 'street_name' in orphaned.columns else False)
        ] if 'name' in orphaned.columns else pd.DataFrame()
        
        if not matchable.empty:
            print(f"  Orphaned records with street name data: {len(matchable)}")
            print(f"  Potential data recovery: {len(matchable)} blockface geometries")
            print(f"  Current loss: {len(matchable)/len(df)*100:.1f}% of total dataset")
            
            # Estimate impact
            print("\n  ESTIMATED IMPACT:")
            print(f"    - Could recover {len(matchable)} additional blockface geometries")
            print(f"    - This represents {len(matchable)/(has_cnn+len(matchable))*100:.1f}% increase in coverage")
        else:
            print("  No orphaned records have sufficient metadata for fuzzy matching")
    
    # 6. Save detailed report
    print("\n6. SAVING DETAILED REPORT:")
    print("-" * 80)
    
    report = {
        "total_records": len(df),
        "records_with_cnn": int(has_cnn),
        "records_without_cnn": int(missing_cnn),
        "orphaned_with_geometry": len(orphaned),
        "orphaned_with_name": len(rich_orphans) if not rich_orphans.empty else 0,
        "columns": list(df.columns),
        "sample_orphaned_records": []
    }
    
    if not rich_orphans.empty:
        for _, row in rich_orphans.head(20).iterrows():
            sample = {
                "name": str(row.get('name', '')),
                "popupinfo": str(row.get('popupinfo', ''))[:500],  # First 500 chars
                "street_nam": str(row.get('street_nam', '')),
                "blockface_": str(row.get('blockface_', '')),
                "sfpark_id": str(row.get('sfpark_id', '')),
                "globalid": str(row.get('globalid', '')),
                "has_geometry": bool(pd.notna(row.get('shape')))
            }
            report["sample_orphaned_records"].append(sample)
    
    report_path = "orphaned_blockfaces_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"  ✓ Saved detailed report to: {report_path}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

def main():
    """Main analysis function."""
    df = fetch_blockface_data()
    
    if df.empty:
        print("ERROR: Could not fetch blockface data")
        return
    
    analyze_dataset(df)

if __name__ == "__main__":
    main()