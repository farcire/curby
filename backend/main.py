import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import Blockface, ErrorReport

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
        
        # Ensure 2dsphere index on blockfaces
        try:
            await db.blockfaces.create_index([("geometry", "2dsphere")])
            print("Ensured 2dsphere index on blockfaces collection.")
        except Exception as e:
            print(f"Failed to create index: {e}")
            
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

    yield
    
    # Shutdown
    client.close()

app = FastAPI(lifespan=lifespan)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

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

@app.get("/api/v1/blockfaces", response_model=List[Blockface])
async def get_blockfaces(lat: float, lng: float, radius_meters: int = 500):
    """
    Get blockfaces within a radius of a location.
    """
    try:
        # Use $geoWithin with $centerSphere for robust radius search
        # Radius must be in radians (meters / earth_radius_in_meters)
        earth_radius_meters = 6378100
        radius_radians = radius_meters / earth_radius_meters

        query = {
            "geometry": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], radius_radians]
                }
            }
        }
        
        blockfaces = []
        async for doc in db.blockfaces.find(query):
            # Convert ObjectId to string if needed, though our schema uses 'id' as string
            if "_id" in doc:
                del doc["_id"]
            blockfaces.append(doc)
            
        print(f"Found {len(blockfaces)} blockfaces")

        # --- Enrich with Non-Metered Regulations ---
        # Fetch regulations within the same area
        # We use a slightly larger radius to ensure we catch things starting/ending just outside
        reg_query = {
            "geometry": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], radius_radians]
                }
            }
        }
        
        regulations = []
        async for reg in db.parking_regulations.find(reg_query):
            regulations.append(reg)
            
        print(f"Found {len(regulations)} regulations in area")
        
        # Simple spatial matching: Associate regulation with the nearest blockface(s)
        # This is an approximation. Ideally this is done during ingestion with robust spatial joins.
        if blockfaces and regulations:
            from math import radians, cos, sin, asin, sqrt

            def haversine(lon1, lat1, lon2, lat2):
                """
                Calculate the great circle distance between two points
                on the earth (specified in decimal degrees)
                """
                # convert decimal degrees to radians
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                # haversine formula
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371000 # Radius of earth in meters
                return c * r

            def get_centroid(geometry):
                if not geometry or 'coordinates' not in geometry:
                    return None
                coords = geometry['coordinates']
                # Handle MultiLineString
                if geometry['type'] == 'MultiLineString':
                    # Flatten to single list of points
                    all_points = [p for line in coords for p in line]
                    coords = all_points
                
                if not coords:
                    return None
                    
                # Simple average of points
                avg_lng = sum(p[0] for p in coords) / len(coords)
                avg_lat = sum(p[1] for p in coords) / len(coords)
                return [avg_lng, avg_lat]

            # Pre-calculate blockface centroids
            bf_centroids = []
            for bf in blockfaces:
                c = get_centroid(bf.get('geometry'))
                bf_centroids.append({'id': bf.get('id'), 'centroid': c})

            for reg in regulations:
                reg_center = get_centroid(reg.get('geometry'))
                if not reg_center:
                    continue
                
                # Find nearest blockface
                nearest_bf = None
                min_dist = float('inf')
                
                for bf_c in bf_centroids:
                    if not bf_c['centroid']:
                        continue
                    dist = haversine(reg_center[0], reg_center[1], bf_c['centroid'][0], bf_c['centroid'][1])
                    if dist < min_dist:
                        min_dist = dist
                        nearest_bf = bf_c['id']
                
                # If reasonably close (e.g., within 20 meters), attach rule
                if nearest_bf and min_dist < 30:
                    # Find the blockface object
                    target_bf = next((b for b in blockfaces if b['id'] == nearest_bf), None)
                    if target_bf:
                        # Map regulation fields to rule structure
                        rule = {
                            "type": map_regulation_type(reg.get('regulation', '')),
                            "day": reg.get('days', 'Daily'),
                            "startTime": reg.get('hrs_begin', '0'),
                            "endTime": reg.get('hrs_end', '2359'),
                            "description": f"{reg.get('regulation')} ({reg.get('days')} {reg.get('hours')})"
                        }
                        target_bf['rules'].append(rule)

        return blockfaces
    except Exception as e:
        print(f"Error in get_blockfaces: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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