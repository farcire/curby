import requests
import json

# Query for 18th Street area
lat = 37.7604
lng = -122.4087

print("Querying 18th Street area...")
response = requests.get(f"http://localhost:8000/api/v1/blockfaces?lat={lat}&lng={lng}&radius_meters=200")

if response.status_code == 200:
    data = response.json()
    
    print(f"Found {len(data)} total segments")
    
    # Find ANY 18th Street L segment
    for segment in data:
        if "18TH" in segment.get("streetName", "").upper() and segment.get("side") == "L":
                print("=" * 80)
                print(f"Found: {segment.get('streetName')} - Side {segment.get('side')}")
                print("=" * 80)
                print(f"From: {segment.get('fromStreet')} → To: {segment.get('toStreet')}")
                print(f"CNN: {segment.get('cnn')}")
                
                # Check for address range in the raw data
                print(f"\n📍 Checking for address/cardinal data in segment...")
                
                # Look at rules for cardinal direction
                rules = segment.get('rules', [])
                print(f"\n📋 Rules ({len(rules)} total):")
                
                for i, rule in enumerate(rules, 1):
                    print(f"\n  Rule {i}:")
                    print(f"    Type: {rule.get('type')}")
                    print(f"    Description: {rule.get('description', 'N/A')}")
                    
                    # Check for cardinal direction
                    if 'cardinalDirection' in rule:
                        print(f"    ✅ Cardinal Direction: {rule.get('cardinalDirection')}")
                    
                    # Print all keys to see what's available
                    print(f"    Available fields: {list(rule.keys())}")
                
                print("\n" + "=" * 80)
                print("ANALYSIS:")
                print("=" * 80)
                
                # Check if any rule has cardinal direction
                cardinal_dirs = [r.get('cardinalDirection') for r in rules if r.get('cardinalDirection')]
                if cardinal_dirs:
                    print(f"✅ Cardinal Direction found: {cardinal_dirs[0]}")
                    print(f"💡 L (Left) side = {cardinal_dirs[0]} side")
                    print(f"💡 Should display as: '18TH ST ({cardinal_dirs[0]} side)' or '18TH ST (L/{cardinal_dirs[0]})'")
                else:
                    print("⚠️  No cardinal direction found in rules")
                
                break
else:
    print(f"Error: {response.status_code}")