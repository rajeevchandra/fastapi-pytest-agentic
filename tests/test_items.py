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


def test_get_item_zero_id():
    """Test GET with item_id = 0 (boundary value)"""
    r = client.get("/items/0")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_negative_id():
    """Test GET with negative item_id"""
    r = client.get("/items/-1")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_large_negative_id():
    """Test GET with large negative item_id"""
    r = client.get("/items/-999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_very_large_id():
    """Test GET with very large item_id"""
    r = client.get("/items/999999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_max_int_boundary():
    """Test GET with maximum integer boundary value"""
    r = client.get("/items/2147483647")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_invalid_string_id():
    """Test GET with string instead of integer for item_id"""
    r = client.get("/items/abc")
    assert r.status_code == 422  # FastAPI validation error
    assert "detail" in r.json()


def test_get_item_invalid_float_id():
    """Test GET with float instead of integer for item_id"""
    r = client.get("/items/1.5")
    assert r.status_code == 422  # FastAPI validation error
    assert "detail" in r.json()
