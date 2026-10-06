"""
Response validation and HTTP status code tests for all endpoints.

Tests response structure, status codes, and error handling for /items endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes returned by POST /items."""

    def test_successful_creation_returns_200(self):
        """Test that valid item creation returns 200."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        assert response.status_code == 200

    def test_invalid_price_returns_400(self):
        """Test that invalid price returns 400."""
        response = client.post(
            "/items", json={"name": "item", "price": -5.0}
        )
        assert response.status_code == 400

    def test_zero_price_returns_400(self):
        """Test that zero price returns 400."""
        response = client.post(
            "/items", json={"name": "item", "price": 0}
        )
        assert response.status_code == 400

    def test_missing_required_field_returns_422(self):
        """Test that missing required field returns 422."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422

    def test_invalid_type_returns_422(self):
        """Test that invalid type returns 422."""
        response = client.post(
            "/items", json={"name": "item", "price": "invalid"}
        )
        assert response.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes returned by GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [1])
    def test_existing_item_returns_200(self, item_id):
        """Test that GET for existing item returns 200."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "item_id",
        [0, -1, 2, 3, 99, 999, 100000],
    )
    def test_non_existing_item_returns_404(self, item_id):
        """Test that GET for non-existing item returns 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"


class TestGetItemResponseStructure:
    """Test response structure for GET /items/{item_id}."""

    def test_item_response_has_required_fields(self):
        """Test that item response contains all required fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_item_response_field_types(self):
        """Test that all fields have correct types."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_item_response_no_extra_fields(self):
        """Test that response only contains expected fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        expected_fields = {"id", "name", "price"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields

    def test_item_response_data_consistency(self):
        """Test that item data is consistent across requests."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        assert response1.json() == response2.json()


class TestErrorResponseFormat:
    """Test error response format and structure."""

    def test_400_error_has_detail_field(self):
        """Test that 400 error response has detail field."""
        response = client.post(
            "/items", json={"name": "item", "price": -1.0}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_404_error_has_detail_field(self):
        """Test that 404 error response has detail field."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_422_error_has_detail_field(self):
        """Test that 422 error response has detail field."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # 422 detail is a list of validation errors
        assert isinstance(data["detail"], list)

    def test_422_error_includes_field_location(self):
        """Test that 422 errors include field location."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0
        # Check that at least one error has 'loc' field
        assert any("loc" in error for error in errors)

    def test_price_validation_error_message(self):
        """Test price validation error message content."""
        response = client.post(
            "/items", json={"name": "item", "price": -10.0}
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "price must be > 0" in detail


class TestCreateItemResponseContent:
    """Test specific content of create_item response."""

    def test_response_reflects_input_name(self):
        """Test that response name matches input."""
        test_name = "BookProduct"
        response = client.post(
            "/items", json={"name": test_name, "price": 29.99}
        )
        assert response.status_code == 200
        assert response.json()["name"] == test_name

    def test_response_reflects_input_price(self):
        """Test that response price matches input."""
        test_price = 49.99
        response = client.post(
            "/items", json={"name": "item", "price": test_price}
        )
        assert response.status_code == 200
        assert response.json()["price"] == test_price

    def test_response_id_is_positive(self):
        """Test that response ID is positive integer."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        assert response.status_code == 200
        item_id = response.json()["id"]
        assert isinstance(item_id, int)
        assert item_id > 0

    @pytest.mark.parametrize("name", ["simple", "with spaces", "with-dash"])
    def test_various_names_preserved_in_response(self, name):
        """Test that various name formats are preserved."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.0, 999.99])
    def test_various_prices_preserved_in_response(self, price):
        """Test that various prices are preserved."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price


class TestContentTypeHeaders:
    """Test content-type headers in responses."""

    def test_create_item_response_content_type(self):
        """Test that create_item returns JSON content-type."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        assert response.headers["content-type"] == "application/json"

    def test_get_item_response_content_type(self):
        """Test that get_item returns JSON content-type."""
        response = client.get("/items/1")
        assert response.headers["content-type"] == "application/json"

    def test_error_response_content_type(self):
        """Test that error responses return JSON content-type."""
        response = client.get("/items/999")
        assert response.headers["content-type"] == "application/json"


class TestResponseConsistency:
    """Test consistency of responses across multiple requests."""

    def test_multiple_get_requests_same_response(self):
        """Test that multiple GET requests return identical data."""
        responses = [client.get("/items/1") for _ in range(3)]
        for resp in responses:
            assert resp.status_code == 200
        # All should have same content
        data = [resp.json() for resp in responses]
        assert all(d == data[0] for d in data)

    def test_get_invalid_id_always_returns_404(self):
        """Test that invalid IDs consistently return 404."""
        invalid_id = 999
        responses = [client.get(f"/items/{invalid_id}") for _ in range(3)]
        for resp in responses:
            assert resp.status_code == 404

    def test_invalid_price_always_returns_400(self):
        """Test that invalid price consistently returns 400."""
        responses = [
            client.post("/items", json={"name": "item", "price": -1.0})
            for _ in range(2)
        ]
        for resp in responses:
            assert resp.status_code == 400


class TestHTTPMethods:
    """Test handling of different HTTP methods on endpoints."""

    def test_get_on_items_endpoint_not_found(self):
        """Test that GET on /items returns 404 or method not allowed."""
        response = client.get("/items")
        # This endpoint doesn't have a GET handler
        assert response.status_code in [404, 405]

    def test_post_on_specific_item_not_found(self):
        """Test that POST on /items/1 returns 404 or method not allowed."""
        response = client.post(
            "/items/1", json={"name": "item", "price": 10.0}
        )
        # This endpoint doesn't have a POST handler
        assert response.status_code in [404, 405]

    def test_delete_on_items_not_found(self):
        """Test that DELETE on /items returns 404 or method not allowed."""
        response = client.delete("/items")
        assert response.status_code in [404, 405]

    def test_delete_on_specific_item_not_found(self):
        """Test that DELETE on /items/1 returns 404 or method not allowed."""
        response = client.delete("/items/1")
        assert response.status_code in [404, 405]


class TestRequestValidation:
    """Test request validation edge cases."""

    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        # TestClient automatically handles JSON parsing
        # This test verifies response to invalid content
        response = client.post(
            "/items",
            content="{invalid json}",
            headers={"content-type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_empty_request_body(self):
        """Test POST with empty body."""
        response = client.post("/items", json={})
        assert response.status_code == 422

    def test_post_with_no_content_type(self):
        """Test POST without explicit content-type."""
        # TestClient will use default
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        assert response.status_code == 200
