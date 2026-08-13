"""
Response structure, error handling, and HTTP status code validation.

Tests cover:
- HTTP status codes for all scenarios
- Response body structure and format
- Error response consistency
- Content type validation
- Response field types and presence
- Error message clarity and consistency
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for item creation."""

    @pytest.mark.parametrize("name,price,expected_status", [
        ("valid", 10.0, 200),          # Normal case
        ("book", 0.01, 200),           # Minimum valid price
        ("item", 999999.99, 200),      # Large price
        ("test", 0, 400),              # Zero price
        ("item", -5, 400),             # Negative price
        ("test", -100.50, 400),        # Large negative
    ])
    def test_create_item_status_codes(self, name, price, expected_status):
        """Test various scenarios return correct HTTP status codes."""
        response = client.post("/items", json={"name": name, "price": price})
        assert response.status_code == expected_status

    def test_create_item_missing_name_returns_422(self):
        """Verify missing required field returns 422 Unprocessable Entity."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422

    def test_create_item_missing_price_returns_422(self):
        """Verify missing price returns 422."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_create_item_empty_payload_returns_422(self):
        """Verify empty JSON returns 422."""
        response = client.post("/items", json={})
        assert response.status_code == 422

    def test_create_item_success_returns_200(self):
        """Verify successful creation returns 200 OK."""
        response = client.post("/items", json={"name": "book", "price": 15.0})
        assert response.status_code == 200

    def test_create_item_zero_price_returns_400(self):
        """Verify zero price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400

    def test_create_item_negative_price_returns_400(self):
        """Verify negative price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "item", "price": -10})
        assert response.status_code == 400


class TestCreateItemResponseStructure:
    """Test response body structure for item creation."""

    def test_create_item_response_has_required_fields(self):
        """Verify response contains all required fields."""
        response = client.post("/items", json={"name": "book", "price": 20.0})
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data, "Response missing 'id' field"
        assert "name" in data, "Response missing 'name' field"
        assert "price" in data, "Response missing 'price' field"

    def test_create_item_response_has_exact_three_fields(self):
        """Verify response has exactly 3 fields (id, name, price)."""
        response = client.post("/items", json={"name": "widget", "price": 5.0})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3, f"Expected 3 fields, got {len(data)}"
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_response_field_types(self):
        """Verify response fields have correct types."""
        response = client.post("/items", json={"name": "test", "price": 12.50})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["id"], int), "id should be integer"
        assert isinstance(data["name"], str), "name should be string"
        assert isinstance(data["price"], (int, float)), "price should be numeric"

    def test_create_item_returns_expected_values(self):
        """Verify response contains submitted values."""
        test_name = "TestBook"
        test_price = 19.99
        response = client.post("/items", json={"name": test_name, "price": test_price})
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == test_name
        assert data["price"] == test_price

    def test_create_item_id_is_always_one(self):
        """Verify created items always get id=1 (current behavior)."""
        response = client.post("/items", json={"name": "first", "price": 10.0})
        assert response.json()["id"] == 1
        
        response = client.post("/items", json={"name": "second", "price": 20.0})
        assert response.json()["id"] == 1

    def test_create_item_preserves_name_exactly(self):
        """Verify name is returned exactly as submitted."""
        names = ["Simple", "With Spaces", "With-Dashes", "123Numbers", "special!@#$"]
        for name in names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            assert response.json()["name"] == name

    def test_create_item_preserves_price_exactly(self):
        """Verify price is returned exactly as submitted."""
        prices = [0.01, 1.0, 9.99, 100.50, 999999.99]
        for price in prices:
            response = client.post("/items", json={"name": "item", "price": price})
            assert response.json()["price"] == price


