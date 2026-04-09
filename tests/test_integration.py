"""
Integration tests for the API endpoints.

These tests focus on end-to-end scenarios, response validation,
and API interaction patterns.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Fixtures for test organization
@pytest.fixture
def valid_item_data():
    """Fixture providing valid item data"""
    return {"name": "Test Item", "price": 29.99}


@pytest.fixture
def various_prices():
    """Fixture providing various valid price values for parametrized tests"""
    return [0.01, 1.0, 10.5, 99.99, 1000.0, 9999.99]


@pytest.fixture
def various_names():
    """Fixture providing various valid name values"""
    return ["Book", "Laptop", "Coffee ☕", "测试商品", "Item-123", "A" * 100]


# End-to-end integration tests
def test_api_headers_content_type():
    """Validate that API returns correct content-type header"""
    r = client.get("/items/1")
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")


def test_post_response_headers():
    """Validate POST response headers"""
    r = client.post("/items", json={"name": "item", "price": 10.0})
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")


def test_error_response_headers():
    """Validate error response headers"""
    r = client.get("/items/999")
    assert r.status_code == 404
    assert "application/json" in r.headers.get("content-type", "")


def test_health_check_integration():
    """Test health check as part of integration flow"""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# Response structure validation
def test_post_response_contains_all_fields(valid_item_data):
    """Verify POST response includes all expected fields"""
    r = client.post("/items", json=valid_item_data)
    assert r.status_code == 200
    data = r.json()
    
    # Check all required fields are present
    assert "id" in data
    assert "name" in data
    assert "price" in data
    
    # Check field values match input
    assert data["name"] == valid_item_data["name"]
    assert data["price"] == valid_item_data["price"]
    assert data["id"] == 1


def test_get_response_has_correct_types():
    """Verify GET response has correct data types"""
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))


def test_error_response_has_detail():
    """Verify error responses have detail field"""
    # Test 404 error
    r = client.get("/items/999")
    assert r.status_code == 404
    assert "detail" in r.json()
    
    # Test 400 error
    r = client.post("/items", json={"name": "item", "price": -1})
    assert r.status_code == 400
    assert "detail" in r.json()


# Parametrized tests for value ranges
@pytest.mark.parametrize("price", [0.01, 1.0, 10.5, 99.99, 1000.0, 9999.99])
def test_create_item_with_various_prices(price):
    """Test creating items with various valid price values"""
    r = client.post("/items", json={"name": "Test Item", "price": price})
    assert r.status_code == 200
    assert r.json()["price"] == price


@pytest.mark.parametrize("name", [
    "Book",
    "Laptop",
    "Coffee ☕",
    "测试商品",
    "Item-123",
    "A" * 100,
    "!@#$%^&*()",
])
def test_create_item_with_various_names(name):
    """Test creating items with various valid name values"""
    r = client.post("/items", json={"name": name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == name


@pytest.mark.parametrize("invalid_price", [-1, -10.5, 0, -999.99])
def test_reject_invalid_prices(invalid_price):
    """Test rejection of invalid price values"""
    r = client.post("/items", json={"name": "item", "price": invalid_price})
    assert r.status_code == 400
    assert "price must be > 0" in r.json()["detail"]


@pytest.mark.parametrize("item_id", [0, 2, 3, -1, 999, 10000])
def test_get_nonexistent_items(item_id):
    """Test getting non-existent items with various IDs"""
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


# API interaction patterns
def test_consistent_id_returned():
    """Verify that the same ID is consistently returned"""
    # Create multiple items
    r1 = client.post("/items", json={"name": "item1", "price": 10.0})
    r2 = client.post("/items", json={"name": "item2", "price": 20.0})
    r3 = client.post("/items", json={"name": "item3", "price": 30.0})
    
    # All should return ID = 1 (current implementation)
    assert r1.json()["id"] == 1
    assert r2.json()["id"] == 1
    assert r3.json()["id"] == 1


def test_get_returns_fixed_data():
    """Verify GET always returns fixed sample data"""
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    
    # Current implementation returns fixed values
    assert data["id"] == 1
    assert data["name"] == "sample"
    assert data["price"] == 10.0


def test_multiple_requests_consistent():
    """Test that multiple identical requests return consistent results"""
    results = []
    for _ in range(3):
        r = client.post("/items", json={"name": "test", "price": 15.0})
        results.append(r.json())
    
    # All responses should be identical
    assert results[0] == results[1] == results[2]


# Request validation edge cases
def test_post_with_json_number_for_name():
    """Test that numeric name is converted to string"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "123"
    assert isinstance(r.json()["name"], str)


def test_post_with_integer_price():
    """Test that integer price is accepted"""
    r = client.post("/items", json={"name": "item", "price": 10})
    assert r.status_code == 200
    assert r.json()["price"] == 10.0


def test_422_validation_error_structure():
    """Verify 422 validation error has expected structure"""
    r = client.post("/items", json={"name": "item"})  # Missing price
    assert r.status_code == 422
    data = r.json()
    
    # FastAPI validation errors have 'detail' field with error list
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0
