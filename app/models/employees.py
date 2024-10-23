from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EmployeeBase(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: str
    name: str
    department: str
    email: str
    created_at: datetime
