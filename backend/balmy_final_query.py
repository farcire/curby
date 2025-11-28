import requests
import json

print("=" * 80)
print("BALMY STREET PARKING REGULATIONS")
print("=" * 80)

# Balmy Street details from Active Streets
cnn = 2699000
street_name = "BALMY ST"
from_street = "24TH ST"
to_street = "25TH ST"

print(f"\nStreet: {street_name}")
print(f"CNN: {cnn}")
print(f"Segment: From {from_street} to {to_street}")
print(f"Address Range: 1-99 (odd, left side), 2-98 (even, right side)")
print("\n" + "=" * 80)

# Query non-metered parking regulations
print("\nQuerying Non-Metered Parking Regulations...")
print("-" * 80)

non_metered_url = f"https://data.sfgov.org/resource/cqh6-v9mp.json?cnn={cnn}"
response = requests.get(non_metered_url)

if response.status_code == 200:
    regulations = response.json()
    
    if regulations:
        print(f"\nFound {len(regulations)} parking regulation(s) for Balmy Street:\n")
        
        for i, reg in enumerate(regulations, 1):
            print(f"Regulation {i}:")
            print(f"  Street: {reg.get('streetname', 'N/A')}")
            print(f"  From: {reg.get('fromstreet', 'N/A')} to {reg.get('tostreet', 'N/A')}")
            print(f"  Side: {reg.get('side', 'N/A')}")
            print(f"  CNN: {reg.get('cnn', 'N/A')}")
            
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
            
            print("\n" + "-" * 80 + "\n")
    else:
        print("\nNo parking regulations found in the non-metered database.")
        print("This typically means:")
        print("  - Parking is allowed without restrictions (except street cleaning)")
        print("  - Or it may be covered by general city-wide regulations")
else:
    print(f"Error querying regulations: {response.status_code}")

# Check for street cleaning
print("\nQuerying Street Cleaning Schedule...")
print("-" * 80)

cleaning_url = f"https://data.sfgov.org/resource/yhqp-riqs.json?cnn={cnn}"
cleaning_response = requests.get(cleaning_url)

if cleaning_response.status_code == 200:
    cleaning_schedules = cleaning_response.json()
    
    if cleaning_schedules:
        print(f"\nFound {len(cleaning_schedules)} street cleaning schedule(s):\n")
        
        for i, schedule in enumerate(cleaning_schedules, 1):
            print(f"Schedule {i}:")
            print(f"  Street: {schedule.get('streetname', 'N/A')}")
            print(f"  Week of Month: {schedule.get('weekofmonth', 'N/A')}")
            print(f"  Day: {schedule.get('corridor', 'N/A')}")
            if schedule.get('fromhour') and schedule.get('tohour'):
                print(f"  Hours: {schedule.get('fromhour')} - {schedule.get('tohour')}")
            print()
    else:
        print("\nNo street cleaning schedules found.")
else:
    print(f"Error querying street cleaning: {cleaning_response.status_code}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nBalmy Street (between 24th and 25th Streets) parking information")
print("has been retrieved from SF Open Data sources.")