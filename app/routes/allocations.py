from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime, timedelta
from typing import List, Optional
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.config.config import allocations, vehicles
from app.models.allocations import AllocationCreate, AllocationResponse, AllocationStatus, AllocationUpdate

allocation_route = APIRouter()


# Create indexes for frequently queried fields
async def create_indexes():
    await allocations.create_index([("allocation_date", DESCENDING)])
    await allocations.create_index([("vehicle_id", ASCENDING), ("allocation_date", DESCENDING)])
    await allocations.create_index([("status", ASCENDING)])


@allocation_route.post("/allocations/", response_model=AllocationResponse)
async def create_allocation(allocation: AllocationCreate):
    """
    Create a new allocation for a vehicle.

    Args:
        allocation (AllocationCreate): The allocation data to create.

    Returns:
        AllocationResponse: The created allocation.

    Raises:
        HTTPException:
            - 400 if the allocation date is in the past.
            - 400 if the vehicle is already allocated for the given date.
    """
    # Check if allocation date is in the past
    if allocation.allocation_date.date() < datetime.now().date():
        raise HTTPException(
            status_code=400,
            detail="Cannot create allocation for past dates"
        )

    # Check if vehicle is already allocated for the given date
    existing_allocation = await allocations.find_one({
        "vehicle_id": allocation.vehicle_id,
        "allocation_date": allocation.allocation_date,
        "status": {"$ne": "cancelled"}
    })

    if existing_allocation:
        raise HTTPException(
            status_code=401,
            detail="Vehicle is already allocated for this date"
        )

    # Create new allocation
    new_allocation = {
        **allocation.dict(),
        "status": AllocationStatus.ALLOCATED,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = await allocations.insert_one(new_allocation)
    created_allocation = await allocations.find_one({"_id": result.inserted_id})
    created_allocation["id"] = str(created_allocation.pop("_id"))

    return created_allocation


@allocation_route.put("/allocations/{allocation_id}", response_model=AllocationResponse)
async def update_allocation(allocation_id: str, allocation_update: AllocationUpdate):
    """
    Update an existing allocation.

    Args:
        allocation_id (str): The ID of the allocation to update.
        allocation_update (AllocationUpdate): The updated allocation data.

    Returns:
        AllocationResponse: The updated allocation.

    Raises:
        HTTPException: 
            - 404 if the allocation is not found.
            - 400 if trying to update an allocation on or after its allocated date.
    """
    # Find the allocation by ID
    allocation = await allocations.find_one({"_id": ObjectId(allocation_id)})

    # Check if the allocation exists
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    # Check if the allocation date is today or in the past
    if allocation["allocation_date"].date() <= date.today():
        raise HTTPException(
            status_code=400,
            detail="Cannot update on allocated date and after"
        )

    # Prepare update data
    update_data = {
        k: v for k, v in allocation_update.dict(exclude_unset=True).items()
        if v is not None
    }
    update_data["updated_at"] = datetime.now()

    # Update the allocation in the database
    await allocations.update_one(
        {"_id": ObjectId(allocation_id)},
        {"$set": update_data}
    )

    # Retrieve the updated allocation
    updated_allocation = await allocations.find_one(
        {"_id": ObjectId(allocation_id)}
    )
    updated_allocation["id"] = str(updated_allocation.pop("_id"))

    return updated_allocation

@allocation_route.delete("/allocations/{allocation_id}")
async def delete_allocation(allocation_id: str):
    """
    Delete an allocation by its ID.

    Args:
        allocation_id (str): The ID of the allocation to delete.

    Raises:
        HTTPException: 
            - 404 if the allocation is not found.
            - 400 if trying to delete an allocation on or after its allocated date.

    Returns:
        dict: A message confirming successful deletion.
    """
    # Find the allocation by ID
    allocation = await allocations.find_one({"_id": ObjectId(allocation_id)})

    # Check if the allocation exists
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    # Check if the allocation date is today or in the past
    if allocation["allocation_date"] <= datetime.combine(date.today(), datetime.max.time()):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete on allocated date and after"
        )

    # Delete the allocation
    await allocations.delete_one({"_id": ObjectId(allocation_id)})
    
    # Return success message
    return {"message": "Allocation deleted successfully"}


