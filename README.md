# Vehicle Allocation System

A FastAPI-based REST API for managing vehicle allocations in an organization. This system allows employees to reserve vehicles for specific dates and manages the allocation lifecycle.

## Features

- Vehicle management (CRUD operations)
- Employee management
- Vehicle allocation system
- Availability checking
- Allocation statistics
- Date-based restrictions
- Input validation
- Error handling

## Tech Stack

- Python 3.12+
- FastAPI
- MongoDB
- Motor (async MongoDB driver)
- pytest for testing
- Docker

## Prerequisites

- Python 3.12 or higher
- MongoDB 4.4 or higher
- Docker
- Heroku CLI

## Local Development

1. Clone the repository:
    ```bash
    git clone https://github.com/nishorgo/vehicle-allocation.git
    cd vehicle-allocation-system
    ```

2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file:
    ```env
    MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/
    DATABASE_NAME=vehicle_allocation
    ```

## Docker Setup

1. Build the Docker image:
    ```bash
    docker build -t vehicle-allocation .
    ```

2. Run with Docker:
    ```bash
    docker run -p 8000:8000 vehicle-allocation
    ```

   Or using Docker Compose:
    ```bash
    docker-compose up --build
    ```

## Running the Application

1. Without Docker:
    ```bash
    uvicorn app.main:app --reload
    ```

2. Access the API documentation:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Vehicles
- `GET /vehicles/` - List all vehicles
- `POST /vehicles/` - Create a vehicle
- `GET /vehicles/availability/{date}` - Check availability

### Allocations
- `GET /allocations/` - List allocations
- `POST /allocations/` - Create allocation
- `GET /allocations/stats` - Get statistics

### Employees
- `GET /employees/` - List employees
- `POST /employees/` - Create employee

## Testing

1. Run all tests:
    ```bash
    pytest -v
    ```

2. Run specific tests:
    ```bash
    pytest tests/test_allocations.py -v
    pytest tests/test_integration.py -v
    ```

3. Run with coverage:
    ```bash
    pytest --cov=app tests/
    ```

## Heroku Deployment

1. Install and login to Heroku:
    ```bash
    # Install Heroku CLI
    curl https://cli-assets.heroku.com/install.sh | sh

    # Login
    heroku login
    ```

2. Create and configure app:
    ```bash
    # Create app
    heroku create vehicle-allocation-app

    # Login to container registry
    heroku container:login

    # Build and push
    heroku container:push web

    # Release
    heroku container:release web
    ```

3. Setup database:
    ```bash
    # Add MongoDB
    heroku addons:create mongolab:sandbox

    # Configure environment
    heroku config:set DATABASE_NAME=vehicle_allocation
    ```

4. Start and monitor:
    ```bash
    # Start application
    heroku ps:scale web=1

    # Monitor logs
    heroku logs --tail
    ```

## Monitoring and Maintenance

1. View application logs:
    ```bash
    # Heroku logs
    heroku logs --tail

    # Container logs
    heroku logs --tail --source container
    ```

2. Database monitoring:
    - Access MongoDB Atlas dashboard
    - Monitor through Heroku add-on dashboard

3. Application shell:
    ```bash
    heroku run bash
    ```

## Troubleshooting

1. Check application status:
    ```bash
    heroku ps
    ```

2. Restart application:
    ```bash
    heroku restart
    ```

3. View build logs:
    ```bash
    heroku builds:output
    ```

## License

This project is licensed under the MIT License.
