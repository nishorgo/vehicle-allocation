from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class AllocationStatus(str, Enum):
    ALLOCATED = "allocated"
    CANCELLED = "cancelled"


class AllocationCreate(BaseModel):
    employee_id: str
    vehicle_id: str
    allocation_date: datetime
    purpose: Optional[str] = None


class AllocationUpdate(BaseModel):
    purpose: Optional[str] = None
    status: Optional[AllocationStatus] = None


class AllocationResponse(BaseModel):
    id: str
    employee_id: str
    vehicle_id: str
    allocation_date: datetime
    purpose: str
    status: AllocationStatus
    created_at: datetime
    updated_at: datetime
