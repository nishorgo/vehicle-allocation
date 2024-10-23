import pytest
from datetime import datetime, date, timedelta
from bson import ObjectId
from httpx import AsyncClient
import random

from app.main import app
from app.models.allocations import AllocationStatus
from app.config.config import vehicles, employees, allocations

@pytest.fixture(autouse=True)
async def cleanup_db():
    """Clean up the database after each test"""
    yield
    await vehicles.delete_many({})
    await employees.delete_many({})
    await allocations.delete_many({})

@pytest.fixture
async def test_vehicle():
    """Create a test vehicle"""
    vehicle_data = {
        "make": "Toyota",
        "model": "Camry",
        "year": 2023,
        "registration_number": f"TEST-{random.randint(1000, 9999)}",
        "status": "available"
    }
    result = await vehicles.insert_one(vehicle_data)
    vehicle_data["_id"] = result.inserted_id
    return vehicle_data

@pytest.fixture
async def test_employee():
    """Create a test employee"""
    employee_data = {
        "name": "Test Employee",
        "email": f"test{random.randint(1000, 9999)}@example.com",
        "department": "IT",
        "position": "Engineer"
    }
    result = await employees.insert_one(employee_data)
    employee_data["_id"] = result.inserted_id
    return employee_data

@pytest.mark.asyncio
async def test_complete_allocation_workflow(test_vehicle, test_employee):
    """Test the complete workflow of vehicle allocation"""
    vehicle = await test_vehicle
    employee = await test_employee
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Check vehicle availability
        tomorrow = date.today() + timedelta(days=1)
        response = await ac.get(f"/vehicles/availability/{tomorrow.isoformat()}")
        assert response.status_code == 200
        availability_data = response.json()
        assert availability_data["available_vehicles"] > 0

        # 2. Create allocation
        allocation_payload = {
            "employee_id": str(employee["_id"]),
            "vehicle_id": str(vehicle["_id"]),
            "allocation_date": datetime.combine(tomorrow, datetime.min.time()).isoformat(),
            "purpose": "Integration Test"
        }
        response = await ac.post("/allocations/", json=allocation_payload)
        assert response.status_code == 200
        allocation_data = response.json()
        allocation_id = allocation_data["id"]

        # 3. Verify allocation details
        response = await ac.get(f"/allocations/{allocation_id}")
        assert response.status_code == 200
        allocation_details = response.json()
        assert allocation_details["id"] == allocation_id
        assert allocation_details["employee_id"] == str(employee["_id"])
        assert allocation_details["vehicle_id"] == str(vehicle["_id"])
        assert allocation_details["status"] == AllocationStatus.ALLOCATED.value

        # 4. Check vehicle is no longer available
        response = await ac.get(f"/vehicles/availability/{tomorrow.isoformat()}")
        assert response.status_code == 200
        updated_availability = response.json()
        assert str(vehicle["_id"]) not in [v["id"] for v in updated_availability["vehicles"]]

        # Add test for invalid allocation ID
        response = await ac.get("/allocations/invalid_id")
        assert response.status_code == 400
        assert "Invalid allocation ID" in response.json()["detail"]

        # Add test for non-existent allocation
        response = await ac.get(f"/allocations/{str(ObjectId())}")
        assert response.status_code == 404
        assert "Allocation not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_multiple_allocations_same_vehicle(test_vehicle, test_employee):
    """Test attempting to allocate same vehicle multiple times"""
    # Await the fixtures
    vehicle = await test_vehicle
    employee = await test_employee
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        tomorrow = date.today() + timedelta(days=1)
        allocation_payload = {
            "employee_id": str(employee["_id"]),
            "vehicle_id": str(vehicle["_id"]),
            "allocation_date": datetime.combine(tomorrow, datetime.min.time()).isoformat(),
            "purpose": "First Allocation"
        }

        # First allocation should succeed
        response = await ac.post("/allocations/", json=allocation_payload)
        assert response.status_code == 200

        # Second allocation for same date should fail
        allocation_payload["purpose"] = "Second Allocation"
        response = await ac.post("/allocations/", json=allocation_payload)
        assert response.status_code == 401
        assert "already allocated" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_allocation_date_restrictions(test_vehicle, test_employee):
    """Test date-related restrictions for allocations"""
    # Await the fixtures
    vehicle = await test_vehicle
    employee = await test_employee
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Past date allocation should fail
        yesterday = date.today() - timedelta(days=1)
        past_payload = {
            "employee_id": str(employee["_id"]),
            "vehicle_id": str(vehicle["_id"]),
            "allocation_date": datetime.combine(yesterday, datetime.min.time()).isoformat(),
            "purpose": "Past Allocation"
        }
        response = await ac.post("/allocations/", json=past_payload)
        assert response.status_code == 400
        assert "past dates" in response.json()["detail"].lower()

        # Future date allocation should succeed
        next_week = date.today() + timedelta(days=7)
        future_payload = {
            "employee_id": str(employee["_id"]),
            "vehicle_id": str(vehicle["_id"]),
            "allocation_date": datetime.combine(next_week, datetime.min.time()).isoformat(),
            "purpose": "Future Allocation"
        }
        response = await ac.post("/allocations/", json=future_payload)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_allocation_endpoints(test_vehicle, test_employee):
    """Test getting single allocation details"""
    vehicle = await test_vehicle
    employee = await test_employee
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create an allocation first
        tomorrow = date.today() + timedelta(days=1)
        allocation_payload = {
            "employee_id": str(employee["_id"]),
            "vehicle_id": str(vehicle["_id"]),
            "allocation_date": datetime.combine(tomorrow, datetime.min.time()).isoformat(),
            "purpose": "Test Allocation"
        }
        
        # Create allocation
        create_response = await ac.post("/allocations/", json=allocation_payload)
        assert create_response.status_code == 200
        allocation_id = create_response.json()["id"]

        # Test successful retrieval
        response = await ac.get(f"/allocations/{allocation_id}")
        assert response.status_code == 200
        allocation = response.json()
        assert allocation["id"] == allocation_id
        assert allocation["employee_id"] == str(employee["_id"])
        assert allocation["vehicle_id"] == str(vehicle["_id"])
        assert allocation["purpose"] == "Test Allocation"
        assert allocation["status"] == AllocationStatus.ALLOCATED.value

        # Test invalid ID format
        response = await ac.get("/allocations/invalid_id")
        assert response.status_code == 400
        assert "Invalid allocation ID" in response.json()["detail"]

        # Test non-existent ID
        response = await ac.get(f"/allocations/{str(ObjectId())}")
        assert response.status_code == 404
        assert "Allocation not found" in response.json()["detail"]
