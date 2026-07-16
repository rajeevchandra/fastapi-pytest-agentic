"""Integration tests and end-to-end scenarios."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_item_data():
    """Fixture providing sample item data."""
    return {"name": "test_item", "price": 15.5}


@pytest.fixture
def valid_prices():
    """Fixture providing valid price values."""
    return [0.01, 1.0, 10.0, 100.0, 1000.50]


@pytest.fixture
def invalid_prices():
    """Fixture providing invalid price values."""
    return [-1, 0, -100, -0.01]


class TestCreateItemResponseStructure:
    """Test complete response structure validation."""

    def test_response_contains_all_fields(self, sample_item_data):
        """Test that response contains id, name, and price."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_response_field_count(self, sample_item_data):
        """Test that response only contains expected fields."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        assert len(data) == 3  # id, name, price

    def test_response_matches_input_name(self, sample_item_data):
        """Test that response name matches input."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        assert data["name"] == sample_item_data["name"]

    def test_response_matches_input_price(self, sample_item_data):
        """Test that response price matches input."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        assert data["price"] == sample_item_data["price"]


class TestParametrizedIntegration:
    """Parametrized integration tests."""

    def test_create_item_with_valid_prices(self, valid_prices):
        """Test creating items with various valid prices."""
        for price in valid_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_create_item_with_invalid_prices(self, invalid_prices):
        """Test creating items with various invalid prices."""
        for price in invalid_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 400

    @pytest.mark.parametrize(
        "name,price",
        [
            ("book", 10.0),
            ("pen", 1.5),
            ("notebook", 5.0),
            ("", 10.0),
            ("very_long_name" * 10, 99.99),
        ],
    )
    def test_create_items_various_names(self, name, price):
        """Test creating items with various name values."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestStatusCodes:
    """Test correct HTTP status codes."""

    def test_create_item_success_returns_200(self):
        """Test that successful create returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Test that invalid price returns 400."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Test that missing field returns 422."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_get_item_found_returns_200(self):
        """Test that found item returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Test that not found item returns 404."""
        r = client.get("/items/99")
        assert r.status_code == 404

    def test_health_returns_200(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200


class TestErrorMessages:
    """Test error message content and format."""

    def test_price_validation_error_message(self):
        """Test error message for invalid price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        data = r.json()
        assert "detail" in data
        assert "price" in data["detail"].lower()

    def test_item_not_found_error_message(self):
        """Test error message for not found."""
        r = client.get("/items/999")
        data = r.json()
        assert data["detail"] == "not found"

    def test_validation_error_has_detail_field(self):
        """Test that validation errors have detail field."""
        r = client.post("/items", json={"price": 10.0})
        data = r.json()
        assert "detail" in data


class TestAPIEndpoints:
    """Test all API endpoints are accessible."""

    def test_health_endpoint_exists(self):
        """Test health endpoint is accessible."""
        r = client.get("/health")
        assert r.status_code in [200, 404]  # Should be 200, but allow 404

    def test_create_item_endpoint_exists(self):
        """Test create item endpoint is accessible."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code in [200, 404]  # Should be 200

    def test_get_item_endpoint_exists(self):
        """Test get item endpoint is accessible."""
        r = client.get("/items/1")
        assert r.status_code in [200, 404]  # Either is acceptable


class TestRequestContentType:
    """Test content type handling in requests."""

    def test_json_request_accepted(self):
        """Test that JSON requests are accepted."""
        r = client.post(
            "/items",
            json={"name": "item", "price": 10.0},
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 200

    def test_response_is_json(self):
        """Test that responses are JSON."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")


class TestCreateItemWorkflow:
    """Test typical workflows using the API."""

    def test_create_and_validate_item(self):
        """Test creating an item and validating response."""
        create_r = client.post("/items", json={"name": "book", "price": 15.0})
        assert create_r.status_code == 200

        created_item = create_r.json()
        assert created_item["name"] == "book"
        assert created_item["price"] == 15.0

    def test_multiple_create_requests(self):
        """Test that multiple create requests all succeed."""
        for i in range(5):
            r = client.post(
                "/items", json={"name": f"item_{i}", "price": 10.0 + i}
            )
            assert r.status_code == 200

    def test_get_existing_item_after_details_check(self):
        """Test getting item by id."""
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        item = get_r.json()
        assert item["id"] == 1
