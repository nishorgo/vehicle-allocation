from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VehicleBase(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    registration_number: Optional[str] = None
    driver_id: str

class VehicleResponse(BaseModel):
    id: str
    brand: str
    model: str
    registration_number: str
    driver_id: str
    created_at: datetime


class DriverBase(BaseModel):
    name: Optional[str] = None
    license_number: Optional[str] = None
    contact_number: Optional[str] = None


class DriverResponse(BaseModel):
    id: str
    name: str
    license_number: str
    contact_number: str
    created_at: datetime
