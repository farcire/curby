import requests
import json

# Query by CNN for Balmy Street
cnn = 2699000

print(f"Querying parking regulations for Balmy Street (CNN: {cnn})")
print("=" * 80)

# Query the API by CNN
try:
    response = requests.get(
        f"http://localhost:8000/api/v1/blockfaces/cnn/{cnn}"
    )
    
    if response.status_code == 200:
        segments = response.json()
        if not isinstance(segments, list):
            segments = [segments]
        
        print(f"\nFound {len(segments)} segment(s) for Balmy Street (CNN {cnn})\n")
        
        for i, segment in enumerate(segments, 1):
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
                    if reg.get('description'):
                        print(f"    Description: {reg.get('description')}")
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
            
            print(f"\n{'='*80}\n")
    else:
        print(f"Error: API returned status code {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error querying API: {e}")
    import traceback
    traceback.print_exc()