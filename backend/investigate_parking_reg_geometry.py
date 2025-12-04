import asyncio
import os
from dotenv import load_dotenv
import motor.motor_asyncio
from shapely.geometry import shape
from sodapy import Socrata

async def main():
    load_dotenv()
    
    print("="*80)
    print("INVESTIGATING PARKING REGULATION GEOMETRY MATCHING")
    print("CNN 1046000 - 20th Street 2801-2899")
    print("="*80)
    
    # Get Socrata data
    app_token = os.getenv("SFMTA_APP_TOKEN")
    socrata = Socrata("data.sfgov.org", app_token)
    
    # Get parking regulations for 20th St
    print("\n1. Fetching parking regulations for 20TH ST from Socrata...")
    regs = socrata.get("hi6h-neyh", streetname="20TH ST", limit=500)
    print(f"   Found {len(regs)} regulations")
    
    # Get CNN 1046000 centerline
    print("\n2. Fetching CNN 1046000 centerline from Socrata...")
    streets = socrata.get("3psu-pn9h", cnn="1046000", limit=10)
    
    if not streets:
        print("   ERROR: Could not find CNN 1046000")
        return
    
    centerline_geo = streets[0].get('line')
    if not centerline_geo:
        print("   ERROR: No geometry for CNN 1046000")
        return
    
    centerline = shape(centerline_geo)
    print(f"   Centerline: {len(centerline.coords)} points")
    print(f"   Start: {list(centerline.coords)[0]}")
    print(f"   End: {list(centerline.coords)[-1]}")
    
    # Analyze each regulation
    print("\n3. Analyzing regulations near CNN 1046000...")
    print("-" * 80)
    
    nearby_regs = []
    for reg in regs:
        reg_geo = reg.get('shape')
        if not reg_geo:
            continue
        
        try:
            reg_line = shape(reg_geo)
            distance = reg_line.distance(centerline)
            
            # Within ~50 meters (0.0005 degrees)
            if distance < 0.0005:
                nearby_regs.append({
                    'regulation': reg.get('regulation'),
                    'days': reg.get('days'),
                    'hours': reg.get('hours'),
                    'hrlimit': reg.get('hrlimit'),
                    'permit': reg.get('rpparea1') or reg.get('rpparea2'),
                    'distance': distance,
                    'geometry': reg_geo
                })
        except Exception as e:
            continue
    
    print(f"\nFound {len(nearby_regs)} regulations within 50m of CNN 1046000:")
    
    for i, reg in enumerate(nearby_regs, 1):
        print(f"\n  Regulation #{i}:")
        print(f"    Type: {reg['regulation']}")
        print(f"    Days: {reg['days']}, Hours: {reg['hours']}")
        print(f"    Time Limit: {reg['hrlimit']} hrs")
        print(f"    Permit Area: {reg['permit']}")
        print(f"    Distance from centerline: {reg['distance']:.6f} degrees (~{reg['distance'] * 111000:.1f}m)")
        
        # Determine which side this regulation is on
        reg_line = shape(reg['geometry'])
        
        # Sample points along regulation line
        sample_positions = [0.25, 0.5, 0.75]
        side_votes = {"L": 0, "R": 0}
        
        for pos in sample_positions:
            reg_point = reg_line.interpolate(pos, normalized=True)
            
            # Project onto centerline
            projected_dist = centerline.project(reg_point)
            projected_point = centerline.interpolate(projected_dist)
            
            # Get tangent vector
            delta = 0.001
            if projected_dist + delta > centerline.length:
                p1 = centerline.interpolate(projected_dist - delta)
                p2 = projected_point
            else:
                p1 = projected_point
                p2 = centerline.interpolate(projected_dist + delta)
            
            # Tangent vector
            tangent = (p2.x - p1.x, p2.y - p1.y)
            
            # Vector to regulation point
            to_reg = (reg_point.x - projected_point.x, 
                     reg_point.y - projected_point.y)
            
            # Cross product
            cross = tangent[0] * to_reg[1] - tangent[1] * to_reg[0]
            
            if cross > 0:
                side_votes["L"] += 1
            elif cross < 0:
                side_votes["R"] += 1
        
        determined_side = "L" if side_votes["L"] > side_votes["R"] else "R"
        print(f"    Determined Side: {determined_side} (votes: L={side_votes['L']}, R={side_votes['R']})")
    
    # Check what's in our database
    print("\n\n4. Checking what's stored in our database...")
    print("-" * 80)
    
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    try:
        db = client.get_default_database()
    except:
        db = client['curby']
    
    segments = await db.street_segments.find({"cnn": "1046000"}).to_list(None)
    
    for seg in segments:
        side = seg.get('side')
        cardinal = seg.get('cardinalDirection')
        parking_rules = [r for r in seg.get('rules', []) if r.get('type') == 'parking-regulation']
        
        print(f"\nCNN 1046000 Side {side} ({cardinal}):")
        print(f"  Parking regulations: {len(parking_rules)}")
        
        for rule in parking_rules:
            print(f"    - {rule.get('regulation')}")
            print(f"      Days: {rule.get('days')}, Time: {rule.get('fromTime')}-{rule.get('toTime')}")
            print(f"      Limit: {rule.get('timeLimit')}hrs, Permit: {rule.get('permitArea')}")
            print(f"      Match Confidence: {rule.get('matchConfidence')}")
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("\nCompare the 'Determined Side' from Socrata analysis")
    print("with what's stored in the database to identify mismatches.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())