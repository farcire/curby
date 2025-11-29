import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio

async def find_block():
    load_dotenv()
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    print("=" * 80)
    print("FINDING 20TH STREET BLOCK BETWEEN BRYANT AND FLORIDA")
    print("=" * 80)
    
    # Find intersections involving 20th Street
    print("\n--- INTERSECTIONS WITH 20TH STREET ---")
    intersections_20th = await db.intersections.find({
        "$or": [
            {"street_1": {"$regex": "^20TH", "$options": "i"}},
            {"street_2": {"$regex": "^20TH", "$options": "i"}}
        ]
    }).to_list(None)
    
    print(f"Found {len(intersections_20th)} intersections with 20TH ST")
    
    # Find specific intersections
    bryant_20th = None
    florida_20th = None
    
    for intersection in intersections_20th:
        st1 = intersection.get('street_1', '')
        st2 = intersection.get('street_2', '')
        
        # Check for Bryant & 20th
        if ('BRYANT' in st1.upper() and '20TH' in st2.upper()) or \
           ('20TH' in st1.upper() and 'BRYANT' in st2.upper()):
            bryant_20th = intersection
            print(f"\nFound Bryant & 20th:")
            print(f"  Intersection ID: {intersection.get('int_id')}")
            print(f"  Streets: {st1} & {st2}")
            print(f"  CNN List: {intersection.get('cnn_list')}")
        
        # Check for Florida & 20th
        if ('FLORIDA' in st1.upper() and '20TH' in st2.upper()) or \
           ('20TH' in st1.upper() and 'FLORIDA' in st2.upper()):
            florida_20th = intersection
            print(f"\nFound Florida & 20th:")
            print(f"  Intersection ID: {intersection.get('int_id')}")
            print(f"  Streets: {st1} & {st2}")
            print(f"  CNN List: {intersection.get('cnn_list')}")
    
    # Use intersection permutations to find the connecting CNN
    print("\n" + "=" * 80)
    print("FINDING CONNECTING CNN SEGMENT")
    print("=" * 80)
    
    if bryant_20th and florida_20th:
        bryant_int_id = bryant_20th.get('int_id')
        florida_int_id = florida_20th.get('int_id')
        
        print(f"\nLooking for CNN connecting:")
        print(f"  Bryant & 20th (int_id: {bryant_int_id})")
        print(f"  Florida & 20th (int_id: {florida_int_id})")
        
        # Find intersection permutations for both intersections
        bryant_perms = await db.intersection_permutations.find({
            "int_id": bryant_int_id
        }).to_list(None)
        
        florida_perms = await db.intersection_permutations.find({
            "int_id": florida_int_id
        }).to_list(None)
        
        print(f"\nBryant intersection permutations: {len(bryant_perms)}")
        print(f"Florida intersection permutations: {len(florida_perms)}")
        
        # Find common CNNs that involve 20th Street
        bryant_cnns_20th = set()
        florida_cnns_20th = set()
        
        for perm in bryant_perms:
            if '20TH' in perm.get('street_name', '').upper():
                cnn = perm.get('cnn')
                if cnn:
                    bryant_cnns_20th.add(cnn)
                    print(f"  Bryant side - CNN: {cnn}, Street: {perm.get('street_name')}")
        
        for perm in florida_perms:
            if '20TH' in perm.get('street_name', '').upper():
                cnn = perm.get('cnn')
                if cnn:
                    florida_cnns_20th.add(cnn)
                    print(f"  Florida side - CNN: {cnn}, Street: {perm.get('street_name')}")
        
        # Find CNN that connects both intersections
        common_cnns = bryant_cnns_20th & florida_cnns_20th
        
        if common_cnns:
            print(f"\n✓ FOUND CONNECTING CNN(s): {common_cnns}")
            
            for cnn in common_cnns:
                print(f"\n--- CNN {cnn} DETAILS ---")
                
                # Get street info
                street = await db.streets.find_one({"cnn": cnn})
                if street:
                    print(f"Street: {street.get('streetname')}")
                    print(f"From: {street.get('st_name')} to {street.get('st_name_to')}")
                    print(f"Zip: {street.get('zip_code')}")
                    print(f"Layer: {street.get('layer')}")
                
                # Check if we have blockfaces for this CNN
                blockfaces = await db.blockfaces.find({"cnn": cnn}).to_list(None)
                print(f"\nBlockfaces in database: {len(blockfaces)}")
                
                if blockfaces:
                    for bf in blockfaces:
                        print(f"\n  Blockface Side {bf.get('side')}:")
                        rules = bf.get('rules', [])
                        print(f"    Rules: {len(rules)} total")
                        for rule in rules:
                            rtype = rule.get('type')
                            if rtype == 'street-sweeping':
                                print(f"      - {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                            elif rtype == 'parking-regulation':
                                print(f"      - {rule.get('regulation')}: {rule.get('days')} {rule.get('hours')}")
                else:
                    print("    ⚠️  NO BLOCKFACES FOUND FOR THIS CNN!")
                    print("    This CNN may not be in our filtered dataset (zip 94110/94103)")
                
                # Check street sweeping for this CNN
                sweeping = await db.street_cleaning_schedules.find({"cnn": cnn}).to_list(None)
                print(f"\n  Street cleaning schedules: {len(sweeping)}")
                for s in sweeping:
                    print(f"    - {s.get('weekday')} {s.get('fromhour')}-{s.get('tohour')} (Side: {s.get('cnnrightleft')})")
                
                # Check parking regulations nearby
                print(f"\n  Checking parking regulations near this location...")
                # This would require spatial query which is complex
        else:
            print("\n❌ NO COMMON CNN FOUND")
            print("The block between Bryant and Florida may not be properly connected in the data")
    else:
        print("\n❌ Could not find both intersections")
        if not bryant_20th:
            print("  Missing: Bryant & 20th intersection")
        if not florida_20th:
            print("  Missing: Florida & 20th intersection")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nExpected (visually verified):")
    print("  North side (Left): No parking Thursday 9am-11am")
    print("  South side (Right): No parking Tuesday 9am-11am + 1hr parking 8am-6pm M-F")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(find_block())