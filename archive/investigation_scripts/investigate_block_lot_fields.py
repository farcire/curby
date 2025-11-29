#!/usr/bin/env python3
"""
Investigate Block Number / Block Lot concepts across all datasets
"""
import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import json

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def investigate_dataset(client, dataset_id, dataset_name):
    """Investigate a dataset for block/lot related fields"""
    print(f"\n{'='*80}")
    print(f"Dataset: {dataset_name} ({dataset_id})")
    print('='*80)
    
    try:
        # Fetch sample records
        results = client.get(dataset_id, limit=10)
        
        if not results:
            print("❌ No results returned")
            return None
        
        # Get all field names
        all_fields = list(results[0].keys())
        
        # Search for block/lot related fields
        block_lot_fields = []
        for field in all_fields:
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in [
                'block', 'lot', 'blklot', 'parcel', 'assessor', 
                'apn', 'mapblk', 'block_num', 'lot_num'
            ]):
                block_lot_fields.append(field)
        
        print(f"\n📋 Total Fields: {len(all_fields)}")
        print(f"🔍 Block/Lot Related Fields: {len(block_lot_fields)}")
        
        if block_lot_fields:
            print("\n✅ FOUND Block/Lot Fields:")
            for field in block_lot_fields:
                print(f"  - {field}")
            
            # Show sample values
            print("\n📊 Sample Values:")
            for i, record in enumerate(results[:3], 1):
                print(f"\n  Record {i}:")
                for field in block_lot_fields:
                    value = record.get(field, 'N/A')
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {field}: {value}")
            
            # Calculate coverage
            print("\n📈 Coverage Statistics:")
            for field in block_lot_fields:
                non_null_count = sum(1 for r in results if r.get(field))
                coverage = (non_null_count / len(results)) * 100
                print(f"  {field}: {non_null_count}/{len(results)} ({coverage:.1f}%)")
            
            return {
                'dataset_id': dataset_id,
                'dataset_name': dataset_name,
                'has_block_lot': True,
                'fields': block_lot_fields,
                'sample_records': results[:3]
            }
        else:
            print("\n❌ No Block/Lot fields found")
            print("\n📋 Available fields:")
            for field in sorted(all_fields)[:20]:  # Show first 20
                print(f"  - {field}")
            if len(all_fields) > 20:
                print(f"  ... and {len(all_fields) - 20} more")
            
            return {
                'dataset_id': dataset_id,
                'dataset_name': dataset_name,
                'has_block_lot': False,
                'fields': [],
                'all_fields': all_fields
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    print("="*80)
    print("BLOCK NUMBER / BLOCK LOT INVESTIGATION")
    print("="*80)
    print("\nSearching for block/lot concepts across datasets...")
    
    datasets = [
        ("i886-hxz9", "RPP Parcels (Residential Parking Permit Eligibility)"),
        ("3psu-pn7h", "Active Streets (Street Centerlines)"),
        ("pep9-66vw", "Parking Regulations (Blockface Geometries)"),
        ("hi6h-neyh", "Parking Regulations (Non-Metered)"),
        ("8juw-jybd", "Street Sweeping Schedules"),
    ]
    
    findings = []
    
    for dataset_id, dataset_name in datasets:
        result = investigate_dataset(client, dataset_id, dataset_name)
        if result:
            findings.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY OF FINDINGS")
    print("="*80)
    
    datasets_with_block_lot = [f for f in findings if f.get('has_block_lot')]
    datasets_without = [f for f in findings if not f.get('has_block_lot')]
    
    print(f"\n✅ Datasets WITH Block/Lot concepts: {len(datasets_with_block_lot)}")
    for f in datasets_with_block_lot:
        print(f"  - {f['dataset_name']}")
        print(f"    Fields: {', '.join(f['fields'])}")
    
    print(f"\n❌ Datasets WITHOUT Block/Lot concepts: {len(datasets_without)}")
    for f in datasets_without:
        print(f"  - {f['dataset_name']}")
    
    # Relationship to CNN architecture
    print("\n" + "="*80)
    print("RELATIONSHIP TO CNN-BASED ARCHITECTURE")
    print("="*80)
    
    if datasets_with_block_lot:
        print("\n🔗 How Block/Lot relates to CNN architecture:")
        print("\n1. RPP Parcels (if found):")
        print("   - Block/Lot = Assessor Parcel Number (APN)")
        print("   - Represents individual building footprints")
        print("   - Different granularity than street segments")
        print("   - Can be used for address-level validation")
        print("   - Requires spatial join to connect to CNN segments")
        
        print("\n2. Current CNN Architecture:")
        print("   - CNN = Centerline Network ID (street segment)")
        print("   - Primary key for all street-level data")
        print("   - Blockfaces = CNN + Side (L/R)")
        print("   - Parking regulations join via CNN")
        
        print("\n3. Integration Strategy:")
        print("   - Keep CNN as primary architecture")
        print("   - Use Block/Lot for supplementary validation")
        print("   - Spatial join: Parcel geometry → Street centerline")
        print("   - Enables 'Check My Address' features")
    else:
        print("\n✅ No Block/Lot fields found in core datasets")
        print("   Current CNN-based architecture is appropriate")
    
    client.close()
    
    return findings

if __name__ == "__main__":
    findings = main()