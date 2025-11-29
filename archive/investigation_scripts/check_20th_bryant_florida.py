import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

async def check_20th_street():
    """Check rules for 20th St between Bryant and Florida"""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI not found in .env file.")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db = client["curby"]

    print("\n" + "="*70)
    print("20TH STREET RULES: Bryant to Florida")
    print("="*70)
    
    # Find all 20th St segments
    segments = await db.street_segments.find({"streetName": "20TH ST"}).to_list(None)
    
    print(f"\nFound {len(segments)} total 20th Street segments")
    
    # Find segments between Bryant and Florida
    bryant_florida_segments = []
    for seg in segments:
        from_st = seg.get("fromStreet", "").upper()
        to_st = seg.get("toStreet", "").upper()
        
        # Check if this is between Bryant and Florida
        if ("BRYANT" in from_st or "BRYANT" in to_st) and \
           ("FLORIDA" in from_st or "FLORIDA" in to_st):
            bryant_florida_segments.append(seg)
        # Also check the reverse
        elif ("FLORIDA" in from_st or "FLORIDA" in to_st) and \
             ("BRYANT" in from_st or "BRYANT" in to_st):
            bryant_florida_segments.append(seg)
    
    if not bryant_florida_segments:
        print("\n⚠ No segments found specifically between Bryant and Florida")
        print("Showing all 20th St segments with their limits:\n")
        
        for seg in sorted(segments, key=lambda x: (x.get("cnn"), x.get("side"))):
            print(f"CNN {seg.get('cnn')} ({seg.get('side')}): {seg.get('fromStreet')} → {seg.get('toStreet')}")
            rules = seg.get("rules", [])
            if rules:
                print(f"  Rules: {len(rules)}")
                for rule in rules:
                    print(f"    - {rule.get('type')}: {rule.get('description') or rule.get('regulation')}")
            else:
                print(f"  No rules")
            print()
    else:
        print(f"\n✓ Found {len(bryant_florida_segments)} segment(s) between Bryant and Florida\n")
        
        for seg in sorted(bryant_florida_segments, key=lambda x: x.get("side")):
            side = seg.get("side")
            cnn = seg.get("cnn")
            
            print("="*70)
            print(f"CNN {cnn} - Side {side} (Left side when facing increasing street numbers)")
            print("="*70)
            print(f"Street: {seg.get('streetName')}")
            print(f"From: {seg.get('fromStreet')}")
            print(f"To: {seg.get('toStreet')}")
            print(f"Zip: {seg.get('zip_code')}")
            
            # Geometries
            has_centerline = bool(seg.get("centerlineGeometry"))
            has_blockface = bool(seg.get("blockfaceGeometry"))
            print(f"\nGeometries:")
            print(f"  Centerline: {'✓' if has_centerline else '✗'}")
            print(f"  Blockface: {'✓' if has_blockface else '✗'}")
            
            # Rules
            rules = seg.get("rules", [])
            print(f"\nRules ({len(rules)} total):")
            
            if not rules:
                print("  ⚠ No rules found for this segment")
            else:
                # Group by type
                sweeping = [r for r in rules if r.get("type") == "street-sweeping"]
                parking = [r for r in rules if r.get("type") == "parking-regulation"]
                
                if sweeping:
                    print(f"\n  Street Sweeping ({len(sweeping)}):")
                    for rule in sweeping:
                        print(f"    • {rule.get('day')} {rule.get('startTime')}-{rule.get('endTime')}")
                        if rule.get('limits'):
                            print(f"      Limits: {rule.get('limits')}")
                
                if parking:
                    print(f"\n  Parking Regulations ({len(parking)}):")
                    for rule in parking:
                        print(f"    • {rule.get('regulation')}")
                        if rule.get('days'):
                            print(f"      Days: {rule.get('days')}")
                        if rule.get('hours'):
                            print(f"      Hours: {rule.get('hours')}")
                        if rule.get('timeLimit'):
                            print(f"      Time Limit: {rule.get('timeLimit')} hours")
                        if rule.get('matchConfidence'):
                            print(f"      Confidence: {rule.get('matchConfidence'):.3f}")
            
            # Meter schedules
            schedules = seg.get("schedules", [])
            if schedules:
                print(f"\nMeter Schedules ({len(schedules)}):")
                for sched in schedules[:3]:  # Show first 3
                    print(f"    • {sched.get('beginTime')} - {sched.get('endTime')}: ${sched.get('rate')}")
            
            print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_20th_street())