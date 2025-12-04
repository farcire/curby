import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
from sodapy import Socrata

async def main():
    load_dotenv()
    
    # Check MongoDB
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("="*80)
    print("DIAGNOSING 20TH STREET CNN MISMATCH")
    print("="*80)
    
    # Get sweeping data from Socrata directly
    print("\n1. Checking SOCRATA street_cleaning_schedules dataset...")
    app_token = os.getenv("SFMTA_APP_TOKEN")
    socrata = Socrata("data.sfgov.org", app_token)
    
    sweeping_data = socrata.get("yhqp-riqs", 
                                 streetname="20TH ST",
                                 limit=1000)
    
    print(f"   Found {len(sweeping_data)} sweeping records")
    
    # Look for our specific block
    print("\n2. Finding records for address range 2800-2899...")
    target_records = []
    for rec in sweeping_data:
        lf_fadd = str(rec.get('lf_fadd', ''))
        lf_toadd = str(rec.get('lf_toadd', ''))
        
        if '28' in lf_fadd or '28' in lf_toadd:
            target_records.append(rec)
            print(f"\n   Record found:")
            print(f"     CNN: {rec.get('cnn')}")
            print(f"     CNNRIGHTLEFT: {rec.get('cnnrightleft')}")
            print(f"     Address: {lf_fadd} - {lf_toadd}")
            print(f"     Weekday: {rec.get('weekday')}")
            print(f"     Time: {rec.get('fromhour')} - {rec.get('tohour')}")
            print(f"     Blockside: {rec.get('blockside')}")
            print(f"     Limits: {rec.get('limits')}")
    
    # Check Active Streets dataset
    print("\n3. Checking SOCRATA active_streets dataset...")
    streets_data = socrata.get("3psu-pn9h",
                                cnn="1046000",
                                limit=10)
    
    for street in streets_data:
        print(f"\n   CNN {street.get('cnn')}:")
        print(f"     Street: {street.get('streetname')}")
        print(f"     Left (L):  {street.get('lf_fadd')} - {street.get('lf_toadd')}")
        print(f"     Right (R): {street.get('rt_fadd')} - {street.get('rt_toadd')}")
        print(f"     CNNL: {street.get('cnn_l')}")
        print(f"     CNNR: {street.get('cnn_r')}")
    
    # Check what's in our database
    print("\n4. Checking our street_segments collection...")
    segments = await db.street_segments.find({
        "cnn": "1046000"
    }).to_list(None)
    
    for seg in segments:
        print(f"\n   CNN {seg.get('cnn')} Side {seg.get('side')}:")
        print(f"     Address: {seg.get('fromAddress')} - {seg.get('toAddress')}")
        print(f"     Cardinal: {seg.get('cardinalDirection')}")
        print(f"     Display: {seg.get('displayName')}")
        
        # Check if rules match the sweeping data
        for rule in seg.get('rules', []):
            if rule.get('type') == 'street-sweeping':
                print(f"     Sweeping: {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                print(f"       Blockside from rule: {rule.get('blockside')}")
    
    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    if target_records:
        print("\nFrom Socrata sweeping data:")
        for rec in target_records:
            cnn = rec.get('cnn')
            side = rec.get('cnnrightleft')
            blockside = rec.get('blockside')
            day = rec.get('weekday')
            
            print(f"  CNN {cnn} Side {side} ({blockside}): {day} sweeping")
        
        print("\nFrom our database:")
        for seg in segments:
            side = seg.get('side')
            cardinal = seg.get('cardinalDirection')
            for rule in seg.get('rules', []):
                if rule.get('type') == 'street-sweeping':
                    day = rule.get('day')
                    print(f"  CNN 1046000 Side {side} ({cardinal}): {day} sweeping")
        
        print("\n⚠️  CHECKING FOR MISMATCH:")
        print("  If 'South' side has Thursday sweeping, there's a mismatch!")
        print("  If 'North' side has Tuesday sweeping, there's a mismatch!")
        print("\n  Expected:")
        print("    - South side should have TUESDAY sweeping")
        print("    - North side should have THURSDAY sweeping")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())