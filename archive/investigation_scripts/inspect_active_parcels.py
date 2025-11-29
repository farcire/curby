#!/usr/bin/env python3
"""
Investigate Active Parcels dataset (acdm-wktn)
This dataset contains comprehensive address and block/lot information
"""
import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import json

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def inspect_active_parcels():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    dataset_id = "acdm-wktn"
    
    print("="*80)
    print("ACTIVE PARCELS DATASET INVESTIGATION (acdm-wktn)")
    print("="*80)
    print("\nDataset: Active Parcels")
    print("Documentation: https://dev.socrata.com/foundry/data.sfgov.org/acdm-wktn")
    print()
    
    try:
        # Fetch sample records
        print("Fetching 10 sample records...")
        results = client.get(dataset_id, limit=10)
        
        if not results:
            print("❌ No results returned")
            return
        
        # Get all field names
        all_fields = list(results[0].keys())
        
        print(f"\n📋 Total Fields: {len(all_fields)}")
        print("\n📝 ALL AVAILABLE FIELDS:")
        for i, field in enumerate(sorted(all_fields), 1):
            print(f"  {i:2d}. {field}")
        
        # Search for key fields
        block_lot_fields = []
        address_fields = []
        street_fields = []
        
        for field in all_fields:
            field_lower = field.lower()
            
            # Block/Lot related
            if any(keyword in field_lower for keyword in [
                'block', 'lot', 'blklot', 'parcel', 'apn', 'mapblk'
            ]):
                block_lot_fields.append(field)
            
            # Address related
            if any(keyword in field_lower for keyword in [
                'address', 'number', 'from', 'to', 'odd', 'even'
            ]):
                address_fields.append(field)
            
            # Street related
            if any(keyword in field_lower for keyword in [
                'street', 'st_name', 'st_type'
            ]):
                street_fields.append(field)
        
        print("\n" + "="*80)
        print("🔍 KEY FIELD CATEGORIES")
        print("="*80)
        
        print(f"\n✅ Block/Lot Fields ({len(block_lot_fields)}):")
        for field in block_lot_fields:
            print(f"  - {field}")
        
        print(f"\n✅ Address Fields ({len(address_fields)}):")
        for field in address_fields:
            print(f"  - {field}")
        
        print(f"\n✅ Street Fields ({len(street_fields)}):")
        for field in street_fields:
            print(f"  - {field}")
        
        # Show sample records with key fields
        print("\n" + "="*80)
        print("📊 SAMPLE RECORDS (First 3)")
        print("="*80)
        
        for i, record in enumerate(results[:3], 1):
            print(f"\n--- Record {i} ---")
            
            # Block/Lot info
            if block_lot_fields:
                print("\n  Block/Lot Information:")
                for field in block_lot_fields:
                    value = record.get(field, 'N/A')
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {field}: {value}")
            
            # Address info
            if address_fields:
                print("\n  Address Information:")
                for field in address_fields:
                    value = record.get(field, 'N/A')
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {field}: {value}")
            
            # Street info
            if street_fields:
                print("\n  Street Information:")
                for field in street_fields:
                    value = record.get(field, 'N/A')
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {field}: {value}")
        
        # Coverage statistics
        print("\n" + "="*80)
        print("📈 COVERAGE STATISTICS")
        print("="*80)
        
        key_fields_to_check = block_lot_fields + address_fields + street_fields
        
        for field in key_fields_to_check[:20]:  # Check first 20 key fields
            non_null_count = sum(1 for r in results if r.get(field))
            coverage = (non_null_count / len(results)) * 100
            print(f"  {field}: {non_null_count}/{len(results)} ({coverage:.1f}%)")
        
        # Analysis
        print("\n" + "="*80)
        print("🎯 ANALYSIS")
        print("="*80)
        
        print("\n✅ This dataset appears to contain:")
        if block_lot_fields:
            print("  - Block/Lot identifiers (Assessor Parcel Numbers)")
        if address_fields:
            print("  - Address information (possibly with ranges)")
        if street_fields:
            print("  - Street names")
        
        print("\n💡 POTENTIAL USE CASES:")
        print("  1. Address-to-Block/Lot mapping")
        print("  2. Street name to parcel lookup")
        print("  3. Address range validation")
        print("  4. Comprehensive parcel directory")
        
        print("\n🔗 RELATIONSHIP TO CNN ARCHITECTURE:")
        print("  - This could bridge addresses → parcels → streets")
        print("  - May enable address-based queries")
        print("  - Could validate address ranges on street segments")
        
        # Check for geometry
        if 'shape' in all_fields or 'geometry' in all_fields or 'the_geom' in all_fields:
            print("\n✅ Dataset includes geometry - can do spatial joins!")
        else:
            print("\n⚠️  No obvious geometry field found")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_active_parcels()