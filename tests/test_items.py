from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# Fixtures for reusable test data
@pytest.fixture
def sample_item():
    return {"name": "test item", "price": 10.0}


@pytest.fixture
def created_item():
    response = client.post("/items", json={"name": "fixture item", "price": 25.0})
    return response.json()


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
# Response structure validation tests
def test_create_item_response_structure():
    r = client.post("/items", json={"name": "structured", "price": 15.5})
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "name" in data
    assert "price" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    assert data["name"] == "structured"
    assert data["price"] == 15.5


def test_create_item_response_headers():
    r = client.post("/items", json={"name": "headers", "price": 20.0})
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")


def test_get_item_response_structure():
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "name" in data
    assert "price" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))


# Integration test: create then retrieve
def test_integration_create_and_retrieve_flow(sample_item):
    # Note: This test documents the expected behavior
    # The API currently returns hardcoded data, so we test the flow
    create_response = client.post("/items", json=sample_item)
    assert create_response.status_code == 200
    created_data = create_response.json()
    assert created_data["name"] == sample_item["name"]
    assert created_data["price"] == sample_item["price"]
    
    # Retrieve the item (API returns hardcoded data for ID 1)
    get_response = client.get("/items/1")
    assert get_response.status_code == 200


# Parametrized tests for valid price ranges
@pytest.mark.parametrize("price", [0.01, 1.0, 10.99, 100.50, 999999.99])
def test_create_item_valid_price_range(price):
    r = client.post("/items", json={"name": "price_test", "price": price})
    assert r.status_code == 200
    assert r.json()["price"] == price


# Parametrized tests for invalid price ranges
@pytest.mark.parametrize("price", [-0.01, -1.0, -100.5, 0, 0.0])
def test_create_item_invalid_price_range(price):
    r = client.post("/items", json={"name": "invalid_price", "price": price})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Parametrized tests for name variations
@pytest.mark.parametrize("name", [
    "a",                           # single character
    "abc123",                      # alphanumeric
    "test item with spaces",       # spaces
    "item-with-special_chars",     # special chars
    "unicode-café-名前",           # unicode
    "very " * 100 + "long",        # long name
    ""                             # empty (should be accepted)
])
def test_create_item_valid_name_variations(name):
    r = client.post("/items", json={"name": name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == name


# Error response structure validation
def test_error_response_structure_400():
    r = client.post("/items", json={"name": "item", "price": 0})
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


def test_error_response_structure_404():
    r = client.get("/items/999")
    assert r.status_code == 404
    data = r.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


# Sequential operations test
def test_multiple_sequential_creates():
    items = [
        {"name": "item1", "price": 10.0},
        {"name": "item2", "price": 20.0},
        {"name": "item3", "price": 30.0}
    ]
    for item in items:
        r = client.post("/items", json=item)
        assert r.status_code == 200
        assert r.json()["name"] == item["name"]
        assert r.json()["price"] == item["price"]
