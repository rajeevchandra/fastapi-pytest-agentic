import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_item():
    """Fixture providing a sample item for testing"""
    return {"name": "book", "price": 12.5}


@pytest.fixture
def created_item():
    """Fixture that creates an item and returns the response"""
    response = client.post("/items", json={"name": "test_item", "price": 25.99})
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


# ===== PR #3: Integration & Response Validation Tests =====


def test_create_item_response_structure(sample_item):
    """Test complete response structure for POST /items"""
    response = client.post("/items", json=sample_item)
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate all expected fields are present
    assert "id" in data
    assert "name" in data
    assert "price" in data
    
    # Validate field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], float)
    
    # Validate field values
    assert data["name"] == sample_item["name"]
    assert data["price"] == sample_item["price"]


def test_get_item_response_structure():
    """Test complete response structure for GET /items/{item_id}"""
    response = client.get("/items/1")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate all expected fields are present
    assert "id" in data
    assert "name" in data
    assert "price" in data
    
    # Validate field types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["price"], float)


def test_create_item_headers():
    """Test response headers for POST /items"""
    response = client.post("/items", json={"name": "book", "price": 9.99})
    
    assert response.status_code == 200
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/json"


def test_get_item_headers():
    """Test response headers for GET /items/{item_id}"""
    response = client.get("/items/1")
    
    assert response.status_code == 200
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/json"


def test_error_response_structure_400():
    """Test error response structure for 400 errors"""
    response = client.post("/items", json={"name": "invalid", "price": -5})
    
    assert response.status_code == 400
    data = response.json()
    
    # Validate error response structure
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert data["detail"] == "price must be > 0"


def test_error_response_structure_404():
    """Test error response structure for 404 errors"""
    response = client.get("/items/999")
    
    assert response.status_code == 404
    data = response.json()
    
    # Validate error response structure
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert data["detail"] == "not found"


@pytest.mark.parametrize("name,price", [
    ("apple", 1.0),
    ("banana", 0.5),
    ("laptop", 999.99),
    ("pencil", 0.01),
    ("car", 25000.0),
])
def test_create_item_parametrized(name, price):
    """Parametrized test for various valid item combinations"""
    response = client.post("/items", json={"name": name, "price": price})
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["price"] == price


@pytest.mark.parametrize("item_id", [1, 2, 3, 100, 999])
def test_get_item_parametrized_not_found(item_id):
    """Parametrized test for various item_id values (only id=1 exists)"""
    response = client.get(f"/items/{item_id}")
    
    if item_id == 1:
        assert response.status_code == 200
    else:
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"
