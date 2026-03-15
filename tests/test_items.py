from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# Basic Functionality Tests


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


class TestResponseStructure:
    """Test complete response structure and headers"""
    
    def test_create_item_response_structure(self):
        """Verify POST /items returns complete response with correct structure"""
        r = client.post("/items", json={"name": "test", "price": 99.99})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)
    
    def test_create_item_content_type(self):
        """Verify response has correct content-type header"""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]
    
    def test_get_item_response_structure(self):
        """Verify GET /items/{id} returns complete response structure"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0
    
    def test_error_response_structure(self):
        """Verify error responses have correct structure"""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        error = r.json()
        assert "detail" in error
        assert error["detail"] == "price must be > 0"


class TestIntegrationScenarios:
    """Test end-to-end API interaction patterns"""
    
    def test_create_and_retrieve_workflow(self):
        """Test that creating an item doesn't affect retrieval of item 1"""
        # This API always returns id=1, but we test the workflow
        create_response = client.post("/items", json={"name": "new_item", "price": 50.0})
        assert create_response.status_code == 200
        
        # GET still returns the hardcoded item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "sample"
    
    def test_multiple_creates_with_different_prices(self):
        """Test multiple POST requests with various price values"""
        prices = [0.01, 1.0, 100.0, 9999.99]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


@pytest.mark.parametrize("name,price,expected_status", [
    ("valid", 10.0, 200),
    ("also_valid", 0.01, 200),
    ("expensive", 999999.99, 200),
    ("zero_price", 0, 400),
    ("negative", -1, 400),
])
def test_create_item_parametrized(name, price, expected_status):
    """Parametrized test for various name/price combinations"""
    r = client.post("/items", json={"name": name, "price": price})
    assert r.status_code == expected_status


@pytest.mark.parametrize("item_id,expected_status", [
    (1, 200),
    (2, 404),
    (0, 404),
    (-1, 404),
    (999, 404),
])
def test_get_item_parametrized(item_id, expected_status):
    """Parametrized test for various item_id values"""
    r = client.get(f"/items/{item_id}")
    assert r.status_code == expected_status
