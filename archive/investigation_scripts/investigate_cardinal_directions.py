"""
Investigate all SFMTA datasets for cardinal direction fields and design master CNN join database.

This script examines:
1. All datasets with cardinal direction information
2. Fields that can help map CNN L/R to cardinal directions
3. Design for a master join database
"""

import os
from dotenv import load_dotenv
from sodapy import Socrata
import pandas as pd

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SFMTA_DOMAIN = "data.sfgov.org"
app_token = os.getenv("SFMTA_APP_TOKEN")

# Known datasets
DATASETS = {
    "Active Streets": "3psu-pn9h",
    "Blockface Geometries": "pep9-66vw", 
    "Street Cleaning": "yhqp-riqs",
    "Parking Regulations": "hi6h-neyh",
    "Parking Meters": "8vzz-qzz9",
    "Meter Schedules": "6cqg-dxku",
    "Street Intersections": "fqt9-tat9",
    "EAS Addresses": "dxjs-vqsy"
}

def investigate_dataset(dataset_id: str, dataset_name: str, limit: int = 5):
    """Investigate a dataset for cardinal direction and CNN-related fields."""
    print(f"\n{'='*80}")
    print(f"Dataset: {dataset_name} ({dataset_id})")
    print(f"{'='*80}")
    
    try:
        client = Socrata(SFMTA_DOMAIN, app_token)
        results = client.get(dataset_id, limit=limit)
        
        if not results:
            print("  No data returned")
            return
        
        df = pd.DataFrame.from_records(results)
        print(f"\n  Total columns: {len(df.columns)}")
        
        # Look for cardinal direction fields
        cardinal_fields = []
        cnn_fields = []
        geometry_fields = []
        address_fields = []
        location_fields = []
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Cardinal direction indicators
            if any(x in col_lower for x in ['cardinal', 'direction', 'corridor', 'blockside', 'side']):
                cardinal_fields.append(col)
            
            # CNN related
            if 'cnn' in col_lower:
                cnn_fields.append(col)
            
            # Geometry
            if any(x in col_lower for x in ['geometry', 'shape', 'line', 'point', 'location']):
                geometry_fields.append(col)
            
            # Address
            if any(x in col_lower for x in ['address', 'fadd', 'toadd', 'number']):
                address_fields.append(col)
            
            # Location identifiers
            if any(x in col_lower for x in ['street', 'block', 'neighborhood', 'district', 'supervisor']):
                location_fields.append(col)
        
        if cardinal_fields:
            print(f"\n  ✅ CARDINAL DIRECTION FIELDS FOUND:")
            for field in cardinal_fields:
                sample_values = df[field].dropna().unique()[:5]
                print(f"    - {field}: {list(sample_values)}")
        
        if cnn_fields:
            print(f"\n  CNN-RELATED FIELDS:")
            for field in cnn_fields:
                print(f"    - {field}")
        
        if geometry_fields:
            print(f"\n  GEOMETRY FIELDS:")
            for field in geometry_fields:
                print(f"    - {field}")
        
        if address_fields:
            print(f"\n  ADDRESS FIELDS:")
            for field in address_fields:
                print(f"    - {field}")
        
        if location_fields:
            print(f"\n  LOCATION FIELDS:")
            for field in location_fields[:10]:  # Limit to first 10
                print(f"    - {field}")
        
        # Show sample record
        print(f"\n  Sample record keys:")
        for key in list(df.columns)[:15]:
            print(f"    - {key}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    print("="*80)
    print("INVESTIGATING SFMTA DATASETS FOR CARDINAL DIRECTIONS")
    print("="*80)
    
    for name, dataset_id in DATASETS.items():
        investigate_dataset(dataset_id, name)
    
    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)
    
    print("\n\nKEY FINDINGS:")
    print("1. Street Cleaning dataset (yhqp-riqs) has 'blockside' field with cardinal directions")
    print("2. Active Streets (3psu-pn9h) has address ranges (lf_fadd, lf_toadd, rt_fadd, rt_toadd)")
    print("3. All datasets use CNN as primary join key")
    print("4. Blockface Geometries (pep9-66vw) has precise geometry for each side")
    
    print("\n\nMASTER JOIN DATABASE DESIGN:")
    print("Collection: cnn_master_join")
    print("Purpose: Fast lookup for CNN → all related identifiers and metadata")
    print("\nSchema:")
    print("  - cnn: Primary key")
    print("  - cnn_left: CNN + 'L' composite key")
    print("  - cnn_right: CNN + 'R' composite key")
    print("  - street_name: Street name")
    print("  - from_street: Intersection start")
    print("  - to_street: Intersection end")
    print("  - left_side:")
    print("      - cardinal_direction: N, S, E, W, etc.")
    print("      - from_address: Starting address (odd)")
    print("      - to_address: Ending address (odd)")
    print("      - blockface_id: GlobalID from blockface geometries")
    print("      - geometry: GeoJSON LineString")
    print("      - centroid: [lng, lat]")
    print("  - right_side:")
    print("      - cardinal_direction: N, S, E, W, etc.")
    print("      - from_address: Starting address (even)")
    print("      - to_address: Ending address (even)")
    print("      - blockface_id: GlobalID from blockface geometries")
    print("      - geometry: GeoJSON LineString")
    print("      - centroid: [lng, lat]")
    print("  - centerline_geometry: Center line geometry")
    print("  - zip_code: Zip code")
    print("  - neighborhood: Analysis neighborhood")
    print("  - supervisor_district: Supervisor district")
    print("  - block_id: Block identifier")
    print("  - created_at: Timestamp")
    print("  - updated_at: Timestamp")

if __name__ == "__main__":
    main()