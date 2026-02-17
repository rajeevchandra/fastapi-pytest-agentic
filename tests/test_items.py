from fastapi.testclient import TestClient
from app.main import app

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


# PR #2: GET Endpoint Edge Cases & Error Handling


def test_get_item_boundary_zero():
    """Test item_id boundary value: 0"""
    r = client.get("/items/0")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_negative_id():
    """Test negative item_id"""
    r = client.get("/items/-1")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_large_negative_id():
    """Test large negative item_id"""
    r = client.get("/items/-999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_very_large_id():
    """Test very large item_id (within int range)"""
    r = client.get("/items/999999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_invalid_type_string():
    """Test invalid path parameter type: string instead of int"""
    r = client.get("/items/abc")
    assert r.status_code == 422  # FastAPI validation error


def test_get_item_invalid_type_float():
    """Test invalid path parameter type: float"""
    r = client.get("/items/1.5")
    assert r.status_code == 422  # FastAPI validation error


def test_get_item_response_structure():
    """Test complete response structure for successful GET"""
    r = client.get("/items/1")
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "name" in data
    assert "price" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], (int, float))
    assert data["id"] == 1
    assert data["name"] == "sample"
    assert data["price"] == 10.0
