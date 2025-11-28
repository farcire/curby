import requests
import json

print("=" * 80)
print("SEARCHING FOR BALMY STREET IN PARKING REGULATIONS")
print("=" * 80)

# Search for any regulations mentioning "BALMY"
print("\n1. Searching Non-Metered Parking Regulations for 'BALMY'...")
print("-" * 80)

# Use $q parameter for text search
non_metered_url = "https://data.sfgov.org/resource/cqh6-v9mp.json"
params = {
    "$where": "upper(streetname) LIKE '%BALMY%'",
    "$limit": 50
}

response = requests.get(non_metered_url, params=params)

if response.status_code == 200:
    regulations = response.json()
    
    if regulations:
        print(f"\nFound {len(regulations)} regulation(s) mentioning BALMY:\n")
        
        for i, reg in enumerate(regulations, 1):
            print(f"Regulation {i}:")
            print(f"  CNN: {reg.get('cnn', 'N/A')}")
            print(f"  Street: {reg.get('streetname', 'N/A')}")
            print(f"  From: {reg.get('fromstreet', 'N/A')} to {reg.get('tostreet', 'N/A')}")
            print(f"  Side: {reg.get('side', 'N/A')}")
            
            # Regulation details
            category = reg.get('parkingcategory', 'N/A')
            description = reg.get('parkingdescription', 'N/A')
            
            print(f"  Category: {category}")
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
        print("\nNo regulations found with 'BALMY' in street name.")
else:
    print(f"Error: {response.status_code}")
    print(f"Response: {response.text[:500]}")

# Also try searching street cleaning
print("\n2. Searching Street Cleaning Schedules for 'BALMY'...")
print("-" * 80)

cleaning_url = "https://data.sfgov.org/resource/yhqp-riqs.json"
cleaning_params = {
    "$where": "upper(streetname) LIKE '%BALMY%'",
    "$limit": 50
}

cleaning_response = requests.get(cleaning_url, params=cleaning_params)

if cleaning_response.status_code == 200:
    schedules = cleaning_response.json()
    
    if schedules:
        print(f"\nFound {len(schedules)} street cleaning schedule(s):\n")
        
        for i, schedule in enumerate(schedules, 1):
            print(f"Schedule {i}:")
            print(f"  CNN: {schedule.get('cnn', 'N/A')}")
            print(f"  Street: {schedule.get('streetname', 'N/A')}")
            print(f"  Week: {schedule.get('weekofmonth', 'N/A')}")
            print(f"  Day: {schedule.get('corridor', 'N/A')}")
            if schedule.get('fromhour') and schedule.get('tohour'):
                print(f"  Hours: {schedule.get('fromhour')} - {schedule.get('tohour')}")
            print()
    else:
        print("\nNo street cleaning schedules found.")
else:
    print(f"Error: {cleaning_response.status_code}")

print("\n" + "=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)