@allocation_route.get("/allocations/", response_model=List[AllocationResponse])
async def get_allocations(
    employee_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    status: Optional[AllocationStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Retrieve a list of allocations based on various filter criteria.

    Args:
        employee_id (Optional[str]): Filter allocations by employee ID.
        vehicle_id (Optional[str]): Filter allocations by vehicle ID.
        status (Optional[AllocationStatus]): Filter allocations by status.
        start_date (Optional[date]): Filter allocations from this date onwards.
        end_date (Optional[date]): Filter allocations up to this date.
        skip (int): Number of records to skip (for pagination).
        limit (int): Maximum number of records to return (for pagination).

    Returns:
        List[AllocationResponse]: A list of allocation objects matching the filter criteria.
    """
    # Initialize an empty query dictionary
    query = {}

    # Add filters to the query based on provided parameters
    if employee_id:
        query["employee_id"] = employee_id
    if vehicle_id:
        query["vehicle_id"] = vehicle_id
    if status:
        query["status"] = status
    if start_date and end_date:
        query["allocation_date"] = {
            "$gte": start_date,
            "$lte": end_date
        }
    elif start_date:
        query["allocation_date"] = {"$gte": datetime.combine(start_date, datetime.min.time())}
    elif end_date:
        query["allocation_date"] = {"$lte": datetime.combine(end_date, datetime.max.time())}

    # Execute the query with pagination and sorting
    cursor = allocations.find(query).skip(
        skip).limit(limit).sort("allocation_date", -1)
    allocation_list = [] 

    # Process each allocation document
    async for allocation in cursor:
        # Convert ObjectId to string for JSON serialization
        allocation["id"] = str(allocation.pop("_id"))
        allocation_list.append(allocation)

    return allocation_list


@allocation_route.get("/allocations/stats")
async def get_allocation_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Retrieve allocation statistics for a given date range.

    Args:
        start_date (Optional[date]): The start date of the range to calculate statistics for.
        end_date (Optional[date]): The end date of the range to calculate statistics for.

    Returns:
        dict: A dictionary containing the total number of allocations and a breakdown by status.
    """
    # Initialize an empty query dictionary
    query = {}
    
    # If both start and end dates are provided, add date range to the query
    if start_date and end_date:
        query["allocation_date"] = {
            "$gte": datetime.combine(start_date, datetime.min.time()),
            "$lte": datetime.combine(end_date, datetime.max.time())
        }

    # Define the aggregation pipeline
    pipeline = [
        # Match documents based on the query (date range if provided)
        {"$match": query},
        # Group documents by status and count occurrences
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]

    # Execute the aggregation pipeline
    stats = await allocations.aggregate(pipeline).to_list(None)
    
    # Prepare and return the response
    return {
        # Calculate total allocations by summing all counts
        "total_allocations": sum(stat["count"] for stat in stats),
        # Create a breakdown of allocations by status
        "status_breakdown": {
            stat["_id"]: stat["count"] for stat in stats
        }
    }


@allocation_route.get("/vehicles/availability/{check_date}")
async def check_vehicle_availability(check_date: date):
    """
    Check the availability of vehicles for a given date.

    This function retrieves all vehicles and determines which ones are available
    for allocation on the specified date.

    Args:
        check_date (date): The date to check for vehicle availability.

    Returns:
        dict: A dictionary containing:
            - date (date): The date checked
            - total_vehicles (int): Total number of vehicles
            - allocated_vehicles (int): Number of allocated vehicles
            - available_vehicles (int): Number of available vehicles
            - vehicles (list): List of available vehicle objects

    Raises:
        HTTPException 500: If there's an error during the process.
    """
    try:
        # Convert date to datetime range for the entire day
        start_datetime = datetime.combine(check_date, datetime.min.time())
        end_datetime = datetime.combine(check_date, datetime.max.time())

        # Get all allocated vehicles for the given date
        pipeline = [
            {
                "$match": {
                    "allocation_date": {
                        "$gte": start_datetime,
                        "$lte": end_datetime
                    },
                    "status": {"$ne": "cancelled"}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "allocated_vehicle_ids": {"$addToSet": "$vehicle_id"}
                }
            }
        ]

        # Execute the aggregation pipeline
        allocated_result = await allocations.aggregate(pipeline).to_list(None)
        allocated_vehicle_ids = set(allocated_result[0]["allocated_vehicle_ids"] if allocated_result else [])

        # Get all vehicles
        all_vehicles = await vehicles.find().to_list(None)
        
        # Process vehicles and add id field
        processed_vehicles = []
        for vehicle in all_vehicles:
            vehicle_id = str(vehicle.pop("_id"))
            vehicle["id"] = vehicle_id
            processed_vehicles.append(vehicle)

        # Filter available vehicles
        available_vehicles = [
            vehicle for vehicle in processed_vehicles
            if vehicle["id"] not in allocated_vehicle_ids
        ]

        return {
            "date": check_date,
            "total_vehicles": len(processed_vehicles),
            "allocated_vehicles": len(allocated_vehicle_ids),
            "available_vehicles": len(available_vehicles),
            "vehicles": available_vehicles
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking vehicle availability: {str(e)}"
        )


@allocation_route.get("/allocations/{allocation_id}", response_model=AllocationResponse)
async def get_allocation(allocation_id: str):
    """
    Retrieve a specific allocation by its ID.

    Args:
        allocation_id (str): The ID of the allocation to retrieve.

    Returns:
        AllocationResponse: The allocation details.

    Raises:
        HTTPException: 
            - 400 if the allocation ID is invalid.
            - 404 if the allocation is not found.
            - 500 for any other server errors.
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(allocation_id):
            raise HTTPException(status_code=400, detail="Invalid allocation ID")

        # Find the allocation
        allocation = await allocations.find_one({"_id": ObjectId(allocation_id)})
        
        if not allocation:
            raise HTTPException(status_code=404, detail="Allocation not found")

        # Convert _id to string id
        allocation["id"] = str(allocation.pop("_id"))
        
        return allocation

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving allocation: {str(e)}"
        )
