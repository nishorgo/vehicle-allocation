from fastapi import APIRouter
from app.config.config import allocations, employees, drivers, vehicles
from app.models.allocations import AllocationCreate, AllocationStatus
from app.models.employees import EmployeeBase
from app.models.vehicles import DriverBase, VehicleBase
from datetime import date, datetime, timedelta
import random

seed_route = APIRouter()

@seed_route.post("/seed")
async def seed_data():
    """
    Seed the database with initial data for testing and development purposes.
    """
    employee_data = [
        EmployeeBase(name="Dave Smith", email="john@example.com", department="Sales"),
        EmployeeBase(name="Dave Chappelle", email="jane@example.com", department="Marketing"),
        EmployeeBase(name="Boris Johnson", email="bob@example.com", department="IT"),
    ]
    for employee in employee_data:
        await employees.insert_one(employee.dict())

    # Seed Drivers
    driver_data = [
        DriverBase(name="Charlie Manjaro", license_number="DL12345"),
        DriverBase(name="Alex Brown", license_number="DL67890"),
    ]
    for driver in driver_data:
        await drivers.insert_one(driver.dict())

    # Seed Vehicles
    vehicle_data = [
        VehicleBase(make="Toyota", model="Camry", year=2020, license_plate="ABC123", driver_id=str((await drivers.find_one())["_id"])),
        VehicleBase(make="Honda", model="Civic", year=2021, license_plate="XYZ789", driver_id=str((await drivers.find().skip(1).limit(1).next())["_id"])),
    ]
    for vehicle in vehicle_data:
        await vehicles.insert_one(vehicle.dict())

    
    allocation_data = [
        AllocationCreate(
            employee_id=str((await employees.find_one())["_id"]),
            vehicle_id=str((await vehicles.find_one())["_id"]),
            allocation_date = datetime.combine(date.today() + timedelta(days=1), datetime.min.time()),
            purpose="Business Trip"
        ),
        AllocationCreate(
            employee_id=str((await employees.find().skip(1).limit(1).next())["_id"]),
            vehicle_id=str((await vehicles.find().skip(1).limit(1).next())["_id"]),
            allocation_date = datetime.combine(date.today() + timedelta(days=2), datetime.min.time()),
            purpose="Client Meeting"
        ),
    ]
    for allocation in allocation_data:
        new_allocation = {
            **allocation.dict(),
            "status": AllocationStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        await allocations.insert_one(new_allocation)

    return {"message": "Data seeded successfully"}
