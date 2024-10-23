from datetime import date, datetime
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.models.vehicles import DriverBase, DriverResponse, VehicleBase, VehicleResponse
from app.config.config import drivers, vehicles

vehicle_route = APIRouter()

@vehicle_route.post("/drivers/", response_model=DriverResponse)
async def create_driver(driver: DriverBase):
    """
    Create a new driver in the database.

    This endpoint creates a new driver entry in the database with the provided information.
    It performs the following steps:
    1. Creates a new driver dictionary with the provided data and current timestamp.
    2. Inserts the new driver into the database.
    3. Retrieves the created driver from the database.
    4. Converts the MongoDB ObjectId to a string for the response.

    Args:
        driver (DriverBase): The driver information to be created.

    Returns:
        DriverResponse: The created driver details.
    """
    # Create new driver
    new_driver = {
        **driver.dict(),
        "created_at": datetime.now()
    }

    result = await drivers.insert_one(new_driver)
    created_driver = await drivers.find_one({"_id": result.inserted_id})
    created_driver["id"] = str(created_driver.pop("_id"))

    return created_driver


@vehicle_route.post("/vehicles/", response_model=VehicleResponse)
async def create_vehicle(vehicle: VehicleBase):
    """
    Create a new vehicle and assign it to a driver.

    This endpoint creates a new vehicle entry in the database and associates it with
    a driver. It performs the following steps:
    1. Checks if the driver is already assigned to another vehicle.
    2. If not, creates a new vehicle entry with the provided information.
    3. Returns the created vehicle details.

    Args:
        vehicle (VehicleBase): The vehicle information to be created.

    Returns:
        VehicleResponse: The created vehicle details.

    Raises:
        HTTPException: If the driver is already assigned to another vehicle.
    """

    # Check if vehicle is already allocated for the given driver_id
    existing_driver = await vehicles.find_one({"driver_id": ObjectId(vehicle.driver_id)})
    if existing_driver:
        raise HTTPException(
            status_code=400,
            detail="Driver is already assigned to another vehicle"
        )
    
    # Create new allocation
    new_vehicle = {
        **vehicle.dict(),
        "created_at": datetime.now(),
    }

    result = await vehicles.insert_one(new_vehicle)
    created_vehicle = await vehicles.find_one({"_id": result.inserted_id})
    created_vehicle["id"] = str(created_vehicle.pop("_id"))

    return created_vehicle

