import requests
import json

# Fetch records WITH cnn_id
base_url = "https://data.sfgov.org/resource/pep9-66vw.json"

print("=" * 80)
print("PEP9-66VW: Records WITH CNN_ID")
print("=" * 80)

params = {
    "$limit": 50,
    "$where": "cnn_id IS NOT NULL"
}

try:
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    records = response.json()
    
    print(f"\nFetched {len(records)} records with cnn_id\n")
    
    # Analyze these records
    with_shape = 0
    without_shape = 0
    with_street_name = 0
    
    for rec in records:
        if rec.get('shape'):
            with_shape += 1
        else:
            without_shape += 1
        
        if rec.get('street_name'):
            with_street_name += 1
    
    print(f"Records with shape: {with_shape}")
    print(f"Records without shape: {without_shape}")
    print(f"Records with street_name: {with_street_name}")
    
    print("\n" + "=" * 80)
    print("Sample records WITH CNN_ID:")
    print("=" * 80)
    
    for i, rec in enumerate(records[:10], 1):
        print(f"\n{i}. GlobalID: {rec.get('globalid')}")
        print(f"   CNN_ID: {rec.get('cnn_id')}")
        print(f"   Street: {rec.get('street_name')}")
        print(f"   From: {rec.get('from_st')} To: {rec.get('to_st')}")
        
        shape = rec.get('shape')
        if shape:
            coords = shape.get('coordinates', [])
            print(f"   Shape: {shape.get('type')} with {len(coords)} points")
            if coords:
                print(f"   Start: [{coords[0][0]:.6f}, {coords[0][1]:.6f}]")
                print(f"   End: [{coords[-1][0]:.6f}, {coords[-1][1]:.6f}]")
        else:
            print(f"   Shape: None")
        
        # Check address ranges
        print(f"   Left side: {rec.get('lf_fadd')} to {rec.get('lf_toadd')}")
        print(f"   Right side: {rec.get('rt_fadd')} to {rec.get('rt_toadd')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()