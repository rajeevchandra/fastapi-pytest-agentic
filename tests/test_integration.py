import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def api_client():
    """Provide test client for integration tests"""
    return client


class TestHealthEndpoint:
    """Test health endpoint"""

    def test_health_returns_ok_status(self):
        """Test health endpoint returns ok status"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self):
        """Test health response has correct structure"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_content_type(self):
        """Test health response content type"""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


class TestItemsEndpointIntegration:
    """Integration tests for items endpoints"""

    def test_create_and_retrieve_item(self):
        """Test creating an item and then retrieving it"""
        # Create item
        create_response = client.post("/items", json={"name": "test_item", "price": 25.0})
        assert create_response.status_code == 200
        created_data = create_response.json()
        assert created_data["name"] == "test_item"
        assert created_data["price"] == 25.0

        # Retrieve item
        get_response = client.get(f"/items/{created_data['id']}")
        assert get_response.status_code == 200

    def test_create_multiple_items_same_price(self):
        """Test creating multiple items with same price"""
        test_price = 50.0
        for i in range(3):
            response = client.post("/items", json={"name": f"item_{i}", "price": test_price})
            assert response.status_code == 200
            assert response.json()["price"] == test_price

    @pytest.mark.parametrize("price", [1.0, 10.5, 99.99])
    def test_create_items_different_prices(self, price):
        """Test creating items with various prices"""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price

    @pytest.mark.parametrize("name", ["Product A", "Item-1", "测试商品", "🎁 Gift"])
    def test_create_items_different_names(self, name):
        """Test creating items with various names"""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_endpoints_independent(self):
        """Test that POST and GET endpoints work independently"""
        # First, test POST works
        post_response = client.post("/items", json={"name": "test1", "price": 5.0})
        assert post_response.status_code == 200

        # Then test GET works for existing item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

        # And GET fails for non-existent item
        get_404_response = client.get("/items/999")
        assert get_404_response.status_code == 404


class TestErrorResponseConsistency:
    """Test error response format and consistency"""

    def test_validation_error_response_format(self):
        """Test validation error response has expected format"""
        response = client.post("/items", json={"price": 10.0})  # missing name
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_business_logic_error_format(self):
        """Test business logic error response format"""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_not_found_error_format(self):
        """Test not found error response format"""
        response = client.get("/items/9999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.parametrize("error_status", [400, 404, 422])
    def test_error_responses_have_detail_field(self, error_status):
        """Test all error responses include detail field"""
        if error_status == 400:
            response = client.post("/items", json={"name": "test", "price": 0})
        elif error_status == 404:
            response = client.get("/items/999")
        else:  # 422
            response = client.post("/items", json={"name": "test"})

        assert response.status_code == error_status
        assert "detail" in response.json()


class TestRequestHeaders:
    """Test handling of various request headers"""

    def test_post_with_content_type_json(self):
        """Test POST request with explicit JSON content type"""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.0},
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 200

    def test_get_with_various_accepts(self):
        """Test GET request with Accept header"""
        response = client.get("/items/1", headers={"accept": "application/json"})
        assert response.status_code == 200

    def test_response_headers_present(self):
        """Test that response includes expected headers"""
        response = client.get("/items/1")
        assert "content-type" in response.headers
        assert "content-length" in response.headers or "transfer-encoding" in response.headers


class TestStressScenarios:
    """Test API behavior under stress"""

    def test_many_successful_requests(self):
        """Test multiple successful requests in sequence"""
        for i in range(10):
            response = client.post("/items", json={"name": f"item{i}", "price": float(i)})
            if i == 0:
                assert response.status_code == 200

    def test_many_requests_with_errors(self):
        """Test multiple error requests"""
        for i in range(10):
            response = client.post("/items", json={"name": "test", "price": -float(i+1)})
            assert response.status_code == 400

    def test_alternating_success_and_error(self):
        """Test alternating between valid and invalid requests"""
        for i in range(10):
            if i % 2 == 0:
                response = client.post("/items", json={"name": f"item{i}", "price": 10.0})
                assert response.status_code == 200
            else:
                response = client.post("/items", json={"name": f"item{i}", "price": 0})
                assert response.status_code == 400

    def test_many_get_requests_same_id(self):
        """Test many GET requests for the same item"""
        for _ in range(10):
            response = client.get("/items/1")
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_many_get_requests_different_ids(self):
        """Test many GET requests for different items"""
        for i in range(2, 12):
            response = client.get(f"/items/{i}")
            assert response.status_code == 404


class TestParametrizedIntegration:
    """Parametrized integration test scenarios"""

    @pytest.mark.parametrize("test_data", [
        {"name": "book", "price": 15.99},
        {"name": "pen", "price": 1.50},
        {"name": "notebook", "price": 5.00},
        {"name": "keyboard", "price": 150.00},
    ])
    def test_create_various_items(self, test_data):
        """Test creating various realistic items"""
        response = client.post("/items", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_data["name"]
        assert data["price"] == test_data["price"]

    @pytest.mark.parametrize("invalid_data", [
        {"name": "test"},
        {"price": 10.0},
        {"name": "test", "price": "invalid"},
        {"name": 123, "price": 10.0},
        {},
    ])
    def test_create_with_invalid_data(self, invalid_data):
        """Test creating items with various invalid data"""
        response = client.post("/items", json=invalid_data)
        assert response.status_code in [400, 422]

    @pytest.mark.parametrize("status_codes_for_ids", [
        (1, 200),
        (2, 404),
        (999, 404),
        (0, 404),
        (-1, 404),
    ])
    def test_get_various_ids(self, status_codes_for_ids):
        """Test getting items with various IDs"""
        item_id, expected_status = status_codes_for_ids
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status


class TestStatusCodes:
    """Test all HTTP status codes used by API"""

    def test_success_200_on_valid_post(self):
        """Test 200 status on valid POST"""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200

    def test_success_200_on_valid_get(self):
        """Test 200 status on valid GET"""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_success_200_on_health(self):
        """Test 200 status on health check"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_error_400_on_business_logic_violation(self):
        """Test 400 status on business logic error"""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_error_404_on_not_found(self):
        """Test 404 status when item not found"""
        response = client.get("/items/999")
        assert response.status_code == 404

    def test_error_422_on_validation_failure(self):
        """Test 422 status on validation error"""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_error_422_on_invalid_path_parameter(self):
        """Test 422 status on invalid path parameter"""
        response = client.get("/items/notanumber")
        assert response.status_code == 422
