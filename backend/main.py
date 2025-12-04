import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import Blockface, ErrorReport, StreetSegment
import httpx
import re

load_dotenv()

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise Exception("MONGODB_URI environment variable not set")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.curby  # Specify the database name

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # The ismaster command is cheap and does not require auth.
        await client.admin.command('ismaster')
        print("Successfully connected to MongoDB.")
        
        # Ensure 2dsphere index on street_segments collection for centerlineGeometry
        try:
            await db.street_segments.create_index([("centerlineGeometry", "2dsphere")])
            print("Ensured 2dsphere index on street_segments.centerlineGeometry.")
        except Exception as e:
            print(f"Failed to create index: {e}")
            
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

    yield
    
    # Shutdown
    client.close()

app = FastAPI(lifespan=lifespan)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthCheckResponse(BaseModel):
    status: str
    db_connection: str

@app.get("/healthz", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify service status and database connectivity.
    """
    db_status = "failed"
    try:
        await client.admin.command('ping')
        db_status = "successful"
    except Exception as e:
        print(f"Database ping failed: {e}")
        # The endpoint will still return a 200, but with db_connection: "failed"
    
    if db_status == "failed":
        raise HTTPException(status_code=503, detail={"status": "ok", "db_connection": db_status})

    return {"status": "ok", "db_connection": db_status}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Curby API"}

def map_regulation_type(reg_type: str) -> str:
    reg_type = reg_type.lower()
    if 'sweeping' in reg_type or 'cleaning' in reg_type:
        return 'street-sweeping'
    if 'tow' in reg_type:
        return 'tow-away'
    if 'no parking' in reg_type:
        return 'no-parking'
    if 'time' in reg_type or 'limit' in reg_type:
        return 'time-limit'
    if 'permit' in reg_type or 'residential' in reg_type:
        return 'rpp-zone'
    return 'unknown'

@app.get("/api/v1/blockfaces", response_model=List[dict])
async def get_blockfaces(lat: float, lng: float, radius_meters: int = 500):
    """
    Get street segments (formerly blockfaces) within a radius of a location.
    Maps new StreetSegment model to the legacy Blockface response structure for frontend compatibility.
    """
    try:
        # Use $geoWithin with $centerSphere for robust radius search
        # Radius must be in radians (meters / earth_radius_in_meters)
        earth_radius_meters = 6378100
        radius_radians = radius_meters / earth_radius_meters

        # Query street_segments using centerlineGeometry field (100% coverage)
        # Note: centerlineGeometry is always present from Active Streets (Layer 1)
        # while blockfaceGeometry is only present ~50-60% of the time
        query = {
            "centerlineGeometry": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], radius_radians]
                }
            }
        }
        
        segments = []
        async for doc in db.street_segments.find(query):
            # Create composite ID in format CNN_SIDE (e.g., "797000_L")
            # This is required for frontend map overlays to work correctly
            cnn = doc.get("cnn", "")
            side = doc.get("side", "")
            composite_id = f"{cnn}_{side}" if cnn and side else str(doc.get("_id", ""))
            doc["id"] = composite_id
            if "_id" in doc:
                del doc["_id"]
            
            # Map to frontend expected structure
            # Use blockfaceGeometry if available, otherwise fallback to centerlineGeometry
            geometry = doc.get("blockfaceGeometry") or doc.get("centerlineGeometry")
            
            # Pre-computed display fields from ingestion
            # These are now stored directly on the document
            
            # Construct a response object compatible with frontend Blockface interface
            segment_response = {
                "id": doc["id"],
                "cnn": doc.get("cnn"),
                "street_name": doc.get("streetName"),
                "streetName": doc.get("streetName"),
                "side": doc.get("side"), # "L" or "R"
                "geometry": geometry,
                
                # Display messages (Pre-computed)
                "display_name": doc.get("displayName"),
                "display_name_short": doc.get("displayNameShort"),
                "display_address_range": doc.get("displayAddressRange"),
                "display_cardinal": doc.get("displayCardinal"),
                
                # Rules now contain pre-computed descriptions and parsed logic
                "rules": doc.get("rules", []),
                "restrictions": doc.get("rules", []),  # Map rules to restrictions for frontend compat
                
                "schedules": doc.get("schedules", []),
                "from_street": doc.get("fromStreet"),
                "fromStreet": doc.get("fromStreet"),
                "to_street": doc.get("toStreet"),
                "toStreet": doc.get("toStreet"),
                "fromAddress": doc.get("fromAddress"),
                "toAddress": doc.get("toAddress"),
                "cardinalDirection": doc.get("cardinalDirection")
            }
            
            segments.append(segment_response)
            
        print(f"Found {len(segments)} segments")
        
        # Note: Regulations are already attached during ingestion phase!
        # No need for runtime spatial joining anymore.
        
        return segments
    except Exception as e:
        print(f"Error in get_blockfaces: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/search")
async def search_address(q: str, limit: int = 10):
    """
    Search for addresses, intersections, and businesses.
    Supports:
    - Street names: "Mission St"
    - Addresses: "2125 Bryant St"
    - Intersections: "Bryant and 20th" or "20th and Bryant"
    - Business names: "Tartine Manufactory" (via Nominatim)
    """
    if not q or len(q) < 2:
        return []
    
    query_lower = q.lower().strip()
    results = []
    seen_ids = set()
    
    # Check for intersection pattern: "street1 and street2" or "street1 & street2"
    intersection_pattern = r'(.+?)\s+(?:and|&)\s+(.+)'
    intersection_match = re.match(intersection_pattern, query_lower, re.IGNORECASE)
    
    if intersection_match:
        street1 = intersection_match.group(1).strip()
        street2 = intersection_match.group(2).strip()
        
        # Find segments for both streets
        segments1 = await db.street_segments.find({
            "streetName": {"$regex": f"^{street1}", "$options": "i"}
        }).limit(5).to_list(None)
        
        segments2 = await db.street_segments.find({
            "streetName": {"$regex": f"^{street2}", "$options": "i"}
        }).limit(5).to_list(None)
        
        # Find intersections by checking if segments share fromStreet or toStreet
        for seg1 in segments1:
            for seg2 in segments2:
                # Safely get street names with default empty strings
                seg1_from = (seg1.get('fromStreet') or '').lower()
                seg1_to = (seg1.get('toStreet') or '').lower()
                seg1_name = (seg1.get('streetName') or '').lower()
                seg2_from = (seg2.get('fromStreet') or '').lower()
                seg2_to = (seg2.get('toStreet') or '').lower()
                seg2_name = (seg2.get('streetName') or '').lower()
                
                # Check if they intersect
                if (seg1_from == seg2_name or seg1_to == seg2_name or
                    seg2_from == seg1_name or seg2_to == seg1_name):
                    
                    # Use seg1's coordinates for the intersection point
                    coords = seg1["centerlineGeometry"]["coordinates"]
                    center_lat = sum(c[1] for c in coords) / len(coords)
                    center_lng = sum(c[0] for c in coords) / len(coords)
                    
                    result_id = f"intersection_{seg1.get('cnn', '')}_{seg2.get('cnn', '')}"
                    if result_id not in seen_ids:
                        seen_ids.add(result_id)
                        results.append({
                            "id": result_id,
                            "name": f"{seg1['streetName']} & {seg2['streetName']}",
                            "displayName": f"{seg1['streetName']} & {seg2['streetName']} (Intersection)",
                            "coordinates": [center_lng, center_lat],
                            "type": "intersection"
                        })
                        break
    
    # Search by address number + street name (e.g., "2125 Bryant St")
    if query_lower[0].isdigit():
        parts = query_lower.split(maxsplit=1)
        if len(parts) == 2:
            number, street = parts
            try:
                addr_num = int(number)
                # Find segments where address is in range
                address_matches = await db.street_segments.find({
                    "streetName": {"$regex": f"^{street}", "$options": "i"},
                    "fromAddress": {"$exists": True},
                    "toAddress": {"$exists": True}
                }).to_list(None)
                
                # Filter by address range
                for match in address_matches:
                    try:
                        from_addr = int(match.get("fromAddress", "0"))
                        to_addr = int(match.get("toAddress", "0"))
                        if from_addr <= addr_num <= to_addr:
                            coords = match["centerlineGeometry"]["coordinates"]
                            center_lat = sum(c[1] for c in coords) / len(coords)
                            center_lng = sum(c[0] for c in coords) / len(coords)
                            
                            result_id = match.get("cnn", "") + "_" + match.get("side", "")
                            if result_id not in seen_ids:
                                seen_ids.add(result_id)
                                results.append({
                                    "id": result_id,
                                    "name": f"{number} {match['streetName']}",
                                    "displayName": f"{number} {match['streetName']} ({match.get('cardinalDirection', match.get('side', ''))} side)",
                                    "coordinates": [center_lng, center_lat],
                                    "type": "address"
                                })
                    except (ValueError, TypeError):
                        continue
            except ValueError:
                pass
    
    # Search by street name if no results yet
    # Group by unique street name and return only one result per street
    if len(results) < limit:
        street_matches = await db.street_segments.find({
            "streetName": {"$regex": f"^{query_lower}", "$options": "i"}
        }).to_list(None)
        
        # Group segments by street name
        streets_by_name = {}
        for match in street_matches:
            street_name = match.get("streetName", "")
            if street_name not in streets_by_name:
                streets_by_name[street_name] = []
            streets_by_name[street_name].append(match)
        
        # For each unique street, calculate the midpoint of all its segments
        for street_name, segments in list(streets_by_name.items())[:limit - len(results)]:
            if street_name in seen_ids:
                continue
            seen_ids.add(street_name)
            
            # Calculate midpoint across all segments for this street
            all_coords = []
            for seg in segments:
                coords = seg["centerlineGeometry"]["coordinates"]
                all_coords.extend(coords)
            
            if all_coords:
                center_lat = sum(c[1] for c in all_coords) / len(all_coords)
                center_lng = sum(c[0] for c in all_coords) / len(all_coords)
                
                results.append({
                    "id": f"street_{street_name.replace(' ', '_')}",
                    "name": street_name,
                    "displayName": f"{street_name}, San Francisco, CA",
                    "coordinates": [center_lng, center_lat],
                    "type": "street"
                })
    
    # If still no results, try Nominatim for business names
    if len(results) == 0:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": f"{q}, San Francisco, CA",
                        "format": "json",
                        "limit": 5,
                        "bounded": 1,
                        "viewbox": "-122.5155,37.8324,-122.3482,37.7034"  # SF bounds
                    },
                    headers={"User-Agent": "Curby/1.0"}
                )
                if response.status_code == 200:
                    nominatim_results = response.json()
                    for item in nominatim_results:
                        lat = float(item["lat"])
                        lon = float(item["lon"])
                        # Verify it's in SF bounds
                        if 37.7034 <= lat <= 37.8324 and -122.5155 <= lon <= -122.3482:
                            # Parse display_name to extract clean address
                            # Format: "Name, Street Number, Street, District, City, County, State, ZIP, Country"
                            display_name = item.get("display_name", "")
                            parts = [p.strip() for p in display_name.split(",")]
                            
                            # Build clean display: "Business Name, Street Address, San Francisco, CA"
                            business_name = item.get("name", q)
                            
                            # Try to find and combine street number + street name
                            street_address = ""
                            if len(parts) >= 3:
                                # parts[1] is usually street number, parts[2] is street name
                                street_number = parts[1] if len(parts) > 1 else ""
                                street_name = parts[2] if len(parts) > 2 else ""
                                
                                # Combine them with a space (not comma)
                                if street_number and street_name:
                                    # Skip if it looks like district, state, zip, or country
                                    if not any(x in street_name.lower() for x in ['district', 'county', 'california', 'united states', '94']):
                                        street_address = f"{street_number} {street_name}"
                            
                            # Build final display string
                            if street_address:
                                clean_display = f"{business_name}, {street_address}, San Francisco, CA"
                            else:
                                clean_display = f"{business_name}, San Francisco, CA"
                            
                            results.append({
                                "id": f"nominatim_{item['place_id']}",
                                "name": business_name,
                                "displayName": clean_display,
                                "coordinates": [lon, lat],
                                "type": "business"
                            })
        except Exception as e:
            print(f"Nominatim search error: {e}")
    
    return results[:limit]

@app.post("/api/v1/error-reports")
async def create_error_report(report: ErrorReport):
    """
    Submit an error report for a blockface.
    """
    try:
        doc = report.dict()
        doc["createdAt"] = datetime.utcnow()
        doc["status"] = "new"
        
        result = await db.error_reports.insert_one(doc)
        
        return {
            "id": str(result.inserted_id),
            "status": "received"
        }
    except Exception as e:
        print(f"Error in create_error_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)