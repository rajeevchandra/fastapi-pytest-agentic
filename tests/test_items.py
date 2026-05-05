from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# ===== Fixtures =====

@pytest.fixture
def sample_item():
    """Fixture providing sample item data"""
    return {"name": "test-item", "price": 25.99}


@pytest.fixture
def created_item(sample_item):
    """Fixture that creates an item and returns the response"""
    response = client.post("/items", json=sample_item)
    return response.json()


# ===== Original Tests =====

def test_create_item_success():
    r = client.post("/items", json={"name": "book", "price": 12.5})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert data["name"] == "book"
    assert data["price"] == 12.5


def test_create_item_rejects_non_positive_price():
    r = client.post("/items", json={"name": "bad", "price": 0})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_get_item_found():
    r = client.get("/items/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_get_item_not_found():
    r = client.get("/items/2")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


# ===== PR #3: Integration & Response Validation Tests =====

# Complete Response Structure Validation
def test_create_item_complete_response_structure():
    """Test complete response structure for POST /items"""
    r = client.post("/items", json={"name": "laptop", "price": 999.99})
    assert r.status_code == 200
    data = r.json()
    
    # Verify all expected fields are present
    assert "id" in data
    assert "name" in data
    assert "price" in data
    
    # Verify field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    
    # Verify values match request
    assert data["name"] == "laptop"
    assert data["price"] == 999.99


def test_get_item_complete_response_structure():
    """Test complete response structure for GET /items/{item_id}"""
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    
    # Verify all fields are present
    assert set(data.keys()) == {"id", "name", "price"}
    
    # Verify field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))


# Headers and Content Types
def test_create_item_content_type():
    """Test that response has correct content type"""
    r = client.post("/items", json={"name": "item", "price": 10.0})
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")


def test_get_item_content_type():
    """Test that GET response has correct content type"""
    r = client.get("/items/1")
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")


def test_error_response_content_type():
    """Test that error responses have correct content type"""
    r = client.get("/items/999")
    assert r.status_code == 404
    assert "application/json" in r.headers.get("content-type", "")


# API Interaction Patterns (Integration Tests)
def test_create_and_retrieve_workflow():
    """Test end-to-end workflow: create item then retrieve it"""
    # Create an item
    create_data = {"name": "smartphone", "price": 699.00}
    create_response = client.post("/items", json=create_data)
    assert create_response.status_code == 200
    created = create_response.json()
    
    # Retrieve the item (note: current API always returns item with id=1)
    get_response = client.get(f"/items/{created['id']}")
    assert get_response.status_code == 200
    retrieved = get_response.json()
    
    # Verify item has correct ID
    assert retrieved["id"] == created["id"]


# Fixture-based Tests
def test_create_item_with_fixture(sample_item):
    """Test item creation using fixture data"""
    r = client.post("/items", json=sample_item)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == sample_item["name"]
    assert data["price"] == sample_item["price"]


def test_created_item_fixture(created_item):
    """Test using the created_item fixture"""
    assert "id" in created_item
    assert "name" in created_item
    assert "price" in created_item
    assert created_item["id"] == 1


# Parametrized Tests
@pytest.mark.parametrize("name,price", [
    ("book", 15.99),
    ("pen", 2.50),
    ("notebook", 5.00),
    ("laptop", 1200.00),
    ("mouse", 25.99),
])
def test_create_item_parametrized_valid(name, price):
    """Parametrized test for valid item creation"""
    r = client.post("/items", json={"name": name, "price": price})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == name
    assert data["price"] == price


@pytest.mark.parametrize("price", [-1, -100, 0, -0.01])
def test_create_item_parametrized_invalid_prices(price):
    """Parametrized test for invalid prices"""
    r = client.post("/items", json={"name": "item", "price": price})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


@pytest.mark.parametrize("item_id", [2, 3, 5, 10, 100, 999])
def test_get_item_parametrized_not_found(item_id):
    """Parametrized test for items that don't exist"""
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


# Error Response Structure Validation
def test_validation_error_structure():
    """Test structure of validation error responses (422)"""
    r = client.post("/items", json={"name": "item"})  # missing price
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)


def test_business_error_structure():
    """Test structure of business logic error responses (400)"""
    r = client.post("/items", json={"name": "item", "price": 0})
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
    assert data["detail"] == "price must be > 0"


def test_not_found_error_structure():
    """Test structure of not found error responses (404)"""
    r = client.get("/items/999")
    assert r.status_code == 404
    data = r.json()
    assert "detail" in data
    assert data["detail"] == "not found"
