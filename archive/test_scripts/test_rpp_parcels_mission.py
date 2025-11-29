#!/usr/bin/env python3
"""
Test RPP Parcels dataset for Mission neighborhood
1. List all RPP codes and their regulations
2. Fetch RPP parcels and visualize coverage
"""
import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv
from sodapy import Socrata
import json
from collections import defaultdict

async def analyze_mission_rpp():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    
    print("Starting analysis...")
    
    # Connect to MongoDB
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not set")
        return
    
    print(f"Connecting to MongoDB...")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client.curby
    
    print("="*70)
    print("MISSION NEIGHBORHOOD RPP ANALYSIS")
    print("="*70)
    
    # 1. Get all RPP codes from parking regulations
    print("\n--- STEP 1: RPP Codes from Parking Regulations ---\n")
    
    regulations = await db.parking_regulations.find({
        "analysis_neighborhood": "Mission",
        "$or": [
            {"rpparea1": {"$exists": True, "$ne": None}},
            {"rpparea2": {"$exists": True, "$ne": None}}
        ]
    }).to_list(length=1000)
    
    # Organize by RPP area
    rpp_data = defaultdict(lambda: {
        "regulations": [],
        "cnns": set(),
        "time_limits": set(),
        "days": set(),
        "hours": set()
    })
    
    for reg in regulations:
        for area_field in ["rpparea1", "rpparea2"]:
            area = reg.get(area_field)
            if area:
                rpp_data[area]["cnns"].add(reg.get("cnn"))
                rpp_data[area]["regulations"].append({
                    "regulation": reg.get("regulation"),
                    "time_limit": reg.get("hrlimit"),
                    "days": reg.get("days"),
                    "hours": reg.get("hours")
                })
                if reg.get("hrlimit"):
                    rpp_data[area]["time_limits"].add(f"{reg.get('hrlimit')}hr")
                if reg.get("days"):
                    rpp_data[area]["days"].add(reg.get("days"))
                if reg.get("hours"):
                    rpp_data[area]["hours"].add(reg.get("hours"))
    
    print(f"Found {len(rpp_data)} unique RPP areas in Mission:\n")
    
    for area in sorted(rpp_data.keys()):
        data = rpp_data[area]
        print(f"RPP AREA {area}:")
        print(f"  Street segments: {len(data['cnns'])}")
        print(f"  Time limits: {', '.join(sorted(data['time_limits'])) if data['time_limits'] else 'None'}")
        print(f"  Days: {', '.join(sorted(data['days'])) if data['days'] else 'None'}")
        print(f"  Hours: {', '.join(sorted(data['hours'])) if data['hours'] else 'None'}")
        print()
    
    # 2. Fetch RPP Parcels from Socrata
    print("\n--- STEP 2: Fetching RPP Parcels from Socrata ---\n")
    
    app_token = os.getenv("SFMTA_APP_TOKEN")
    socrata_client = Socrata("data.sfgov.org", app_token)
    
    # Fetch parcels for Mission RPP areas
    mission_rpp_codes = list(rpp_data.keys())
    print(f"Fetching parcels for RPP areas: {', '.join(sorted(mission_rpp_codes))}")
    
    # Build where clause
    where_clause = " OR ".join([f"rppeligib='{code}'" for code in mission_rpp_codes])
    
    try:
        parcels = socrata_client.get(
            "i886-hxz9",
            where=where_clause,
            limit=5000
        )
        
        print(f"\nFetched {len(parcels)} parcels\n")
        
        # Organize parcels by RPP area
        parcels_by_area = defaultdict(list)
        for parcel in parcels:
            area = parcel.get("rppeligib")
            if area:
                parcels_by_area[area].append(parcel)
        
        print("Parcel counts by RPP area:")
        for area in sorted(parcels_by_area.keys()):
            print(f"  Area {area}: {len(parcels_by_area[area])} parcels")
        
        # 3. Save data for visualization
        print("\n--- STEP 3: Saving Data for Visualization ---\n")
        
        # Save summary
        summary = {
            "rpp_areas": {},
            "total_parcels": len(parcels),
            "total_street_segments": sum(len(data["cnns"]) for data in rpp_data.values())
        }
        
        for area in sorted(rpp_data.keys()):
            summary["rpp_areas"][area] = {
                "street_segments": len(rpp_data[area]["cnns"]),
                "parcels": len(parcels_by_area.get(area, [])),
                "time_limits": list(rpp_data[area]["time_limits"]),
                "days": list(rpp_data[area]["days"]),
                "hours": list(rpp_data[area]["hours"])
            }
        
        with open("mission_rpp_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print("✅ Saved mission_rpp_summary.json")
        
        # Save parcel geometries for mapping
        parcel_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for parcel in parcels:
            if parcel.get("shape"):
                feature = {
                    "type": "Feature",
                    "properties": {
                        "rpp_area": parcel.get("rppeligib"),
                        "parcel_id": parcel.get("mapblklot")
                    },
                    "geometry": parcel["shape"]
                }
                parcel_geojson["features"].append(feature)
        
        with open("mission_rpp_parcels.geojson", "w") as f:
            json.dump(parcel_geojson, f)
        
        print("✅ Saved mission_rpp_parcels.geojson")
        print(f"\nTotal features in GeoJSON: {len(parcel_geojson['features'])}")
        
        # 4. Analysis
        print("\n" + "="*70)
        print("ANALYSIS")
        print("="*70)
        
        print("\nCoverage Comparison:")
        for area in sorted(summary["rpp_areas"].keys()):
            data = summary["rpp_areas"][area]
            print(f"\nArea {area}:")
            print(f"  {data['street_segments']} street segments have regulations")
            print(f"  {data['parcels']} parcels exist")
            if data['parcels'] > 0:
                print(f"  ✅ Parcels available for spatial validation")
            else:
                print(f"  ⚠️  No parcels found - may need different area code")
        
    except Exception as e:
        print(f"Error fetching parcels: {e}")
        import traceback
        traceback.print_exc()
    
    socrata_client.close()
    client.close()
    
    print("\n" + "="*70)
    print("Next step: Visualize mission_rpp_parcels.geojson on a map")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(analyze_mission_rpp())