import requests
import json

# York St near 18th/Mariposa coordinates
LAT = 37.76272
LNG = -122.4092
RADIUS = 300

url = f"http://localhost:8000/api/v1/blockfaces?lat={LAT}&lng={LNG}&radius_meters={RADIUS}"

def simulate_toast_display(segment):
    """Simulates the frontend toast/detail view display."""
    cardinal = segment.get('cardinalDirection')
    side = segment.get('side')
    from_addr = segment.get('fromAddress')
    to_addr = segment.get('toAddress')
    street_name = segment.get('streetName')
    
    # Logic from BlockfaceDetail.tsx:
    # ({blockface.cardinalDirection || blockface.side}
    # {blockface.fromAddress && blockface.toAddress ? `, ${blockface.fromAddress}-${blockface.toAddress}` : ''})
    
    side_text = cardinal if cardinal else side
    
    addr_text = ""
    if from_addr and to_addr:
        addr_text = f", {from_addr}-{to_addr}"
        
    display_string = f"{street_name} ({side_text}{addr_text})"
    
    print("\n" + "="*40)
    print(" TOAST SIMULATION")
    print("="*40)
    print(display_string)
    print("="*40 + "\n")
    return display_string

try:
    print(f"Querying API: {url}")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    target_cnn = "13766000"
    found = False
    
    for segment in data:
        if str(segment.get('cnn')) == target_cnn and segment.get('side') == 'L':
            found = True
            print(f"Found Segment: CNN {segment.get('cnn')} Side {segment.get('side')}")
            print(f"Data - Cardinal: {segment.get('cardinalDirection')}, Address: {segment.get('fromAddress')}-{segment.get('toAddress')}")
            simulate_toast_display(segment)
            break
            
    if not found:
        print(f"CNN {target_cnn} (L) not found in API response.")
        
except Exception as e:
    print(f"Error: {e}")