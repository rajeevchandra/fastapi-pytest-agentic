from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# Fixtures for test data
@pytest.fixture
def valid_item_data():
    """Fixture providing valid item data"""
    return {"name": "test-item", "price": 25.99}


@pytest.fixture
def invalid_prices():
    """Fixture providing invalid price values"""
    return [0, -1, -100.5, -0.01]


# Parametrized tests for price validation
@pytest.mark.parametrize("price", [0, -1, -5.5, -100, -0.01])
def test_create_item_invalid_prices_parametrized(price):
    """Parametrized test for various invalid prices"""
    r = client.post("/items", json={"name": "item", "price": price})
    assert r.status_code == 400
    assert "price must be > 0" in r.json()["detail"]


@pytest.mark.parametrize("price", [0.01, 1, 10.5, 100, 999.99, 9999999.99])
def test_create_item_valid_prices_parametrized(price):
    """Parametrized test for various valid prices"""
    r = client.post("/items", json={"name": "item", "price": price})
    assert r.status_code == 200
    assert r.json()["price"] == price


@pytest.mark.parametrize("name", ["a", "test", "product-123", "item_with_underscore", "测试", "🎁"])
def test_create_item_valid_names_parametrized(name):
    """Parametrized test for various valid names"""
    r = client.post("/items", json={"name": name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == name


@pytest.mark.parametrize("item_id", [2, 3, 99, 100, 999, 10000])
def test_get_item_not_found_parametrized(item_id):
    """Parametrized test for various non-existent item IDs"""
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


# Integration test: Create and retrieve pattern
def test_integration_health_check_then_items():
    """Integration: Check health before working with items"""
    # First verify service is healthy
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    
    # Then work with items
    item_response = client.get("/items/1")
    assert item_response.status_code == 200


def test_integration_multiple_operations_sequence():
    """Integration: Sequence of multiple operations"""
    # Create an item
    create_response = client.post("/items", json={"name": "widget", "price": 15.0})
    assert create_response.status_code == 200
    
    # Get existing item
    get_response = client.get("/items/1")
    assert get_response.status_code == 200
    
    # Try to get non-existent item
    not_found_response = client.get("/items/999")
    assert not_found_response.status_code == 404


def test_integration_error_recovery():
    """Integration: Test error recovery patterns"""
    # Try invalid request
    error_response = client.post("/items", json={"name": "bad", "price": -1})
    assert error_response.status_code == 400
    
    # Follow up with valid request - should work
    valid_response = client.post("/items", json={"name": "good", "price": 10})
    assert valid_response.status_code == 200


# Complete response validation tests
def test_complete_create_response_structure():
    """Validate complete structure of create item response"""
    r = client.post("/items", json={"name": "complete-test", "price": 12.34})
    assert r.status_code == 200
    
    data = r.json()
    # Check all expected fields exist
    assert set(data.keys()) == {"id", "name", "price"}
    
    # Validate field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    
    # Validate field values
    assert data["id"] == 1
    assert data["name"] == "complete-test"
    assert data["price"] == 12.34


def test_complete_get_response_structure():
    """Validate complete structure of get item response"""
    r = client.get("/items/1")
    assert r.status_code == 200
    
    data = r.json()
    # Check exact fields
    assert set(data.keys()) == {"id", "name", "price"}
    
    # Validate types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    
    # Validate sample values
    assert data["id"] == 1
    assert data["name"] == "sample"
    assert data["price"] == 10.0


def test_complete_error_response_structure():
    """Validate complete structure of error responses"""
    # 404 error
    r_404 = client.get("/items/999")
    assert r_404.status_code == 404
    assert "detail" in r_404.json()
    
    # 400 error
    r_400 = client.post("/items", json={"name": "x", "price": -1})
    assert r_400.status_code == 400
    assert "detail" in r_400.json()
    
    # 422 error
    r_422 = client.post("/items", json={"name": "x"})
    assert r_422.status_code == 422
    # 422 has different structure with loc, msg, type
    assert isinstance(r_422.json(), dict) or isinstance(r_422.json(), list)


# Header validation tests
def test_response_headers_post():
    """Validate response headers for POST endpoint"""
    r = client.post("/items", json={"name": "header-test", "price": 5.0})
    assert r.status_code == 200
    
    # Check content type
    assert "content-type" in r.headers
    assert "application/json" in r.headers["content-type"]


def test_response_headers_get():
    """Validate response headers for GET endpoint"""
    r = client.get("/items/1")
    assert r.status_code == 200
    
    # Check content type
    assert "content-type" in r.headers
    assert "application/json" in r.headers["content-type"]


def test_response_headers_health():
    """Validate response headers for health endpoint"""
    r = client.get("/health")
    assert r.status_code == 200
    
    # Check content type
    assert "content-type" in r.headers
    assert "application/json" in r.headers["content-type"]


# API consistency tests
def test_api_consistency_across_endpoints():
    """Validate consistent behavior across all endpoints"""
    responses = [
        client.get("/health"),
        client.get("/items/1"),
        client.post("/items", json={"name": "test", "price": 10})
    ]
    
    # All should return JSON
    for r in responses:
        assert "application/json" in r.headers.get("content-type", "")
        assert r.status_code == 200


def test_error_consistency():
    """Validate consistent error response format"""
    errors = [
        client.get("/items/999"),  # 404
        client.post("/items", json={"name": "x", "price": -1}),  # 400
    ]
    
    # All should have detail field
    for r in errors:
        assert r.status_code in [400, 404]
        assert "detail" in r.json()


# Fixture-based tests
def test_with_valid_item_fixture(valid_item_data):
    """Test using valid item data fixture"""
    r = client.post("/items", json=valid_item_data)
    assert r.status_code == 200
    assert r.json()["name"] == valid_item_data["name"]
    assert r.json()["price"] == valid_item_data["price"]


def test_with_invalid_prices_fixture(invalid_prices):
    """Test using invalid prices fixture"""
    for price in invalid_prices:
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400


# Cross-endpoint validation
def test_health_endpoint_isolation():
    """Validate health endpoint is independent of other operations"""
    # Health should work before any items operations
    r1 = client.get("/health")
    assert r1.status_code == 200
    
    # Create an item
    client.post("/items", json={"name": "test", "price": 10})
    
    # Health should still work the same
    r2 = client.get("/health")
    assert r2.status_code == 200
    assert r1.json() == r2.json()


def test_concurrent_endpoint_access():
    """Test that different endpoints can be accessed in any order"""
    # Random access pattern
    r1 = client.get("/items/1")
    r2 = client.get("/health")
    r3 = client.post("/items", json={"name": "x", "price": 1})
    r4 = client.get("/items/999")
    
    # All should respond correctly
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200
    assert r4.status_code == 404
