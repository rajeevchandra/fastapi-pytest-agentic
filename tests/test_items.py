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


# Fixtures for Integration Testing

@pytest.fixture
def sample_item():
    """Fixture providing a valid item payload"""
    return {"name": "test_item", "price": 19.99}


@pytest.fixture
def created_item(sample_item):
    """Fixture that creates an item and returns the response data"""
    r = client.post("/items", json=sample_item)
    assert r.status_code == 200
    return r.json()


# Integration & Response Validation Tests

def test_create_and_retrieve_flow(created_item):
    """Test end-to-end flow: create item then retrieve it"""
    item_id = created_item["id"]
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 200
    retrieved = r.json()
    # Verify the retrieved item matches created data
    assert retrieved["id"] == item_id


def test_create_item_response_structure(sample_item):
    """Test POST response has complete structure with correct types"""
    r = client.post("/items", json=sample_item)
    assert r.status_code == 200
    data = r.json()
    # Validate structure
    assert "id" in data
    assert "name" in data
    assert "price" in data
    assert len(data) >= 3
    # Validate types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    # Validate values
    assert data["id"] > 0
    assert data["name"] == sample_item["name"]
    assert data["price"] == sample_item["price"]


def test_create_item_response_headers(sample_item):
    """Test POST response headers are correct"""
    r = client.post("/items", json=sample_item)
    assert r.status_code == 200
    assert "content-type" in r.headers
    assert "application/json" in r.headers["content-type"]


def test_get_item_response_structure():
    """Test GET response has complete structure with correct types"""
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    # Validate structure
    assert "id" in data
    assert "name" in data
    assert "price" in data
    # Validate types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    # Validate specific values
    assert data["id"] == 1
    assert isinstance(data["name"], str)
    assert len(data["name"]) > 0


def test_get_item_response_headers():
    """Test GET response headers are correct"""
    r = client.get("/items/1")
    assert r.status_code == 200
    assert "content-type" in r.headers
    assert "application/json" in r.headers["content-type"]


def test_error_response_400_structure(sample_item):
    """Test 400 error response structure is valid"""
    invalid_item = {**sample_item, "price": -10}
    r = client.post("/items", json=invalid_item)
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


def test_error_response_404_structure():
    """Test 404 error response structure is valid"""
    r = client.get("/items/999")
    assert r.status_code == 404
    data = r.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


# Parametrized Tests for Better Value Range Coverage

@pytest.mark.parametrize("price", [0.01, 1.0, 10.99, 100.50, 999999.99])
def test_create_item_valid_price_range(price):
    """Test creating items with various valid price values"""
    r = client.post("/items", json={"name": f"item_{price}", "price": price})
    assert r.status_code == 200
    assert r.json()["price"] == price


@pytest.mark.parametrize("price", [-0.01, -1.0, -100.5, 0, 0.0])
def test_create_item_invalid_price_range(price):
    """Test that non-positive prices are rejected"""
    r = client.post("/items", json={"name": "test", "price": price})
    assert r.status_code == 400
    assert "price must be > 0" in r.json()["detail"]


@pytest.mark.parametrize("name", [
    "a",
    "test item",
    "Item-123",
    "Special!@#$",
    "Unicode测试",
])
def test_create_item_valid_name_variations(name):
    """Test creating items with various valid name formats"""
    r = client.post("/items", json={"name": name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == name


@pytest.mark.parametrize("item_id", [1, 0, -1, 999, 2147483647])
def test_get_item_parametrized_ids(item_id):
    """Test GET with various item_id values"""
    r = client.get(f"/items/{item_id}")
    if item_id == 1:
        assert r.status_code == 200
    else:
        assert r.status_code == 404
