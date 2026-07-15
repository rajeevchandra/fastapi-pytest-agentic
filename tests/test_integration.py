"""
Integration tests and comprehensive response validation.
Tests end-to-end scenarios and API interaction patterns.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_item_data():
    """Fixture providing sample item data."""
    return {"name": "test_item", "price": 25.50}


@pytest.fixture
def created_item(sample_item_data):
    """Fixture that creates an item and returns the response."""
    response = client.post("/items", json=sample_item_data)
    return response.json()


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_endpoint_returns_200(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200
    
    def test_health_endpoint_returns_ok_status(self):
        """Test that health endpoint returns ok status."""
        r = client.get("/health")
        assert r.json()["status"] == "ok"
    
    def test_health_endpoint_response_structure(self):
        """Test health endpoint response has expected structure."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestCreateItemResponseStructure:
    """Test the response structure of item creation."""
    
    def test_create_item_response_has_all_fields(self, sample_item_data):
        """Test that create response has all required fields."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data
    
    def test_create_item_response_has_correct_types(self, sample_item_data):
        """Test that response fields have correct types."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
    
    def test_create_item_response_matches_input_for_name(self, sample_item_data):
        """Test that response name matches input."""
        r = client.post("/items", json=sample_item_data)
        assert r.json()["name"] == sample_item_data["name"]
    
    def test_create_item_response_matches_input_for_price(self, sample_item_data):
        """Test that response price matches input."""
        r = client.post("/items", json=sample_item_data)
        assert r.json()["price"] == sample_item_data["price"]
    
    def test_create_item_response_has_id(self, sample_item_data):
        """Test that response includes an ID."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        assert "id" in data
        assert data["id"] is not None


class TestGetItemResponseStructure:
    """Test the response structure of item retrieval."""
    
    def test_get_item_response_has_all_fields(self):
        """Test that get response has all required fields."""
        r = client.get("/items/1")
        data = r.json()
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data
    
    def test_get_item_response_has_correct_types(self):
        """Test that get response fields have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
    
    def test_get_item_returns_correct_data(self):
        """Test that get returns the correct item data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestErrorResponses:
    """Test error response structures and formats."""
    
    def test_invalid_price_error_has_detail(self):
        """Test that invalid price error includes detail."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert "detail" in r.json()
    
    def test_invalid_price_error_message(self):
        """Test that invalid price error has correct message."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert "price must be > 0" in r.json()["detail"]
    
    def test_not_found_error_has_detail(self):
        """Test that not found error includes detail."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()
    
    def test_not_found_error_message(self):
        """Test that not found error has correct message."""
        r = client.get("/items/999")
        assert "not found" in r.json()["detail"]
    
    def test_missing_field_error_returns_422(self):
        """Test that missing fields return 422."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422


class TestContentTypes:
    """Test response content types."""
    
    def test_create_item_returns_json(self, sample_item_data):
        """Test that create endpoint returns JSON."""
        r = client.post("/items", json=sample_item_data)
        assert r.headers["content-type"] == "application/json"
    
    def test_get_item_returns_json(self):
        """Test that get endpoint returns JSON."""
        r = client.get("/items/1")
        assert r.headers["content-type"] == "application/json"
    
    def test_health_returns_json(self):
        """Test that health endpoint returns JSON."""
        r = client.get("/health")
        assert r.headers["content-type"] == "application/json"


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_create_and_verify_response(self, sample_item_data):
        """Test creating an item and verifying the response."""
        r = client.post("/items", json=sample_item_data)
        assert r.status_code == 200
        
        data = r.json()
        assert data["name"] == sample_item_data["name"]
        assert data["price"] == sample_item_data["price"]
        assert "id" in data
    
    def test_multiple_items_different_prices(self):
        """Test creating multiple items with different prices."""
        items = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.50},
            {"name": "item3", "price": 100.0},
        ]
        
        for item in items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            assert r.json()["price"] == item["price"]
    
    def test_multiple_items_different_names(self):
        """Test creating multiple items with different names."""
        names = ["apple", "book", "computer", "diamond"]
        
        for name in names:
            r = client.post("/items", json={"name": name, "price": 50.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestParametrizedIntegration:
    """Parametrized integration tests for comprehensive coverage."""
    
    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.0, 999.99])
    def test_create_item_multiple_valid_prices(self, price):
        """Test creating items with various valid prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price
    
    @pytest.mark.parametrize("name", ["a", "test", "product name", "very long name with multiple words"])
    def test_create_item_multiple_valid_names(self, name):
        """Test creating items with various valid names."""
        r = client.post("/items", json={"name": name, "price": 50.0})
        assert r.status_code == 200
        assert r.json()["name"] == name
    
    @pytest.mark.parametrize("invalid_price", [-1, 0, -100, -0.01])
    def test_create_item_multiple_invalid_prices(self, invalid_price):
        """Test that various invalid prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": invalid_price})
        assert r.status_code == 400
    
    @pytest.mark.parametrize("item_id", [2, 5, 10, 999, 100000])
    def test_get_nonexistent_items(self, item_id):
        """Test getting various non-existent items."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestAPIConsistency:
    """Test consistency across multiple API calls."""
    
    def test_health_consistent(self):
        """Test that health endpoint returns consistent results."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.json() == r2.json()
    
    def test_get_item_1_consistent(self):
        """Test that getting item 1 returns consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        assert r1.json() == r2.json() == r3.json()
    
    def test_not_found_consistent(self):
        """Test that not found responses are consistent."""
        r1 = client.get("/items/999")
        r2 = client.get("/items/999")
        assert r1.status_code == r2.status_code == 404
        assert r1.json() == r2.json()


class TestStressScenarios:
    """Test API under stress scenarios."""
    
    def test_multiple_sequential_creates(self):
        """Test creating multiple items sequentially."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i) + 1})
            assert r.status_code == 200
    
    def test_multiple_sequential_gets(self):
        """Test getting item 1 multiple times."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
    
    def test_alternating_operations(self):
        """Test alternating create and get operations."""
        for i in range(5):
            # Create
            r1 = client.post("/items", json={"name": f"stress_item_{i}", "price": 50.0})
            assert r1.status_code == 200
            
            # Get
            r2 = client.get("/items/1")
            assert r2.status_code == 200
