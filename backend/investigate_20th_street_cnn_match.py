import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
from sodapy import Socrata

async def investigate():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("INVESTIGATING 20TH STREET SOUTH 2801-2899 CNN MATCHING")
    print("=" * 80)
    
    # First, let's check what's in the street_sweeping_schedules for 20th St
    print("\n--- STREET SWEEPING DATA for 20TH ST ---")
    sweeping = await db.street_cleaning_schedules.find({
        "streetname": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    print(f"Found {len(sweeping)} street sweeping records for 20TH ST")
    
    # Group by CNN and side
    by_cnn_side = {}
    for s in sweeping:
        cnn = s.get('cnn')
        side = s.get('cnnrightleft')
        key = f"{cnn}_{side}"
        if key not in by_cnn_side:
            by_cnn_side[key] = []
        by_cnn_side[key].append(s)
    
    print(f"\nFound {len(by_cnn_side)} unique CNN+Side combinations")
    
    # Look for address range 2801-2899
    print("\n--- SEARCHING FOR ADDRESS RANGE 2801-2899 ---")
    target_found = False
    for key, schedules in by_cnn_side.items():
        for s in schedules:
            lf_fadd = s.get('lf_fadd', '')
            lf_toadd = s.get('lf_toadd', '')
            
            # Check if this matches our target range
            if '2801' in str(lf_fadd) or '2899' in str(lf_toadd):
                target_found = True
                print(f"\n✓ FOUND MATCH:")
                print(f"  CNN: {s.get('cnn')}")
                print(f"  Side: {s.get('cnnrightleft')}")
                print(f"  Street: {s.get('streetname')}")
                print(f"  Address Range: {lf_fadd} - {lf_toadd}")
                print(f"  Day: {s.get('weekday')}")
                print(f"  Time: {s.get('fromhour')} - {s.get('tohour')}")
                print(f"  Limits: {s.get('limits')}")
                print(f"  Blockside: {s.get('blockside')}")
    
    if not target_found:
        print("\n✗ No sweeping schedule found with address range 2801-2899")
    
    # Now check the Active Streets dataset to see what CNNs exist for 20th St
    print("\n--- CHECKING ACTIVE STREETS DATASET ---")
    app_token = os.getenv("SFMTA_APP_TOKEN")
    socrata_client = Socrata("data.sfgov.org", app_token)
    
    streets_data = socrata_client.get("3psu-pn9h", 
                                      streetname="20TH ST",
                                      limit=100)
    
    print(f"\nFound {len(streets_data)} street segments for 20TH ST")
    
    # Check address ranges
    print("\n--- ADDRESS RANGES IN ACTIVE STREETS ---")
    for street in streets_data:
        cnn = street.get('cnn')
        lf_fadd = street.get('lf_fadd', '')
        lf_toadd = street.get('lf_toadd', '')
        rt_fadd = street.get('rt_fadd', '')
        rt_toadd = street.get('rt_toadd', '')
        
        # Check if this segment contains our target range
        if any('28' in str(addr) for addr in [lf_fadd, lf_toadd, rt_fadd, rt_toadd]):
            print(f"\nCNN {cnn}:")
            print(f"  Left side:  {lf_fadd} - {lf_toadd}")
            print(f"  Right side: {rt_fadd} - {rt_toadd}")
    
    # Now check what's in our street_segments collection
    print("\n--- CHECKING STREET_SEGMENTS COLLECTION ---")
    segments = await db.street_segments.find({
        "streetName": {"$regex": "20TH", "$options": "i"}
    }).to_list(None)
    
    print(f"\nFound {len(segments)} segments for 20TH ST in database")
    
    # Look for segments with address range containing 28xx
    print("\n--- SEGMENTS WITH 28XX ADDRESSES ---")
    for seg in segments:
        from_addr = seg.get('fromAddress', '')
        to_addr = seg.get('toAddress', '')
        
        if '28' in str(from_addr) or '28' in str(to_addr):
            print(f"\nCNN {seg.get('cnn')} Side {seg.get('side')}:")
            print(f"  Address Range: {from_addr} - {to_addr}")
            print(f"  Display Name: {seg.get('displayName')}")
            print(f"  Cardinal: {seg.get('cardinalDirection')}")
            print(f"  Rules: {len(seg.get('rules', []))} rules")
            
            # Show the rules
            for rule in seg.get('rules', []):
                if rule.get('type') == 'street-sweeping':
                    print(f"    - Sweeping: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                    print(f"      Blockside: {rule.get('blockside')}")
    
    # Check if there's a mismatch between sweeping data and segments
    print("\n" + "=" * 80)
    print("ANALYSIS: CHECKING FOR CNN MISMATCH")
    print("=" * 80)
    
    # Get the CNN from sweeping data for 2801-2899
    sweeping_cnn = None
    for s in sweeping:
        lf_fadd = str(s.get('lf_fadd', ''))
        lf_toadd = str(s.get('lf_toadd', ''))
        if '2801' in lf_fadd or '2899' in lf_toadd:
            sweeping_cnn = s.get('cnn')
            sweeping_side = s.get('cnnrightleft')
            print(f"\nSweeping data says: CNN {sweeping_cnn} Side {sweeping_side}")
            break
    
    # Get the CNN from Active Streets for 2801-2899
    streets_cnn = None
    for street in streets_data:
        lf_fadd = str(street.get('lf_fadd', ''))
        lf_toadd = str(street.get('lf_toadd', ''))
        rt_fadd = str(street.get('rt_fadd', ''))
        rt_toadd = str(street.get('rt_toadd', ''))
        
        if '2801' in lf_fadd or '2899' in lf_toadd:
            streets_cnn = street.get('cnn')
            print(f"Active Streets says: CNN {streets_cnn} (Left side)")
            break
        elif '2801' in rt_fadd or '2899' in rt_toadd:
            streets_cnn = street.get('cnn')
            print(f"Active Streets says: CNN {streets_cnn} (Right side)")
            break
    
    if sweeping_cnn and streets_cnn:
        if sweeping_cnn != streets_cnn:
            print(f"\n⚠️  MISMATCH DETECTED!")
            print(f"   Sweeping data uses CNN: {sweeping_cnn}")
            print(f"   Active Streets uses CNN: {streets_cnn}")
            print(f"\n   This means the sweeping schedule is being attached to the wrong segment!")
        else:
            print(f"\n✓ CNNs match: {sweeping_cnn}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(investigate())