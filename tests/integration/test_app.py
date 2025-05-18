import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from product_evaluator.main import app
from product_evaluator.utils.database import Base, get_db
from product_evaluator.models.user.user_model import User


# Create a test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    
    # Create a test client using the FastAPI app
    with TestClient(app) as client:
        yield client
    
    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(client):
    """Create a test user and return the user data."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    
    # Create the user
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Return the user data with password for login tests
    return user_data


@pytest.fixture
def test_token(client, test_user):
    """Get an access token for the test user."""
    response = client.post(
        "/api/auth/token",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def authenticated_client(client, test_token):
    """Create a client with the Authorization header set."""
    client.headers = {
        "Authorization": f"Bearer {test_token}"
    }
    return client


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


def test_user_registration(client):
    """Test user registration."""
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
        "full_name": "New User"
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "password" not in data


def test_user_login(client, test_user):
    """Test user login."""
    response = client.post(
        "/api/auth/token",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data


def test_get_current_user(authenticated_client):
    """Test getting the current user's info."""
    response = authenticated_client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_update_user_password(authenticated_client):
    """Test updating user password."""
    password_data = {
        "current_password": "password123",
        "new_password": "newpassword123"
    }
    response = authenticated_client.put("/api/users/me/password", json=password_data)
    assert response.status_code == 200
    
    # Try logging in with the new password
    response = authenticated_client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "newpassword123"}
    )
    assert response.status_code == 200


def test_create_product(authenticated_client):
    """Test creating a product."""
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "website_url": "https://example.com",
        "category": "Development Tool",
        "vendor": "Test Vendor",
        "extract_content": False
    }
    response = authenticated_client.post("/api/products", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["description"] == product_data["description"]
    assert "id" in data
    assert "created_at" in data
    
    # Return the product ID for other tests
    return data["id"]


def test_get_products(authenticated_client, test_token):
    """Test getting products."""
    # Create a product first
    product_id = test_create_product(authenticated_client)
    
    # Get products
    response = authenticated_client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["id"] == product_id


def test_get_product(authenticated_client):
    """Test getting a specific product."""
    # Create a product first
    product_id = test_create_product(authenticated_client)
    
    # Get the product
    response = authenticated_client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == "Test Product"


def test_update_product(authenticated_client):
    """Test updating a product."""
    # Create a product first
    product_id = test_create_product(authenticated_client)
    
    # Update the product
    update_data = {
        "name": "Updated Product",
        "description": "This is an updated product description"
    }
    response = authenticated_client.put(f"/api/products/{product_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


def test_create_evaluation(authenticated_client):
    """Test creating an evaluation."""
    # Create a product first
    product_id = test_create_product(authenticated_client)
    
    # Get criteria
    response = authenticated_client.get("/api/criteria")
    assert response.status_code == 200
    criteria = response.json()
    assert len(criteria) > 0
    criterion_id = criteria[0]["id"]
    
    # Create an evaluation
    evaluation_data = {
        "title": "Test Evaluation",
        "product_id": product_id,
        "criteria_evaluations": [
            {
                "criterion_id": criterion_id,
                "score": 8,
                "notes": "Test notes for this criterion"
            }
        ],
        "notes": "Overall test notes",
        "use_ai_analysis": False
    }
    response = authenticated_client.post("/api/evaluations", json=evaluation_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == evaluation_data["title"]
    assert data["product_id"] == product_id
    assert len(data["criteria_evaluations"]) == 1
    assert data["criteria_evaluations"][0]["criterion_id"] == criterion_id
    assert data["criteria_evaluations"][0]["score"] == 8
    
    # Return the evaluation ID for other tests
    return data["id"]


def test_get_evaluations(authenticated_client):
    """Test getting evaluations."""
    # Create an evaluation first
    evaluation_id = test_create_evaluation(authenticated_client)
    
    # Get evaluations
    response = authenticated_client.get("/api/evaluations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["id"] == evaluation_id


def test_get_evaluation(authenticated_client):
    """Test getting a specific evaluation."""
    # Create an evaluation first
    evaluation_id = test_create_evaluation(authenticated_client)
    
    # Get the evaluation
    response = authenticated_client.get(f"/api/evaluations/{evaluation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == evaluation_id
    assert data["title"] == "Test Evaluation"


def test_update_evaluation(authenticated_client):
    """Test updating an evaluation."""
    # Create an evaluation first
    evaluation_id = test_create_evaluation(authenticated_client)
    
    # Update the evaluation
    update_data = {
        "title": "Updated Evaluation",
        "notes": "Updated test notes",
        "is_published": True
    }
    response = authenticated_client.put(f"/api/evaluations/{evaluation_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == evaluation_id
    assert data["title"] == update_data["title"]
    assert data["notes"] == update_data["notes"]
    assert data["is_published"] == update_data["is_published"]


def test_publish_evaluation(authenticated_client):
    """Test publishing an evaluation."""
    # Create an evaluation first
    evaluation_id = test_create_evaluation(authenticated_client)
    
    # Publish the evaluation
    response = authenticated_client.post(f"/api/evaluations/{evaluation_id}/publish")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == evaluation_id
    assert data["is_published"] is True