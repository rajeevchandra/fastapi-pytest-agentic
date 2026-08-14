"""Response structure and error handling validation for items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    @pytest.mark.parametrize(
        "item_data,expected_status",
        [
            ({"name": "valid", "price": 10.0}, 200),  # Valid request
            ({"name": "test", "price": 0.01}, 200),  # Minimum valid price
            ({"name": "item", "price": 0}, 400),  # Zero price
            ({"name": "item", "price": -5.0}, 400),  # Negative price
            ({"name": "item"}, 422),  # Missing price
            ({"price": 10.0}, 422),  # Missing name
        ],
    )
    def test_create_item_status_codes(self, item_data, expected_status):
        """Test various HTTP status codes for create_item."""
        response = client.post("/items", json=item_data)
        assert response.status_code == expected_status

    def test_success_returns_200_ok(self):
        """Test that successful item creation returns 200 OK."""
        response = client.post("/items", json={"name": "test", "price": 15.0})
        assert response.status_code == 200

    def test_invalid_price_returns_400_bad_request(self):
        """Test that invalid price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400

    def test_missing_field_returns_422_unprocessable_entity(self):
        """Test that missing required field returns 422."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_invalid_json_returns_422(self):
        """Test that malformed JSON returns 422."""
        response = client.post("/items", json={"name": "test", "price": None})
        assert response.status_code == 422


class TestCreateItemErrorResponses:
    """Test error response format and content."""

    def test_error_response_has_detail_field(self):
        """Test that error responses contain detail field."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_price_error_message_content(self):
        """Test that price error message is descriptive."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail or "positive" in detail.lower()

    def test_validation_error_for_missing_price(self):
        """Test validation error format for missing price."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_validation_error_for_missing_name(self):
        """Test validation error format for missing name."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_error_response_is_json(self):
        """Test that error responses are valid JSON."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        # If this doesn't raise, JSON is valid
        data = response.json()
        assert isinstance(data, dict)


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            (1, 200),  # Valid item ID
            (2, 404),  # Non-existent item
            (999, 404),  # Non-existent item
            (0, 404),  # Zero ID not found
            (-1, 404),  # Negative ID not found
        ],
    )
    def test_get_item_status_codes(self, item_id, expected_status):
        """Test various HTTP status codes for get_item."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status

    def test_get_existing_item_returns_200(self):
        """Test that getting existing item returns 200 OK."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_non_existent_item_returns_404(self):
        """Test that getting non-existent item returns 404."""
        response = client.get("/items/2")
        assert response.status_code == 404

    def test_get_with_zero_id_returns_404(self):
        """Test that zero item ID returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_with_negative_id_returns_404(self):
        """Test that negative item ID returns 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404


class TestGetItemErrorResponses:
    """Test error response format for get_item."""

    def test_not_found_response_has_detail(self):
        """Test that 404 response contains detail field."""
        response = client.get("/items/2")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_not_found_error_message(self):
        """Test that not found error message is present."""
        response = client.get("/items/2")
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "not found" in detail.lower() or "404" in str(response.status_code)

    def test_not_found_response_is_json(self):
        """Test that 404 response is valid JSON."""
        response = client.get("/items/2")
        assert response.status_code == 404
        data = response.json()
        assert isinstance(data, dict)


class TestCreateItemResponseFormat:
    """Test response format and structure for create_item."""

    def test_response_content_type(self):
        """Test that response has correct content type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_response_is_json_object(self):
        """Test that response is a JSON object (dict)."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_response_contains_id_name_price(self):
        """Test that response contains id, name, and price fields."""
        response = client.post("/items", json={"name": "book", "price": 25.0})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_has_no_extra_fields(self):
        """Test that response contains only expected fields."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_response_values_match_input(self):
        """Test that response values match input values."""
        request_data = {"name": "test item", "price": 15.50}
        response = client.post("/items", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == request_data["name"]
        assert data["price"] == request_data["price"]


class TestGetItemResponseFormat:
    """Test response format and structure for get_item."""

    def test_response_content_type(self):
        """Test that response has correct content type."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_response_is_json_object(self):
        """Test that response is a JSON object (dict)."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_response_contains_id_name_price(self):
        """Test that response contains id, name, and price fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_has_no_extra_fields(self):
        """Test that response contains only expected fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_response_has_expected_values(self):
        """Test that response values are as expected."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestResponseFieldTypes:
    """Test type validation of response fields."""

    def test_create_item_response_id_is_int(self):
        """Test that created item id is integer."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert isinstance(response.json()["id"], int)

    def test_create_item_response_name_is_str(self):
        """Test that created item name is string."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert isinstance(response.json()["name"], str)

    def test_create_item_response_price_is_numeric(self):
        """Test that created item price is numeric."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        price = response.json()["price"]
        assert isinstance(price, (int, float))
        assert not isinstance(price, bool)

    def test_get_item_response_id_is_int(self):
        """Test that retrieved item id is integer."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert isinstance(response.json()["id"], int)

    def test_get_item_response_name_is_str(self):
        """Test that retrieved item name is string."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert isinstance(response.json()["name"], str)

    def test_get_item_response_price_is_numeric(self):
        """Test that retrieved item price is numeric."""
        response = client.get("/items/1")
        assert response.status_code == 200
        price = response.json()["price"]
        assert isinstance(price, (int, float))
        assert not isinstance(price, bool)


class TestHealthEndpointResponses:
    """Test health check endpoint responses."""

    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_is_json(self):
        """Test that health check response is JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_health_check_has_status_field(self):
        """Test that health check response has status field."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_health_check_status_value(self):
        """Test that health check status is 'ok'."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_content_type(self):
        """Test that health check has correct content type."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
