import pytest
from datetime import datetime, date, timedelta
from bson import ObjectId
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.models.allocations import AllocationStatus
from app.config.config import allocations

# Event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup():
    yield
    await allocations.delete_many({})

# Base URL fixture
@pytest.fixture
def base_url():
    return "http://test"

@pytest.mark.asyncio
async def test_create_allocation_success(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        future_date = datetime.now() + timedelta(days=1)
        payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": future_date.isoformat(),
            "purpose": "Test Purpose"
        }
        response = await ac.post("/allocations/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == AllocationStatus.ALLOCATED
        assert data["purpose"] == "Test Purpose"

@pytest.mark.asyncio
async def test_create_allocation_past_date(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        past_date = datetime.now() - timedelta(days=1)
        payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": past_date.isoformat(),
            "purpose": "Test Purpose"
        }
        response = await ac.post("/allocations/", json=payload)
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_allocation_success(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # First create an allocation
        future_date = datetime.now() + timedelta(days=2)
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": future_date.isoformat(),
            "purpose": "Original Purpose"
        }
        create_response = await ac.post("/allocations/", json=create_payload)
        allocation_id = create_response.json()["id"]

        # Then update it
        update_payload = {
            "purpose": "Updated Purpose",
            "status": AllocationStatus.CANCELLED
        }
        response = await ac.put(f"/allocations/{allocation_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["purpose"] == "Updated Purpose"
        assert data["status"] == AllocationStatus.CANCELLED

@pytest.mark.asyncio
async def test_delete_allocation_success(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        future_date = datetime.now() + timedelta(days=3)
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": future_date.isoformat(),
            "purpose": "To be deleted"
        }
        create_response = await ac.post("/allocations/", json=create_payload)
        allocation_id = create_response.json()["id"]

        response = await ac.delete(f"/allocations/{allocation_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Allocation deleted successfully"

@pytest.mark.asyncio
async def test_update_allocation_on_allocation_date(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Create an allocation for today
        current_date = datetime.now()
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": current_date.isoformat(),
            "purpose": "Original Purpose"
        }
        
        # First create the allocation
        create_response = await ac.post("/allocations/", json=create_payload)
        assert create_response.status_code == 200
        allocation_id = create_response.json()["id"]

        # Try to update it
        update_payload = {
            "purpose": "Updated Purpose",
            "status": AllocationStatus.CANCELLED.value
        }
        response = await ac.put(f"/allocations/{allocation_id}", json=update_payload)
        
        # Verify that update is not allowed
        assert response.status_code == 400
        assert response.json()["detail"] == "Cannot update on allocated date and after"

@pytest.mark.asyncio
async def test_update_allocation_after_allocation_date(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Create an allocation for yesterday
        past_date = datetime.now() - timedelta(days=1)
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": past_date.isoformat(),
            "purpose": "Original Purpose"
        }
        
        # First create the allocation
        create_response = await ac.post("/allocations/", json=create_payload)
        assert create_response.status_code == 400  # Should fail as it's a past date
        assert "Cannot create allocation for past dates" in create_response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_allocation_on_allocation_date(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Create an allocation for today
        current_date = datetime.now()
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": current_date.isoformat(),
            "purpose": "To be deleted"
        }
        
        # First create the allocation
        create_response = await ac.post("/allocations/", json=create_payload)
        assert create_response.status_code == 200
        allocation_id = create_response.json()["id"]

        # Try to delete it
        response = await ac.delete(f"/allocations/{allocation_id}")
        
        # Verify that deletion is not allowed
        assert response.status_code == 400
        assert response.json()["detail"] == "Cannot delete on allocated date and after"

@pytest.mark.asyncio
async def test_delete_allocation_after_allocation_date(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Create an allocation for yesterday
        past_date = datetime.now() - timedelta(days=1)
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": past_date.isoformat(),
            "purpose": "To be deleted"
        }
        
        # First create the allocation
        create_response = await ac.post("/allocations/", json=create_payload)
        assert create_response.status_code == 400  # Should fail as it's a past date
        assert "Cannot create allocation for past dates" in create_response.json()["detail"]

@pytest.mark.asyncio
async def test_successful_update_before_allocation_date(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Create an allocation for future
        future_date = datetime.now() + timedelta(days=2)
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": future_date.isoformat(),
            "purpose": "Original Purpose"
        }
        
        # First create the allocation
        create_response = await ac.post("/allocations/", json=create_payload)
        assert create_response.status_code == 200
        allocation_id = create_response.json()["id"]

        # Try to update it
        update_payload = {
            "purpose": "Updated Purpose",
            "status": AllocationStatus.CANCELLED.value
        }
        response = await ac.put(f"/allocations/{allocation_id}", json=update_payload)
        
        # Verify that update is allowed
        assert response.status_code == 200
        updated_data = response.json()
        assert updated_data["purpose"] == "Updated Purpose"
        assert updated_data["status"] == AllocationStatus.CANCELLED.value

@pytest.mark.asyncio
async def test_successful_delete_before_allocation_date(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Create an allocation for future
        future_date = datetime.now() + timedelta(days=2)
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": future_date.isoformat(),
            "purpose": "To be deleted"
        }
        
        # First create the allocation
        create_response = await ac.post("/allocations/", json=create_payload)
        assert create_response.status_code == 200
        allocation_id = create_response.json()["id"]

        # Try to delete it
        response = await ac.delete(f"/allocations/{allocation_id}")
        
        # Verify that deletion is allowed
        assert response.status_code == 200
        assert response.json()["message"] == "Allocation deleted successfully"


@pytest.mark.asyncio
async def test_get_allocation_stats(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        future_date = datetime.now() + timedelta(days=1)
        create_payload = {
            "employee_id": str(ObjectId()),
            "vehicle_id": str(ObjectId()),
            "allocation_date": future_date.isoformat(),
            "purpose": "Test Purpose"
        }
        await ac.post("/allocations/", json=create_payload)

        params = {
            "start_date": future_date.date().isoformat(),
            "end_date": (future_date + timedelta(days=1)).date().isoformat()
        }
        response = await ac.get("/allocations/stats", params=params)
        assert response.status_code == 200
        data = response.json()
        assert "total_allocations" in data
        assert "status_breakdown" in data
        assert data["total_allocations"] > 0