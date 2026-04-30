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
    """Test item_id = 0 (boundary value)"""
    r = client.get("/items/0")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_negative_id():
    """Test negative item_id"""
    r = client.get("/items/-1")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_large_negative_id():
    """Test very large negative item_id"""
    r = client.get("/items/-999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_large_positive_id():
    """Test very large positive item_id"""
    r = client.get("/items/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_max_int():
    """Test maximum integer value"""
    r = client.get("/items/2147483647")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


def test_get_item_invalid_type_string():
    """Test string instead of integer for item_id"""
    r = client.get("/items/abc")
    assert r.status_code == 422
    # FastAPI automatic validation error for type mismatch


def test_get_item_invalid_type_float():
    """Test float instead of integer for item_id"""
    r = client.get("/items/1.5")
    assert r.status_code == 422
    # FastAPI automatic validation error for type mismatch
