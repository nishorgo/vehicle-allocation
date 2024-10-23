import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_client():
    client = AsyncIOMotorClient('mongodb+srv://nishorgo:nishorgopass123@cluster0.hwwzv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    yield client
    await client.close()