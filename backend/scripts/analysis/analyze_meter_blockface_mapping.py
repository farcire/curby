"""
Analyze Meters by Blockface Dataset
Determine if:
1. All meters can be mapped to a blockface
2. All metered blockfaces can be mapped to a CNN
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv()

SFMTA_DOMAIN = "data.sfgov.org"
METERED_BLOCKFACES_ID = "mk27-a5x2"    # Metered Blockfaces (Metadata)
METERS_DATASET_ID = "8vzz-qzz9"        # Parking Meters
BLOCKFACE_GEOMETRY_ID = "pep9-66vw"    # Blockface geometry

def analyze_meter_blockface_mapping():
    """Analyze the mapping between meters, blockfaces, and CNNs"""
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata(SFMTA_DOMAIN, app_token)
    
    print("="*80)
    print("METERS BY BLOCKFACE MAPPING ANALYSIS")
    print("="*80)
    
    # 1. Fetch sample of meters dataset
    print("\n1. Fetching meters dataset...")
    print("-"*80)
    
    meters = client.get(METERS_DATASET_ID, limit=100)
    meters_df = pd.DataFrame.from_records(meters)
    
    print(f"✓ Fetched {len(meters_df)} meter records")
    print(f"\nColumns: {list(meters_df.columns)}")
    
    # Show sample record
    if not meters_df.empty:
        print("\nSample meter record:")
        sample = meters_df.iloc[0]
        for col in meters_df.columns:
            print(f"  {col:30s}: {sample[col]}")
    
    # 2. Check for blockface_id field
    print("\n2. Checking blockface_id field...")
    print("-"*80)
    
    if 'blockface_id' in meters_df.columns:
        has_blockface = meters_df['blockface_id'].notna().sum()
        total = len(meters_df)
        print(f"✓ blockface_id field exists")
        print(f"  Records with blockface_id: {has_blockface}/{total} ({has_blockface/total*100:.1f}%)")
        
        # Show sample blockface IDs
        sample_ids = meters_df['blockface_id'].dropna().head(5).tolist()
        print(f"  Sample blockface_ids: {sample_ids}")
    else:
        print("✗ No blockface_id field found")
        print(f"  Available fields: {list(meters_df.columns)}")
    
    # 3. Check for CNN field
    print("\n3. Checking for CNN field in meters...")
    print("-"*80)
    
    cnn_fields = [col for col in meters_df.columns if 'cnn' in col.lower()]
    if cnn_fields:
        print(f"✓ Found CNN-related fields: {cnn_fields}")
        for field in cnn_fields:
            has_cnn = meters_df[field].notna().sum()
            print(f"  {field}: {has_cnn}/{len(meters_df)} records ({has_cnn/len(meters_df)*100:.1f}%)")
    else:
        print("✗ No CNN field found in meters dataset")
    
    # 4. Fetch blockface geometry to check CNN mapping
    print("\n4. Fetching blockface geometry dataset...")
    print("-"*80)
    
    blockfaces = client.get(BLOCKFACE_GEOMETRY_ID, limit=100)
    blockfaces_df = pd.DataFrame.from_records(blockfaces)
    
    print(f"✓ Fetched {len(blockfaces_df)} blockface records")
    
    # Check for CNN in blockfaces
    if 'cnn_id' in blockfaces_df.columns:
        has_cnn = blockfaces_df['cnn_id'].notna().sum()
        print(f"✓ cnn_id field exists in blockfaces")
        print(f"  Blockfaces with CNN: {has_cnn}/{len(blockfaces_df)} ({has_cnn/len(blockfaces_df)*100:.1f}%)")
    else:
        print("✗ No cnn_id field in blockfaces")
    
    # 5. Try to match meters to blockfaces
    print("\n5. Attempting to match meters to blockfaces...")
    print("-"*80)
    
    if 'blockface_id' in meters_df.columns and not meters_df.empty:
        # Get unique blockface IDs from meters
        meter_blockface_ids = set(meters_df['blockface_id'].dropna().astype(str))
        print(f"Unique blockface_ids in meters: {len(meter_blockface_ids)}")
        
        # Check if blockfaces have matching IDs
        if 'blockface_id' in blockfaces_df.columns:
            blockface_ids = set(blockfaces_df['blockface_id'].dropna().astype(str))
            print(f"Unique blockface_ids in blockfaces: {len(blockface_ids)}")
            
            # Find matches
            matches = meter_blockface_ids.intersection(blockface_ids)
            print(f"Matching blockface_ids: {len(matches)}")
            print(f"Match rate: {len(matches)/len(meter_blockface_ids)*100:.1f}%")
        elif 'globalid' in blockfaces_df.columns:
            # Try matching with globalid
            globalids = set(blockfaces_df['globalid'].dropna().astype(str))
            print(f"Unique globalids in blockfaces: {len(globalids)}")
            
            matches = meter_blockface_ids.intersection(globalids)
            print(f"Matching with globalid: {len(matches)}")
            print(f"Match rate: {len(matches)/len(meter_blockface_ids)*100:.1f}%")
    
    # 6. Summary
    print("\n6. SUMMARY")
    print("="*80)
    
    print("\nMapping Chain:")
    print("  Meters → blockface_id → Blockface Geometry → cnn_id → CNN")
    
    print("\nKey Questions:")
    print("  Q1: Can all meters be mapped to a blockface?")
    if 'blockface_id' in meters_df.columns:
        coverage = meters_df['blockface_id'].notna().sum() / len(meters_df) * 100
        print(f"      A: {coverage:.1f}% of meters have blockface_id")
    else:
        print("      A: Unknown - no blockface_id field found")
    
    print("\n  Q2: Can all metered blockfaces be mapped to a CNN?")
    if 'cnn_id' in blockfaces_df.columns:
        coverage = blockfaces_df['cnn_id'].notna().sum() / len(blockfaces_df) * 100
        print(f"      A: {coverage:.1f}% of blockfaces have cnn_id")
    else:
        print("      A: Unknown - no cnn_id field found")
    
    # 7. Get full dataset statistics
    print("\n7. FULL DATASET STATISTICS")
    print("-"*80)
    
    # Count total meters
    total_meters = client.get(METERS_DATASET_ID, select="COUNT(*)")
    print(f"Total meters in dataset: {total_meters[0].get('COUNT_post_id', 'Unknown')}")
    
    # Count total metered blockfaces
    total_metered_bf = client.get(METERED_BLOCKFACES_ID, select="COUNT(*)")
    print(f"Total metered blockfaces: {total_metered_bf[0].get('COUNT_blockface_id', 'Unknown')}")
    
    # Count total blockfaces
    total_blockfaces = client.get(BLOCKFACE_GEOMETRY_ID, select="COUNT(*)")
    print(f"Total blockfaces in dataset: {total_blockfaces[0].get('COUNT_globalid', 'Unknown')}")
    
    client.close()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    analyze_meter_blockface_mapping()