class TestCreateItemErrorHandling:
    """Test error responses and error message consistency."""

    def test_create_item_error_response_has_detail(self):
        """Verify error responses include a detail field."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_create_item_price_error_message_clear(self):
        """Verify price error message is clear and helpful."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        
        detail = response.json()["detail"]
        assert "price" in detail.lower()
        assert "must be > 0" in detail or "greater than" in detail.lower()

    def test_create_item_validation_error_has_detail(self):
        """Verify validation errors include detail array."""
        response = client.post("/items", json={"price": 10.0})  # missing name
        assert response.status_code == 422
        
        error = response.json()
        assert "detail" in error
        # FastAPI returns detail as a list of validation errors
        assert isinstance(error["detail"], list)

    def test_create_item_null_price_error(self):
        """Verify null price produces proper error."""
        response = client.post("/items", json={"name": "item", "price": None})
        assert response.status_code == 422
        
        error = response.json()
        assert "detail" in error

    def test_create_item_string_price_handling(self):
        """Verify non-numeric string price is handled properly."""
        response = client.post("/items", json={"name": "item", "price": "not_a_number"})
        assert response.status_code == 422

    def test_create_item_error_response_is_json(self):
        """Verify error responses are valid JSON."""
        response = client.post("/items", json={"name": "item", "price": -1})
        assert response.status_code == 400
        
        try:
            data = response.json()
            assert isinstance(data, dict)
        except Exception as e:
            pytest.fail(f"Error response is not valid JSON: {e}")


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for item retrieval."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),    # Existing item
        (2, 404),    # Non-existent item
        (0, 404),    # Zero ID
        (-1, 404),   # Negative ID
        (999, 404),  # Large ID
    ])
    def test_get_item_status_codes(self, item_id, expected_status):
        """Test various item IDs return correct status codes."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status

    def test_get_item_found_returns_200(self):
        """Verify existing item returns 200 OK."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Verify non-existent item returns 404 Not Found."""
        response = client.get("/items/2")
        assert response.status_code == 404

    def test_get_item_zero_id_returns_404(self):
        """Verify item_id=0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_negative_id_returns_404(self):
        """Verify negative item_id returns 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_get_item_large_id_returns_404(self):
        """Verify very large item_id returns 404."""
        response = client.get("/items/999999999")
        assert response.status_code == 404


class TestGetItemResponseStructure:
    """Test response structure for item retrieval."""

    def test_get_item_response_has_required_fields(self):
        """Verify GET response includes all required fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Verify GET response fields have correct types."""
        response = client.get("/items/1")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_values(self):
        """Verify GET response returns sample data."""
        response = client.get("/items/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_not_found_error_structure(self):
        """Verify 404 error response has proper structure."""
        response = client.get("/items/999")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_get_item_not_found_error_message(self):
        """Verify 404 error has clear message."""
        response = client.get("/items/2")
        assert response.status_code == 404
        
        detail = response.json()["detail"]
        assert "not found" in detail.lower() or "404" in detail


class TestContentTypeValidation:
    """Test Content-Type headers in responses."""

    def test_create_item_response_is_json(self):
        """Verify POST response is JSON."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_item_response_is_json(self):
        """Verify GET response is JSON."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_error_response_is_json(self):
        """Verify error responses are JSON."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")

    def test_validation_error_response_is_json(self):
        """Verify validation error responses are JSON."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        assert "application/json" in response.headers.get("content-type", "")


class TestResponseConsistency:
    """Test consistency across different scenarios."""

    def test_create_and_get_have_same_field_structure(self):
        """Verify POST and GET responses have same fields."""
        post_response = client.post("/items", json={"name": "test", "price": 15.0})
        get_response = client.get("/items/1")
        
        post_fields = set(post_response.json().keys())
        get_fields = set(get_response.json().keys())
        assert post_fields == get_fields == {"id", "name", "price"}

    def test_multiple_create_responses_have_consistent_structure(self):
        """Verify multiple POSTs return consistently formatted responses."""
        responses = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            responses.append(r.json())
        
        # All responses should have same fields
        fields = [set(r.keys()) for r in responses]
        assert all(f == fields[0] for f in fields)

    def test_error_responses_have_consistent_structure(self):
        """Verify error responses consistently include detail."""
        responses = [
            client.post("/items", json={"name": "test", "price": 0}),     # 400
            client.post("/items", json={"price": 10.0}),                  # 422
            client.get("/items/999"),                                      # 404
        ]
        
        for response in responses:
            assert response.status_code >= 400
            data = response.json()
            assert "detail" in data, f"Missing detail in {response.status_code} response"


class TestHTTPMethods:
    """Test HTTP method validation."""

    def test_items_post_endpoint_accepts_post(self):
        """Verify POST method is accepted."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code in [200, 400, 422]  # Valid responses

    def test_items_get_endpoint_accepts_get(self):
        """Verify GET method is accepted."""
        response = client.get("/items/1")
        assert response.status_code in [200, 404]  # Valid responses

    def test_items_endpoint_exists_and_is_callable(self):
        """Verify items endpoints are properly defined."""
        # Test that endpoints exist and are callable
        post_response = client.post("/items", json={"name": "test", "price": 10.0})
        get_response = client.get("/items/1")
        
        assert post_response.status_code != 404
        assert get_response.status_code != 404
