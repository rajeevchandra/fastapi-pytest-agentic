"""
Integration tests and end-to-end scenarios for API.
Tests verify response structures, headers, and interaction patterns.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_item_data():
    """Fixture providing sample item data."""
    return {"name": "Test Item", "price": 15.5}


@pytest.fixture
def created_item(sample_item_data):
    """Fixture that creates an item and returns the response."""
    response = client.post("/items", json=sample_item_data)
    return response.json()


@pytest.fixture
def valid_prices():
    """Fixture providing valid price values."""
    return [0.01, 1.0, 10.0, 100.5, 9999.99]


@pytest.fixture
def invalid_prices():
    """Fixture providing invalid price values."""
    return [0, -1, -10.5, -0.01, -9999.99]


class TestCreateItemResponseStructure:
    """Test the structure of successful POST responses."""

    def test_create_item_response_has_required_fields(self, sample_item_data):
        """Test that response contains all required fields."""
        response = client.post("/items", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_no_extra_fields(self, sample_item_data):
        """Test that response contains only expected fields."""
        response = client.post("/items", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_response_field_types(self, sample_item_data):
        """Test that response fields have correct types."""
        response = client.post("/items", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_preserves_input_data(self, sample_item_data):
        """Test that created item preserves input name and price."""
        response = client.post("/items", json=sample_item_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_item_data["name"]
        assert data["price"] == sample_item_data["price"]


class TestCreateItemHTTPHeaders:
    """Test HTTP headers in responses."""

    def test_create_item_returns_200_status(self, sample_item_data):
        """Test successful POST returns 200 status code."""
        response = client.post("/items", json=sample_item_data)
        assert response.status_code == 200

    def test_create_item_content_type_is_json(self, sample_item_data):
        """Test response content-type is application/json."""
        response = client.post("/items", json=sample_item_data)
        assert "application/json" in response.headers["content-type"]

    def test_create_item_error_response_content_type(self):
        """Test error response also has JSON content-type."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        assert "application/json" in response.headers["content-type"]

    def test_validation_error_response_content_type(self):
        """Test validation error has JSON content-type."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        assert "application/json" in response.headers["content-type"]


class TestParametrizedIntegration:
    """Parametrized tests for comprehensive scenario coverage."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.5, 9999.99])
    def test_create_and_get_items_with_valid_prices(self, price):
        """Test creating items with various valid prices."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        item = response.json()
        assert item["price"] == price

    @pytest.mark.parametrize("price", [0, -1, -10.5])
    def test_create_items_with_invalid_prices_rejected(self, price):
        """Test that invalid prices are rejected."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.parametrize("name", ["book", "a", "test item", "Product-123"])
    def test_create_items_with_various_names(self, name):
        """Test creating items with different names."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name

    @pytest.mark.parametrize("item_id", [1, 2, 0, -1, 999])
    def test_get_items_various_ids(self, item_id):
        """Test getting items with various IDs."""
        response = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert response.status_code == 200
        else:
            assert response.status_code == 404


class TestResponseStatusCodes:
    """Test various HTTP status codes across scenarios."""

    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_create_item_success_returns_200(self, sample_item_data):
        """Test successful create returns 200."""
        response = client.post("/items", json=sample_item_data)
        assert response.status_code == 200

    def test_create_item_validation_error_returns_422(self):
        """Test create with missing fields returns 422."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_create_item_business_error_returns_400(self):
        """Test create with invalid price returns 400."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_get_item_success_returns_200(self):
        """Test successful get returns 200."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Test get non-existent item returns 404."""
        response = client.get("/items/999")
        assert response.status_code == 404

    def test_get_item_invalid_id_type_returns_422(self):
        """Test get with invalid path parameter returns 422."""
        response = client.get("/items/abc")
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling and error messages."""

    def test_invalid_price_error_detail_message(self):
        """Test error message for invalid price."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_not_found_error_detail_message(self):
        """Test error message for not found."""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_validation_error_has_detail(self):
        """Test that validation errors include detail."""
        response = client.post("/items", json={})
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_invalid_json_error_response(self):
        """Test handling of invalid JSON."""
        response = client.post(
            "/items",
            content=b"invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestItemCreationSequence:
    """Test sequences of API calls."""

    def test_create_item_then_retrieve_it(self):
        """Test creating an item and then retrieving it."""
        create_response = client.post(
            "/items",
            json={"name": "Laptop", "price": 999.99}
        )
        assert create_response.status_code == 200
        created = create_response.json()
        
        get_response = client.get(f"/items/{created['id']}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["id"] == created["id"]

    def test_multiple_create_requests_succeed(self):
        """Test multiple create requests in sequence."""
        items_data = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        
        for item_data in items_data:
            response = client.post("/items", json=item_data)
            assert response.status_code == 200
            assert response.json()["name"] == item_data["name"]

    def test_retrieve_after_failed_create_still_works(self):
        """Test that failed create doesn't break subsequent retrieval."""
        # Attempt failed create
        failed_response = client.post("/items", json={"name": "test", "price": -1})
        assert failed_response.status_code == 400
        
        # Retrieval should still work
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == 1
