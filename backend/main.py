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