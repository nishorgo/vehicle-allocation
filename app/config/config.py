from motor.motor_asyncio import AsyncIOMotorClient

from os import environ
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from environment variables
mongodb_uri = environ.get('MONGODB_URI')

# Create the MongoDB client
client = AsyncIOMotorClient(mongodb_uri)
db = client.vehicle_allocation

allocations = db['allocations']
employees = db['employees']
drivers = db['drivers']
vehicles = db['vehicles']
