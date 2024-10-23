from fastapi import FastAPI
from app.routes.allocations import allocation_route, create_indexes
from app.routes.employees import employee_route
from app.routes.vehicles import vehicle_route 
from app.routes.seed import seed_route


app = FastAPI(title='Vehicle Allocation System')
app.include_router(allocation_route)
app.include_router(employee_route)
app.include_router(vehicle_route)
app.include_router(seed_route)


@app.on_event("startup")
async def startup_event():
    await create_indexes()