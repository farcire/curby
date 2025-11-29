import os
import pandas as pd
from sodapy import Socrata
from dotenv import load_dotenv

# Load environment
load_dotenv()
app_token = os.getenv("SFMTA_APP_TOKEN")

SFMTA_DOMAIN = "data.sfgov.org"
PARKING_REGULATIONS_ID = "hi6h-neyh"

print("Fetching parking regulations dataset...")
client = Socrata(SFMTA_DOMAIN, app_token)
results = client.get(PARKING_REGULATIONS_ID, limit=200000)
df = pd.DataFrame.from_records(results)

print(f"Total records: {len(df)}")
print(f"\nColumns: {list(df.columns)}")

# Check for geometry/shape fields
geometry_field = None
if 'shape' in df.columns:
    geometry_field = 'shape'
elif 'geometry' in df.columns:
    geometry_field = 'geometry'

if geometry_field:
    print(f"\nGeometry field found: '{geometry_field}'")
    
    # Check types
    print(f"\nChecking data types in '{geometry_field}' field...")
    type_counts = {}
    problematic_records = []
    
    for idx, row in df.iterrows():
        geo = row.get(geometry_field)
        geo_type = type(geo).__name__
        
        type_counts[geo_type] = type_counts.get(geo_type, 0) + 1
        
        # Collect ALL problematic records (non-dict types)
        if geo_type != 'dict':
            problematic_records.append({
                'index': idx,
                'objectid': row.get('objectid', 'N/A'),
                'type': geo_type,
                'value': geo,
                'regulation': row.get('regulation', 'N/A'),
                'street': row.get('streetname', 'N/A')
            })
    
    print(f"\nType distribution:")
    for geo_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {geo_type}: {count:,} records ({count/len(df)*100:.1f}%)")
    
    if problematic_records:
        print(f"\n{'='*80}")
        print(f"PROBLEMATIC RECORDS (non-dict geometry):")
        print(f"{'='*80}")
        for i, rec in enumerate(problematic_records, 1):
            print(f"\nRecord {i}:")
            print(f"  Index: {rec['index']}")
            print(f"  ObjectID: {rec['objectid']}")
            print(f"  Type: {rec['type']}")
            print(f"  Value: {rec['value']}")
            print(f"  Regulation: {rec['regulation']}")
            print(f"  Street: {rec['street']}")
            print(f"  Full row keys: {list(df.iloc[rec['index']].keys())}")
    
    # Show a valid record for comparison
    valid_records = [idx for idx, row in df.iterrows() if isinstance(row.get(geometry_field), dict)]
    if valid_records:
        print(f"\n{'='*80}")
        print(f"VALID RECORD (for comparison):")
        print(f"{'='*80}")
        valid_idx = valid_records[0]
        valid_row = df.iloc[valid_idx]
        print(f"  Index: {valid_idx}")
        print(f"  ObjectID: {valid_row.get('objectid', 'N/A')}")
        print(f"  Type: {type(valid_row.get(geometry_field)).__name__}")
        print(f"  Geometry keys: {list(valid_row.get(geometry_field, {}).keys())}")
        print(f"  Regulation: {valid_row.get('regulation', 'N/A')}")
        print(f"  Street: {valid_row.get('streetname', 'N/A')}")
else:
    print("\nNo geometry or shape field found!")
    print(f"Available fields: {list(df.columns)}")

client.close()