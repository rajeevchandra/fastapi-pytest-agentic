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


# PR #1: Enhanced Input Validation Tests


def test_create_item_negative_price():
    """Test rejection of negative price value"""
    r = client.post("/items", json={"name": "item", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Test rejection of large negative price"""
    r = client.post("/items", json={"name": "item", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_missing_name():
    """Test rejection when name field is missing"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower()


def test_create_item_missing_price():
    """Test rejection when price field is missing"""
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower()


def test_create_item_missing_both_fields():
    """Test rejection when both fields are missing"""
    r = client.post("/items", json={})
    assert r.status_code == 422


def test_create_item_price_as_string():
    """Test rejection of string value for price"""
    r = client.post("/items", json={"name": "item", "price": "invalid"})
    assert r.status_code == 422


def test_create_item_name_as_number():
    """Test rejection of number value for name"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_name():
    """Test rejection of null name"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_price():
    """Test rejection of null price"""
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422


def test_create_item_empty_string_name():
    """Test behavior with empty string name"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Test behavior with whitespace-only name"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


def test_create_item_very_large_price():
    """Test handling of very large price values"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    """Test handling of very long name"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_special_characters_name():
    """Test name with special characters"""
    r = client.post("/items", json={"name": "test@#$%^&*()", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "test@#$%^&*()"


def test_create_item_unicode_name():
    """Test name with unicode characters"""
    r = client.post("/items", json={"name": "测试🎉", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "测试🎉"


def test_create_item_malformed_json():
    """Test rejection of malformed JSON"""
    r = client.post("/items", data="not json", headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_create_item_extra_fields():
    """Test handling of extra fields in request"""
    r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "field"})
    assert r.status_code == 200
    data = r.json()
    assert "extra" not in data


def test_create_item_very_small_positive_price():
    """Test handling of very small positive price"""
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    assert r.json()["price"] == 0.01
