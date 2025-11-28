import requests
import json

print("=" * 80)
print("BALMY STREET PARKING REGULATIONS - CORRECT API")
print("=" * 80)

cnn = 2699000

# Query the CORRECT non-metered parking regulations dataset
print("\nQuerying Non-Metered Parking Regulations (hi6h-neyh)...")
print("-" * 80)

non_metered_url = f"https://data.sfgov.org/resource/hi6h-neyh.json?cnn={cnn}"
response = requests.get(non_metered_url)

print(f"Request URL: {non_metered_url}")
print(f"Status Code: {response.status_code}\n")

if response.status_code == 200:
    regulations = response.json()
    
    if regulations:
        print(f"Found {len(regulations)} parking regulation(s) for Balmy Street:\n")
        
        for i, reg in enumerate(regulations, 1):
            print(f"{'='*80}")
            print(f"Regulation {i}:")
            print(f"{'='*80}")
            print(f"  CNN: {reg.get('cnn', 'N/A')}")
            print(f"  Street: {reg.get('streetname', 'N/A')}")
            print(f"  From: {reg.get('fromstreet', 'N/A')} to {reg.get('tostreet', 'N/A')}")
            print(f"  Side: {reg.get('side', 'N/A')}")
            
            # Regulation details
            category = reg.get('parkingcategory', 'N/A')
            description = reg.get('parkingdescription', 'N/A')
            
            print(f"\n  Parking Category: {category}")
            print(f"  Description: {description}")
            
            # Time restrictions
            if reg.get('weekday'):
                print(f"  Days: {reg.get('weekday')}")
            if reg.get('fromhour') and reg.get('tohour'):
                print(f"  Hours: {reg.get('fromhour')} - {reg.get('tohour')}")
            if reg.get('timelimit'):
                print(f"  Time Limit: {reg.get('timelimit')}")
            
            # Additional fields
            if reg.get('location'):
                print(f"  Location: {reg.get('location')}")
            
            print("\n" + "-" * 80 + "\n")
    else:
        print("No parking regulations found for CNN 2699000.")
        print("This typically means unrestricted parking (subject to general SF rules).")
else:
    print(f"Error: {response.status_code}")
    print(f"Response: {response.text[:500]}")

# Also search by street name
print("\nSearching by street name 'BALMY'...")
print("-" * 80)

search_url = "https://data.sfgov.org/resource/hi6h-neyh.json"
params = {
    "$where": "upper(streetname) LIKE '%BALMY%'",
    "$limit": 50
}

search_response = requests.get(search_url, params=params)

if search_response.status_code == 200:
    results = search_response.json()
    
    if results:
        print(f"\nFound {len(results)} regulation(s) with 'BALMY' in street name:\n")
        
        for i, reg in enumerate(results, 1):
            print(f"  {i}. {reg.get('streetname')} (CNN: {reg.get('cnn')}) - {reg.get('parkingcategory', 'N/A')}")
    else:
        print("\nNo regulations found with 'BALMY' in street name.")
else:
    print(f"Error: {search_response.status_code}")

print("\n" + "=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)