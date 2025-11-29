import requests
import json

# Balmy Street is in the Mission district
# Let's search for Balmy Street coordinates
# Balmy Street runs roughly between 24th and Cesar Chavez in the Mission

# Using a point on Balmy Street (approximately mid-block)
# Balmy Street near 24th Street coordinates
lat = 37.7526
lng = -122.4107

print(f"Searching for parking regulations near Balmy Street (lat: {lat}, lng: {lng})")
print("=" * 80)

# Query the API
try:
    response = requests.get(
        f"http://localhost:8000/api/v1/blockfaces?lat={lat}&lng={lng}&radius_meters=200"
    )
    
    if response.status_code == 200:
        blockfaces = response.json()
        if not isinstance(blockfaces, list):
            blockfaces = blockfaces.get('blockfaces', [])
        
        print(f"\nFound {len(blockfaces)} blockface segments near Balmy Street\n")
        
        # Print first segment to see structure
        if blockfaces:
            print("\nFirst segment structure:")
            print(json.dumps(blockfaces[0], indent=2))
            print("\n" + "="*80 + "\n")
        
        # Filter for Balmy Street specifically
        balmy_segments = [bf for bf in blockfaces if bf.get('street_name') and 'balmy' in bf.get('street_name', '').lower()]
        
        if balmy_segments:
            print(f"Found {len(balmy_segments)} segments on Balmy Street:\n")
            
            for i, segment in enumerate(balmy_segments, 1):
                print(f"\n{'='*80}")
                print(f"Segment {i}: {segment.get('street_name', 'Unknown')} - {segment.get('side', 'Unknown')} side")
                print(f"{'='*80}")
                print(f"CNN: {segment.get('cnn')}")
                print(f"From: {segment.get('from_street')} to {segment.get('to_street')}")
                
                # Parking regulations
                regs = segment.get('parking_regulations', [])
                if regs:
                    print(f"\nParking Regulations ({len(regs)} rules):")
                    for j, reg in enumerate(regs, 1):
                        print(f"\n  Rule {j}:")
                        print(f"    Type: {reg.get('regulation_type', 'Unknown')}")
                        if reg.get('time_limit_minutes'):
                            print(f"    Time Limit: {reg.get('time_limit_minutes')} minutes")
                        if reg.get('days_of_week'):
                            print(f"    Days: {reg.get('days_of_week')}")
                        if reg.get('start_time') and reg.get('end_time'):
                            print(f"    Hours: {reg.get('start_time')} - {reg.get('end_time')}")
                        if reg.get('rate_per_hour'):
                            print(f"    Rate: ${reg.get('rate_per_hour')}/hour")
                else:
                    print("\n  No specific parking regulations found")
                
                # Street cleaning
                cleaning = segment.get('street_cleaning', [])
                if cleaning:
                    print(f"\nStreet Cleaning ({len(cleaning)} schedules):")
                    for j, clean in enumerate(cleaning, 1):
                        print(f"\n  Schedule {j}:")
                        print(f"    Week: {clean.get('week_of_month', 'Unknown')}")
                        print(f"    Day: {clean.get('day_of_week', 'Unknown')}")
                        if clean.get('from_hour') and clean.get('to_hour'):
                            print(f"    Hours: {clean.get('from_hour')} - {clean.get('to_hour')}")
                
                # RPP info
                if segment.get('rpp_area'):
                    print(f"\nResidential Permit Parking: Area {segment.get('rpp_area')}")
        else:
            print("No segments found specifically on Balmy Street.")
            print("\nShowing all nearby segments:")
            for bf in blockfaces[:5]:
                print(f"  - {bf.get('street_name')} ({bf.get('side')} side)")
    else:
        print(f"Error: API returned status code {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error querying API: {e}")