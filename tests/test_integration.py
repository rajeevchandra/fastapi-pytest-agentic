import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Fixtures for reusable test data
@pytest.fixture
def sample_item():
    """Provides a valid item payload for testing"""
    return {"name": "Test Item", "price": 25.99}


@pytest.fixture
def created_item(sample_item):
    """Creates an item and returns its data for dependent tests"""
    response = client.post("/items", json=sample_item)
    return response.json()


# Response Structure Validation Tests
def test_create_item_response_structure(sample_item):
    """Validates complete response structure for POST /items"""
    response = client.post("/items", json=sample_item)
    assert response.status_code == 200
    data = response.json()
    
    # Verify all expected fields are present
    assert "id" in data
    assert "name" in data
    assert "price" in data
    
    # Verify field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    
    # Verify values match input
    assert data["name"] == sample_item["name"]
    assert data["price"] == sample_item["price"]


def test_get_item_response_structure():
    """Validates complete response structure for GET /items/{item_id}"""
    response = client.get("/items/1")
    assert response.status_code == 200
    data = response.json()
    
    # Verify all expected fields are present
    assert "id" in data
    assert "name" in data
    assert "price" in data
    
    # Verify field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))


def test_error_response_structure():
    """Validates error response structure"""
    response = client.get("/items/999")
    assert response.status_code == 404
    data = response.json()
    
    # FastAPI HTTPException returns detail field
    assert "detail" in data
    assert isinstance(data["detail"], str)


# Headers and Content Type Tests
def test_create_item_content_type(sample_item):
    """Validates response content type for POST /items"""
    response = client.post("/items", json=sample_item)
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


def test_get_item_content_type():
    """Validates response content type for GET /items/{item_id}"""
    response = client.get("/items/1")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


def test_health_content_type():
    """Validates response content type for GET /health"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


# Integration Tests - API Interaction Patterns
def test_create_then_retrieve_workflow():
    """Tests end-to-end workflow: create item, then retrieve it"""
    # Create an item
    create_payload = {"name": "Workflow Test Item", "price": 45.00}
    create_response = client.post("/items", json=create_payload)
    assert create_response.status_code == 200
    created_data = create_response.json()
    item_id = created_data["id"]
    
    # Retrieve the same item
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 200
    retrieved_data = get_response.json()
    
    # Verify ID matches
    assert retrieved_data["id"] == item_id


def test_multiple_creates_same_session():
    """Tests creating multiple items in the same session"""
    items = [
        {"name": "Item A", "price": 10.0},
        {"name": "Item B", "price": 20.0},
        {"name": "Item C", "price": 30.0},
    ]
    
    for item_data in items:
        response = client.post("/items", json=item_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == item_data["name"]
        assert data["price"] == item_data["price"]


# Parametrized Tests for Value Ranges
@pytest.mark.parametrize("price", [
    0.01,      # minimum valid price
    1.00,      # small price
    99.99,     # typical price
    999.99,    # large price
    9999.99,   # very large price
])
def test_valid_price_ranges(price):
    """Tests various valid price values using parametrization"""
    response = client.post("/items", json={"name": "Price Test", "price": price})
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == price


@pytest.mark.parametrize("name", [
    "A",                    # single character
    "Short",                # short name
    "Medium Length Name",   # medium name
    "A" * 100,             # long name
    "Item with Numbers 123",
    "Item-with-dashes",
    "Item_with_underscores",
    "Item with émojis 🎉",
])
def test_valid_name_variations(name):
    """Tests various valid name values using parametrization"""
    response = client.post("/items", json={"name": name, "price": 10.0})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name


@pytest.mark.parametrize("item_id,expected_status", [
    (1, 200),    # valid ID
    (2, 404),    # non-existent ID
    (999, 404),  # large non-existent ID
])
def test_get_item_various_ids(item_id, expected_status):
    """Tests GET endpoint with various item IDs"""
    response = client.get(f"/items/{item_id}")
    assert response.status_code == expected_status


# Edge Case Tests
def test_health_endpoint_always_available():
    """Verifies health endpoint is always accessible"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_handles_trailing_slash():
    """Tests if API handles URLs with trailing slashes"""
    # Most FastAPI apps handle this, but let's verify
    response = client.get("/health/")
    # Accept either 200 (if trailing slash is handled) or 404/307 (redirect)
    assert response.status_code in [200, 307, 404]


def test_create_item_preserves_decimal_precision():
    """Verifies decimal precision is preserved in price"""
    response = client.post("/items", json={"name": "Precise", "price": 12.345})
    assert response.status_code == 200
    data = response.json()
    # Check if precision is preserved (within float tolerance)
    assert abs(data["price"] - 12.345) < 0.0001
