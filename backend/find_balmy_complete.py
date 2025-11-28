from pymongo import MongoClient
import json
from dotenv import load_dotenv
import os
import requests

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["parking_data"]

cnn = 2699000

print(f"Finding Balmy Street parking regulations (CNN: {cnn})")
print("=" * 80)

# Step 1: Get Active Streets data from SFMTA API for CNN 2699000
print("\nStep 1: Fetching Active Streets data from SFMTA API...")
active_streets_url = f"https://data.sfgov.org/resource/3psu-pn9h.json?cnn={cnn}"
response = requests.get(active_streets_url)

if response.status_code == 200:
    active_streets = response.json()
    print(f"Found {len(active_streets)} active street record(s)")
    
    for record in active_streets:
        print(f"\nActive Streets Record:")
        print(f"  CNN: {record.get('cnn')}")
        print(f"  Street Name: {record.get('street_name')}")
        print(f"  Left From Address: {record.get('lf_fadd')}")
        print(f"  Left To Address: {record.get('lf_toad')}")
        print(f"  Right From Address: {record.get('rt_fadd')}")
        print(f"  Right To Address: {record.get('rt_toad')}")
        print(f"  From Node: {record.get('f_node')}")
        print(f"  To Node: {record.get('t_node')}")
        
        # Get geometry if available
        if 'the_geom' in record:
            print(f"  Geometry: Available")
        
        print("\n" + "-" * 80)
        
        # Step 2: Now search for parking regulations using the address ranges
        print("\nStep 2: Searching for parking regulations...")
        
        # Try to find regulations by CNN in non-metered parking regulations
        print("\nSearching non-metered parking regulations by CNN...")
        non_metered_url = f"https://data.sfgov.org/resource/cqh6-v9mp.json?cnn={cnn}"
        reg_response = requests.get(non_metered_url)
        
        if reg_response.status_code == 200:
            regulations = reg_response.json()
            print(f"Found {len(regulations)} non-metered parking regulation(s)")
            
            for i, reg in enumerate(regulations, 1):
                print(f"\n  Regulation {i}:")
                print(f"    CNN: {reg.get('cnn')}")
                print(f"    Street Name: {reg.get('streetname')}")
                print(f"    From Street: {reg.get('fromstreet')}")
                print(f"    To Street: {reg.get('tostreet')}")
                print(f"    Side: {reg.get('side')}")
                
                # Regulation details
                if reg.get('weekday'):
                    print(f"    Days: {reg.get('weekday')}")
                if reg.get('fromhour') and reg.get('tohour'):
                    print(f"    Hours: {reg.get('fromhour')} - {reg.get('tohour')}")
                if reg.get('timelimit'):
                    print(f"    Time Limit: {reg.get('timelimit')}")
                if reg.get('parkingcategory'):
                    print(f"    Category: {reg.get('parkingcategory')}")
                if reg.get('parkingdescription'):
                    print(f"    Description: {reg.get('parkingdescription')}")
                
                print("    " + "-" * 40)
        else:
            print(f"Error fetching non-metered regulations: {reg_response.status_code}")
        
        # Also check RPP data
        print("\nStep 3: Checking for RPP (Residential Permit Parking)...")
        # Search RPP parcels that might overlap with Balmy Street
        rpp_url = "https://data.sfgov.org/resource/cqh6-v9mp.json?$where=parkingcategory='RPP'"
        rpp_response = requests.get(rpp_url + f" AND cnn={cnn}", params={"$limit": 10})
        
        if rpp_response.status_code == 200:
            rpp_regs = rpp_response.json()
            if rpp_regs:
                print(f"Found {len(rpp_regs)} RPP regulation(s)")
                for rpp in rpp_regs:
                    print(f"  RPP Area: {rpp.get('parkingdescription', 'N/A')}")
            else:
                print("No RPP regulations found for this CNN")
        
else:
    print(f"Error fetching Active Streets data: {response.status_code}")

print("\n" + "=" * 80)
print("\nSummary: Balmy Street Parking Regulations")
print("=" * 80)

client.close()