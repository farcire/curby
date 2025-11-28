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

class ErrorReport(BaseModel):
    blockfaceId: str
    description: str