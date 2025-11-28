#!/usr/bin/env python3
"""
Investigate Enterprise Addressing System (EAS) dataset (ramy-di5m)
This is THE master address database linking addresses, CNN, parcels, blocks
"""
import os
import sys
from dotenv import load_dotenv
from sodapy import Socrata
import json

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

def inspect_eas():
    app_token = os.getenv("SFMTA_APP_TOKEN")
    client = Socrata("data.sfgov.org", app_token)
    
    dataset_id = "ramy-di5m"
    
    print("="*80)
    print("ENTERPRISE ADDRESSING SYSTEM (EAS) INVESTIGATION (ramy-di5m)")
    print("="*80)
    print("\nDataset: San Francisco Addresses with Units - Enterprise Addressing System")
    print("Documentation: https://dev.socrata.com/foundry/data.sfgov.org/ramy-di5m")
    print("\n🎯 THIS IS THE MASTER ADDRESS DATABASE!")
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
        
        # Categorize fields
        cnn_fields = []
        address_fields = []
        block_lot_fields = []
        street_fields = []
        zip_fields = []
        
        for field in all_fields:
            field_lower = field.lower()
            
            # CNN related
            if 'cnn' in field_lower or 'centerline' in field_lower:
                cnn_fields.append(field)
            
            # Block/Lot related
            if any(keyword in field_lower for keyword in [
                'block', 'lot', 'blklot', 'parcel', 'apn', 'mapblk'
            ]):
                block_lot_fields.append(field)
            
            # Address related
            if any(keyword in field_lower for keyword in [
                'address', 'number', 'street_number', 'unit'
            ]):
                address_fields.append(field)
            
            # Street related
            if any(keyword in field_lower for keyword in [
                'street', 'st_name', 'st_type'
            ]):
                street_fields.append(field)
            
            # ZIP related
            if 'zip' in field_lower or 'postal' in field_lower:
                zip_fields.append(field)
        
        print("\n" + "="*80)
        print("🔍 KEY FIELD CATEGORIES")
        print("="*80)
        
        print(f"\n⭐ CNN Fields ({len(cnn_fields)}):")
        for field in cnn_fields:
            print(f"  - {field}")
        
        print(f"\n⭐ Block/Lot Fields ({len(block_lot_fields)}):")
        for field in block_lot_fields:
            print(f"  - {field}")
        
        print(f"\n⭐ Address Fields ({len(address_fields)}):")
        for field in address_fields:
            print(f"  - {field}")
        
        print(f"\n⭐ Street Fields ({len(street_fields)}):")
        for field in street_fields:
            print(f"  - {field}")
        
        print(f"\n⭐ ZIP Code Fields ({len(zip_fields)}):")
        for field in zip_fields:
            print(f"  - {field}")
        
        # Show sample records
        print("\n" + "="*80)
        print("📊 SAMPLE RECORDS (First 3)")
        print("="*80)
        
        for i, record in enumerate(results[:3], 1):
            print(f"\n{'='*80}")
            print(f"Record {i}")
            print('='*80)
            
            # CNN info
            if cnn_fields:
                print("\n  🔗 CNN (Centerline Network) Information:")
                for field in cnn_fields:
                    value = record.get(field, 'N/A')
                    print(f"    {field}: {value}")
            
            # Block/Lot info
            if block_lot_fields:
                print("\n  📦 Block/Lot Information:")
                for field in block_lot_fields:
                    value = record.get(field, 'N/A')
                    print(f"    {field}: {value}")
            
            # Address info
            if address_fields:
                print("\n  🏠 Address Information:")
                for field in address_fields:
                    value = record.get(field, 'N/A')
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {field}: {value}")
            
            # Street info
            if street_fields:
                print("\n  🛣️  Street Information:")
                for field in street_fields:
                    value = record.get(field, 'N/A')
                    print(f"    {field}: {value}")
            
            # ZIP info
            if zip_fields:
                print("\n  📮 ZIP Code Information:")
                for field in zip_fields:
                    value = record.get(field, 'N/A')
                    print(f"    {field}: {value}")
        
        # Coverage statistics
        print("\n" + "="*80)
        print("📈 COVERAGE STATISTICS (Key Fields)")
        print("="*80)
        
        key_fields = cnn_fields + block_lot_fields + address_fields[:5] + street_fields[:3]
        
        for field in key_fields:
            non_null_count = sum(1 for r in results if r.get(field))
            coverage = (non_null_count / len(results)) * 100
            print(f"  {field}: {non_null_count}/{len(results)} ({coverage:.1f}%)")
        
        # Critical analysis
        print("\n" + "="*80)
        print("🎯 CRITICAL ANALYSIS")
        print("="*80)
        
        print("\n✅ THIS DATASET PROVIDES:")
        if cnn_fields:
            print("  ⭐ CNN (Centerline Network ID) - LINKS TO STREETS!")
        if block_lot_fields:
            print("  ⭐ Block/Lot Numbers - LINKS TO PARCELS!")
        if address_fields:
            print("  ⭐ Full Address Information - USER INPUT!")
        if street_fields:
            print("  ⭐ Street Names - SEARCHABLE!")
        if zip_fields:
            print("  ⭐ ZIP Codes - GEOGRAPHIC GROUPING!")
        
        print("\n🔗 RELATIONSHIP CHAIN:")
        print("  Address → CNN → Street Segment → Blockface → Parking Rules")
        print("  Address → Block/Lot → Parcel → RPP Area")
        print("  Address → ZIP Code → Neighborhood")
        
        print("\n💡 GAME-CHANGING CAPABILITIES:")
        print("  1. Direct address-to-CNN mapping")
        print("  2. Determine L/R side from address number (odd/even)")
        print("  3. Link addresses to parcels via block/lot")
        print("  4. Complete address validation")
        print("  5. ZIP code-based queries")
        
        print("\n🚀 USE CASES:")
        print("  • User enters '123 Valencia St' → Find CNN → Get parking rules")
        print("  • Validate address exists in SF")
        print("  • Determine which side of street (odd/even)")
        print("  • Link to parcel for RPP eligibility")
        print("  • Search by ZIP code")
        
        print("\n⚠️  IMPORTANT CONSIDERATIONS:")
        print("  • Dataset size: Potentially 500K+ addresses")
        print("  • May include units (apartments, suites)")
        print("  • Need to handle address normalization")
        print("  • Critical for address-based queries")
        
        # Check for geometry
        if 'shape' in all_fields or 'geometry' in all_fields or 'point' in all_fields:
            print("\n✅ Dataset includes geometry - can do spatial queries!")
        else:
            print("\n⚠️  No obvious geometry field - may need geocoding")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_eas()