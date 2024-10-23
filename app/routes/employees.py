from datetime import date, datetime
from fastapi import APIRouter, HTTPException
from app.models.employees import EmployeeBase, EmployeeResponse
from app.config.config import employees

employee_route = APIRouter()

@employee_route.post("/employees/", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeBase):
    """
    Create a new employee.

    This endpoint creates a new employee record in the database.

    Args:
        employee (EmployeeBase): The employee data to be created.

    Returns:
        EmployeeResponse: The created employee record.

    Raises:
        HTTPException: If there's an error during the creation process.
    """
    # Create new employee record
    new_employee = {
        **employee.dict(),
        "created_at": datetime.now()
    }

    # Insert the new employee into the database
    result = await employees.insert_one(new_employee)

    # Retrieve the created employee
    created_employee = await employees.find_one({"_id": result.inserted_id})

    # Convert the MongoDB _id to a string id
    created_employee["id"] = str(created_employee.pop("_id"))

    return created_employee