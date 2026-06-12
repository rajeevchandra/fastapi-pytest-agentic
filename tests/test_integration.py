import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestResponseHeaders:
    """Test HTTP response headers"""

    def test_create_item_response_headers(self):
        """Test that response includes proper headers"""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_get_item_response_headers(self):
        """Test that GET response includes proper headers"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_error_response_headers(self):
        """Test that error response includes proper headers"""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "content-type" in r.headers

    def test_validation_error_response_headers(self):
        """Test that validation error includes proper headers"""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "content-type" in r.headers


class TestResponseTypeValidation:
    """Test response type and structure validation"""

    def test_create_item_returns_dict(self):
        """Test that create_item returns a JSON object"""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_returns_dict(self):
        """Test that get_item returns a JSON object"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_error_response_returns_dict(self):
        """Test that error response is a JSON object"""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data, dict)

    def test_validation_error_returns_dict(self):
        """Test that validation error is a JSON object"""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        assert isinstance(data, dict)


class TestAPIIntegration:
    """Test end-to-end API interaction patterns"""

    def test_create_and_retrieve_item(self):
        """Test creating an item and then retrieving it"""
        # Create item
        create_response = client.post("/items", json={"name": "test book", "price": 15.99})
        assert create_response.status_code == 200
        created = create_response.json()
        
        # Retrieve the created item
        get_response = client.get(f"/items/{created['id']}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        
        # Verify retrieval succeeds (even though only id=1 is implemented)
        assert retrieved["id"] == created["id"]

    def test_multiple_create_requests(self):
        """Test making multiple create requests"""
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["price"] == 10.0 + i

    def test_multiple_get_requests(self):
        """Test making multiple GET requests"""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1

    def test_invalid_create_then_valid_create(self):
        """Test invalid request followed by valid request"""
        # Invalid request
        r1 = client.post("/items", json={"price": 10.0})
        assert r1.status_code == 422
        
        # Valid request
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200


class TestResponseConsistency:
    """Test consistency of API responses"""

    def test_create_response_id_always_one(self):
        """Test that create always returns id=1"""
        for _ in range(3):
            r = client.post("/items", json={"name": "test", "price": 10.0})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1

    def test_create_response_includes_all_fields(self):
        """Test that create response includes name, price, and id"""
        r = client.post("/items", json={"name": "test", "price": 15.50})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_response_consistent(self):
        """Test that GET /items/1 response is consistent"""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()


class TestHealthEndpoint:
    """Test the health check endpoint"""

    def test_health_endpoint_exists(self):
        """Test that health endpoint responds"""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_endpoint_returns_ok(self):
        """Test that health endpoint returns ok status"""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_health_endpoint_response_structure(self):
        """Test health endpoint response structure"""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data


class TestParametrizedIntegration:
    """Parametrized integration tests"""

    @pytest.mark.parametrize("name,price", [
        ("book", 12.99),
        ("pen", 0.99),
        ("laptop", 999.99),
        ("notebook", 5.50),
        ("monitor", 199.00),
    ])
    def test_create_with_various_items(self, name, price):
        """Test creating various items"""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1

    @pytest.mark.parametrize("endpoint", [
        ("/health", "GET", None, 200),
        ("/items/1", "GET", None, 200),
        ("/items", "POST", {"name": "test", "price": 10.0}, 200),
    ])
    def test_various_endpoints(self, endpoint):
        """Test various API endpoints"""
        path, method, json_data, expected_status = endpoint
        if method == "GET":
            r = client.get(path)
        else:
            r = client.post(path, json=json_data)
        assert r.status_code == expected_status

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (999, 404),
    ])
    def test_get_item_various_ids(self, item_id, expected_status):
        """Test GET with various item IDs"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestFixtures:
    """Test suite with fixtures for better organization"""

    @pytest.fixture
    def valid_item_data(self):
        """Fixture providing valid item data"""
        return {"name": "test item", "price": 25.50}

    @pytest.fixture
    def invalid_item_missing_name(self):
        """Fixture providing item data missing name"""
        return {"price": 10.0}

    @pytest.fixture
    def invalid_item_zero_price(self):
        """Fixture providing item data with zero price"""
        return {"name": "test", "price": 0}

    def test_create_with_valid_fixture(self, valid_item_data):
        """Test creating item with valid fixture"""
        r = client.post("/items", json=valid_item_data)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == valid_item_data["name"]
        assert data["price"] == valid_item_data["price"]

    def test_create_with_invalid_fixture_missing_name(self, invalid_item_missing_name):
        """Test creating item with invalid fixture (missing name)"""
        r = client.post("/items", json=invalid_item_missing_name)
        assert r.status_code == 422

    def test_create_with_invalid_fixture_zero_price(self, invalid_item_zero_price):
        """Test creating item with invalid fixture (zero price)"""
        r = client.post("/items", json=invalid_item_zero_price)
        assert r.status_code == 400


class TestErrorMessages:
    """Test error message clarity and consistency"""

    def test_price_validation_error_message(self):
        """Test that price validation error has clear message"""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        error = r.json()
        assert "detail" in error
        assert "price" in error["detail"].lower()
        assert "0" in error["detail"]

    def test_missing_field_error_response(self):
        """Test that missing field error is in proper format"""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        error = r.json()
        assert "detail" in error

    def test_not_found_error_message(self):
        """Test that not found error has clear message"""
        r = client.get("/items/999")
        assert r.status_code == 404
        error = r.json()
        assert error["detail"] == "not found"
