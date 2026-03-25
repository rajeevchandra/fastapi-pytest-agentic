from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


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


# PR #3: Integration & Response Validation Tests


# Fixtures for reusable test data
@pytest.fixture
def sample_item():
    """Provides a valid item payload for testing"""
    return {"name": "test-item", "price": 25.99}


@pytest.fixture
def created_item(sample_item):
    """Creates an item and returns the response data"""
    r = client.post("/items", json=sample_item)
    assert r.status_code == 200
    return r.json()


# Response Structure Validation Tests
def test_create_item_response_structure(sample_item):
    r = client.post("/items", json=sample_item)
    assert r.status_code == 200
    data = r.json()
    
    # Validate all expected fields are present
    assert "id" in data
    assert "name" in data
    assert "price" in data
    
    # Validate field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    
    # Validate values match input
    assert data["name"] == sample_item["name"]
    assert data["price"] == sample_item["price"]


def test_get_item_complete_response_structure():
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    
    # Validate structure
    assert len(data) == 3
    assert set(data.keys()) == {"id", "name", "price"}
    
    # Validate types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))


def test_error_response_structure():
    r = client.get("/items/999")
    assert r.status_code == 404
    data = r.json()
    
    # Validate error response has detail field
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


# Headers and Content Type Tests
def test_create_item_response_headers(sample_item):
    r = client.post("/items", json=sample_item)
    assert r.status_code == 200
    assert "content-type" in r.headers
    assert "application/json" in r.headers["content-type"]


def test_get_item_response_headers():
    r = client.get("/items/1")
    assert r.status_code == 200
    assert "content-type" in r.headers
    assert "application/json" in r.headers["content-type"]


# Integration Tests - Create then Retrieve
def test_create_and_retrieve_workflow(sample_item):
    # Note: Since the API always returns id=1, this is a limited integration test
    create_r = client.post("/items", json=sample_item)
    assert create_r.status_code == 200
    
    # The API returns hardcoded id=1 and data
    get_r = client.get("/items/1")
    assert get_r.status_code == 200
    
    # Validate the GET returns consistent structure
    get_data = get_r.json()
    assert "id" in get_data
    assert "name" in get_data
    assert "price" in get_data


def test_multiple_validations_same_endpoint():
    # Test that multiple calls work consistently
    r1 = client.get("/items/1")
    r2 = client.get("/items/1")
    
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()


# Parametrized Tests for Value Ranges
@pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.0, 1000.0])
def test_create_item_valid_price_range(price):
    r = client.post("/items", json={"name": "item", "price": price})
    assert r.status_code == 200
    data = r.json()
    assert data["price"] == price


@pytest.mark.parametrize("price", [0, -0.01, -1, -100])
def test_create_item_invalid_price_range(price):
    r = client.post("/items", json={"name": "item", "price": price})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


@pytest.mark.parametrize("item_id", [0, 2, 100, -1, 999999])
def test_get_item_not_found_various_ids(item_id):
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"
