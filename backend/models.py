from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class Schedule(BaseModel):
    beginTime: Optional[str] = None
    endTime: Optional[str] = None
    rate: Optional[str] = None
    rateQualifier: Optional[str] = None
    rateUnit: Optional[str] = None

class Geometry(BaseModel):
    type: str
    coordinates: List[List[float]]

class Blockface(BaseModel):
    id: str
    cnn: Optional[str] = None
    streetName: Optional[str] = None
    fromStreet: Optional[str] = None
    toStreet: Optional[str] = None
    side: Optional[str] = None
    geometry: Geometry
    rules: List[Any] = []
    schedules: List[Schedule] = []

class StreetSegment(BaseModel):
    """
    Represents one side of one CNN street segment.
    Primary key: (cnn, side)
    
    This model provides 100% coverage by using CNN + side as the primary identifier,
    rather than relying on incomplete blockface geometries.
    """
    cnn: str                                    # e.g., "1046000"
    side: str                                   # "L" or "R"
    streetName: str                             # e.g., "20TH ST"
    fromStreet: Optional[str] = None            # From street sweeping limits
    toStreet: Optional[str] = None              # From street sweeping limits
    
    # Address ranges from Active Streets dataset
    # These correspond to the side (L or R) of this segment
    fromAddress: Optional[str] = None           # Starting address (lf_fadd for L, rt_fadd for R)
    toAddress: Optional[str] = None             # Ending address (lf_toadd for L, rt_toadd for R)
    
    # Geometries
    centerlineGeometry: Dict                    # GeoJSON from Active Streets (REQUIRED)
    blockfaceGeometry: Optional[Dict] = None    # GeoJSON from pep9 (OPTIONAL)
    
    # Rules and schedules
    rules: List[Dict] = []                      # Parking regs, sweeping, etc.
    schedules: List[Schedule] = []              # Meter schedules
    
    # Metadata
    zip_code: Optional[str] = None
    layer: Optional[str] = None
    
    # Pre-computed display fields (Optimization)
    displayName: Optional[str] = None               # e.g., "18th Street (North side, 3401-3449)"
    displayNameShort: Optional[str] = None          # e.g., "18th Street (North side)"
    displayAddressRange: Optional[str] = None       # e.g., "3401-3449"
    displayCardinal: Optional[str] = None           # e.g., "North side"
    cardinalDirection: Optional[str] = None         # e.g., "N", "North"

    class Config:
        arbitrary_types_allowed = True

class ErrorReport(BaseModel):
    blockfaceId: str
    description: str