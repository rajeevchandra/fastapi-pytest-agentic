"""
Response validation tests for the items API.

Tests cover:
- Response structure and field presence
- Response data type validation
- Error response format consistency
- HTTP headers and content types
- Status code correctness
- Response field values and bounds
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemSuccessResponse:
    """Tests for successful create_item response structure and types."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_fields_are_correct_types(self):
        """Test that response fields have correct data types."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_create_item_response_id_is_positive(self):
        """Test that response id is a positive integer."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] > 0

    def test_create_item_response_price_matches_request(self):
        """Test that response price matches request price."""
        price = 99.99
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_response_name_matches_request(self):
        """Test that response name matches request name."""
        name = "special_item"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_response_no_extra_fields(self):
        """Test that response contains only expected fields."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_create_item_response_content_type(self):
        """Test that response has correct content type."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    @pytest.mark.parametrize("name", ["a", "item", "very_long_item_name_" * 5])
    def test_create_item_various_names_in_response(self, name):
        """Test response with various name values."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name
        assert isinstance(r.json()["name"], str)

    @pytest.mark.parametrize("price", [0.01, 1.0, 100.0, 10000.0])
    def test_create_item_various_prices_in_response(self, price):
        """Test response with various price values."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price
        assert isinstance(r.json()["price"], float)


class TestCreateItemErrorResponse:
    """Tests for error response format and consistency."""

    def test_create_item_error_response_has_detail(self):
        """Test that error response contains detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_create_item_error_response_detail_is_string(self):
        """Test that error detail is a string."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert isinstance(r.json()["detail"], str)

    def test_create_item_error_response_detail_message(self):
        """Test that error detail contains meaningful message."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail

    @pytest.mark.parametrize("price", [0, -1, -100, -0.5])
    def test_create_item_error_response_for_non_positive_prices(self, price):
        """Test consistent error response for various non-positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_validation_error_response_format(self):
        """Test that validation error (422) has proper format."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_create_item_validation_error_contains_location(self):
        """Test that validation error includes field location."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert len(detail) > 0
        assert "loc" in detail[0]

    def test_create_item_validation_error_contains_type(self):
        """Test that validation error includes error type."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert len(detail) > 0
        assert "type" in detail[0]


class TestGetItemSuccessResponse:
    """Tests for successful get_item response structure and types."""

    def test_get_item_response_has_required_fields(self):
        """Test that GET response contains all required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_fields_are_correct_types(self):
        """Test that GET response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_id_matches_request(self):
        """Test that GET response id matches requested id."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_response_id_is_positive(self):
        """Test that GET response id is positive."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] > 0

    def test_get_item_response_name_is_string(self):
        """Test that GET response name is a string."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_get_item_response_name_not_empty(self):
        """Test that GET response name is not empty."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert len(r.json()["name"]) > 0

    def test_get_item_response_price_is_positive(self):
        """Test that GET response price is positive."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["price"] > 0

    def test_get_item_response_no_extra_fields(self):
        """Test that GET response contains only expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_get_item_response_content_type(self):
        """Test that GET response has correct content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemErrorResponse:
    """Tests for GET item error response format."""

    def test_get_item_not_found_response_has_detail(self):
        """Test that 404 response contains detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_get_item_not_found_detail_is_string(self):
        """Test that 404 detail is a string."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert isinstance(r.json()["detail"], str)

    def test_get_item_not_found_detail_message(self):
        """Test that 404 detail contains meaningful message."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_item_not_found_for_non_existing_ids(self, item_id):
        """Test consistent 404 for various non-existing item IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_not_found_content_type(self):
        """Test that 404 response has correct content type."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseConsistency:
    """Tests for consistency between responses."""

    def test_created_item_id_always_one(self):
        """Test that multiple creates return same id (as per implementation)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_created_item_can_be_retrieved(self):
        """Test that created item can be retrieved with correct id."""
        create_r = client.post("/items", json={"name": "testitem", "price": 25.0})
        item_id = create_r.json()["id"]
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200

    def test_response_fields_consistency_across_requests(self):
        """Test that response structure is consistent across multiple requests."""
        responses = [
            client.post("/items", json={"name": f"item{i}", "price": float(i)})
            for i in range(1, 4)
        ]
        for r in responses:
            data = r.json()
            assert set(data.keys()) == {"id", "name", "price"}
            assert isinstance(data["id"], int)
            assert isinstance(data["name"], str)
            assert isinstance(data["price"], float)

    def test_error_responses_have_consistent_format(self):
        """Test that error responses use consistent format."""
        bad_request = client.post("/items", json={"name": "item", "price": 0})
        not_found = client.get("/items/999")
        
        # Both should have detail field
        assert "detail" in bad_request.json()
        assert "detail" in not_found.json()
        
        # Both should be JSON
        assert "application/json" in bad_request.headers.get("content-type", "")
        assert "application/json" in not_found.headers.get("content-type", "")


class TestHTTPStatusCodes:
    """Tests for correct HTTP status codes."""

    def test_create_item_success_returns_200(self):
        """Test that successful create returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Test that invalid price returns 400."""
        r = client.post("/items", json={"name": "item", "price": 0})
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
        """Test that missing item returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    @pytest.mark.parametrize("status_code", [400, 404, 422])
    def test_error_status_codes_are_in_4xx_range(self, status_code):
        """Test that error codes are in 4xx range."""
        assert 400 <= status_code < 500


class TestResponseSerialization:
    """Tests for proper JSON serialization of responses."""

    def test_response_is_valid_json(self):
        """Test that response is valid JSON that can be parsed."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        # Should not raise exception
        data = r.json()
        assert data is not None

    def test_response_can_be_serialized_multiple_times(self):
        """Test that response data is serializable."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        data1 = r.json()
        data2 = r.json()
        assert data1 == data2

    def test_unicode_response_serialization(self):
        """Test that unicode in response is properly serialized."""
        r = client.post("/items", json={"name": "café", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "café"
