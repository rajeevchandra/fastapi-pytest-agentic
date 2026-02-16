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

# Fixtures for common test data
@pytest.fixture
def valid_item_data():
    return {"name": "test-item", "price": 25.99}


@pytest.fixture
def invalid_item_data():
    return {"name": "invalid", "price": -5}


# Integration Tests - End-to-End Scenarios
def test_create_and_verify_response_headers(valid_item_data):
    r = client.post("/items", json=valid_item_data)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"
    data = r.json()
    assert data["name"] == valid_item_data["name"]
    assert data["price"] == valid_item_data["price"]


def test_get_item_response_headers():
    r = client.get("/items/1")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"


def test_error_response_structure_400():
    r = client.post("/items", json={"name": "test", "price": 0})
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


def test_error_response_structure_422():
    r = client.post("/items", json={"name": "test"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)


# Parametrized Tests for Value Ranges
@pytest.mark.parametrize("price", [0.01, 1.00, 10.50, 100.00, 9999.99])
def test_create_item_valid_price_range(price):
    r = client.post("/items", json={"name": "item", "price": price})
    assert r.status_code == 200
    assert r.json()["price"] == price


@pytest.mark.parametrize("price", [0, -0.01, -1, -100, -9999.99])
def test_create_item_invalid_price_range(price):
    r = client.post("/items", json={"name": "item", "price": price})
    assert r.status_code == 400
    assert "price must be > 0" in r.json()["detail"]


@pytest.mark.parametrize("item_id", [0, 2, 3, 100, 999, -1, -100])
def test_get_item_not_found_range(item_id):
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"
