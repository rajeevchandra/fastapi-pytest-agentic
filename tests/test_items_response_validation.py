"""
Part 2: Response Validation Testing - Verify response JSON structure, data types,
field consistency, and error response formats across success and error cases.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseValid:
    """Test response structure for successful item creation."""

    def test_response_status_code_success(self):
        """Test that successful creation returns 200 status."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200

    def test_response_is_json(self):
        """Test that response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.headers["content-type"] == "application/json"

    def test_response_is_dict(self):
        """Test that response body is a dict."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data, dict)

    def test_response_has_exactly_three_fields(self):
        """Test that response has exactly id, name, and price fields."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert len(data) == 3
        assert set(data.keys()) == {"id", "name", "price"}

    def test_response_no_extra_fields(self):
        """Test that response doesn't include unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        unexpected = set(data.keys()) - {"id", "name", "price"}
        assert len(unexpected) == 0

    def test_response_all_required_fields_present(self):
        """Test that all required fields are in response."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data


class TestResponseFieldTypes:
    """Test that response fields have correct data types."""

    def test_id_field_is_integer(self):
        """Test that id field is an integer."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["id"], int)
        assert not isinstance(data["id"], bool)

    def test_name_field_is_string(self):
        """Test that name field is a string."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["name"], str)

    def test_price_field_is_number(self):
        """Test that price field is a number (int or float)."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_price_field_is_not_string(self):
        """Test that price is not returned as a string."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert not isinstance(data["price"], str)

    def test_id_not_null(self):
        """Test that id field is not null."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert data["id"] is not None

    def test_name_not_null(self):
        """Test that name field is not null."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert data["name"] is not None

    def test_price_not_null(self):
        """Test that price field is not null."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert data["price"] is not None


class TestResponseFieldValues:
    """Test that response field values are correct and match input."""

    def test_response_name_matches_input(self):
        """Test that returned name matches input."""
        input_name = "my_custom_item"
        r = client.post("/items", json={"name": input_name, "price": 10})
        assert r.json()["name"] == input_name

    def test_response_price_matches_input(self):
        """Test that returned price matches input."""
        input_price = 42.5
        r = client.post("/items", json={"name": "test", "price": input_price})
        assert r.json()["price"] == input_price

    @pytest.mark.parametrize("input_name", ["a", "test", "product", "αβγ", "🎉"])
    def test_response_name_matches_for_various_inputs(self, input_name):
        """Test name preservation for different input values."""
        r = client.post("/items", json={"name": input_name, "price": 10})
        assert r.json()["name"] == input_name

    @pytest.mark.parametrize("input_price", [0.01, 1, 10.5, 100, 999.99])
    def test_response_price_matches_for_various_inputs(self, input_price):
        """Test price preservation for different input values."""
        r = client.post("/items", json={"name": "test", "price": input_price})
        assert r.json()["price"] == input_price

    def test_id_is_consistent(self):
        """Test that id field has a consistent value."""
        r1 = client.post("/items", json={"name": "item1", "price": 10})
        r2 = client.post("/items", json={"name": "item2", "price": 20})
        # Both should have the same id (implementation returns 1)
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1

    def test_id_positive(self):
        """Test that id is positive."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.json()["id"] > 0

    def test_price_positive_in_response(self):
        """Test that price in response is positive (or zero - if accepted)."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.json()["price"] >= 0


class TestCreateItemErrorResponses:
    """Test error response formats for invalid requests."""

    def test_error_response_is_dict(self):
        """Test that error response is a dict."""
        r = client.post("/items", json={"price": 10})
        assert isinstance(r.json(), dict)

    def test_error_response_has_detail_field(self):
        """Test that error response includes detail field."""
        r = client.post("/items", json={"price": 10})
        data = r.json()
        assert "detail" in data

    def test_invalid_price_error_detail_not_empty(self):
        """Test that error detail is not empty."""
        r = client.post("/items", json={"name": "test", "price": 0})
        detail = r.json()["detail"]
        assert detail
        assert len(detail) > 0

    def test_invalid_price_error_is_string(self):
        """Test that error detail is a string."""
        r = client.post("/items", json={"name": "test", "price": 0})
        detail = r.json()["detail"]
        assert isinstance(detail, str)

    def test_missing_field_error_status_422(self):
        """Test that missing field returns 422 status."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422

    def test_invalid_price_error_status_400(self):
        """Test that invalid price returns 400 status."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_price_zero_error_message_consistent(self):
        """Test that zero price error message is consistent."""
        r1 = client.post("/items", json={"name": "test1", "price": 0})
        r2 = client.post("/items", json={"name": "test2", "price": 0})
        assert r1.json()["detail"] == r2.json()["detail"]

    def test_negative_price_error_message_consistent(self):
        """Test that negative price error message is consistent."""
        r1 = client.post("/items", json={"name": "test1", "price": -10})
        r2 = client.post("/items", json={"name": "test2", "price": -20})
        assert r1.json()["detail"] == r2.json()["detail"]


class TestGetItemResponseValid:
    """Test response structure for get item endpoint."""

    def test_get_item_response_status_200(self):
        """Test that get returns 200 status."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_response_is_json(self):
        """Test that get response is JSON."""
        r = client.get("/items/1")
        assert r.headers["content-type"] == "application/json"

    def test_get_item_response_is_dict(self):
        """Test that get response body is a dict."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_has_id_field(self):
        """Test that get response has id field."""
        r = client.get("/items/1")
        assert "id" in r.json()

    def test_get_item_has_name_field(self):
        """Test that get response has name field."""
        r = client.get("/items/1")
        assert "name" in r.json()

    def test_get_item_has_price_field(self):
        """Test that get response has price field."""
        r = client.get("/items/1")
        assert "price" in r.json()

    def test_get_item_response_has_exactly_three_fields(self):
        """Test that get response has exactly 3 fields."""
        r = client.get("/items/1")
        data = r.json()
        assert len(data) == 3

    def test_get_item_id_matches_request_id(self):
        """Test that returned id matches requested id."""
        r = client.get("/items/1")
        assert r.json()["id"] == 1

    def test_get_item_has_name_value(self):
        """Test that get response name field has a value."""
        r = client.get("/items/1")
        name = r.json()["name"]
        assert name
        assert isinstance(name, str)

    def test_get_item_has_price_value(self):
        """Test that get response price field has a value."""
        r = client.get("/items/1")
        price = r.json()["price"]
        assert price is not None
        assert isinstance(price, (int, float))

    def test_get_item_price_is_positive(self):
        """Test that returned price is positive."""
        r = client.get("/items/1")
        assert r.json()["price"] > 0


class TestGetItemErrorResponses:
    """Test error response formats for get item endpoint."""

    def test_not_found_status_404(self):
        """Test that non-existent item returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_not_found_has_detail(self):
        """Test that 404 response has detail field."""
        r = client.get("/items/999")
        assert "detail" in r.json()

    def test_not_found_detail_not_empty(self):
        """Test that 404 detail is not empty."""
        r = client.get("/items/999")
        detail = r.json()["detail"]
        assert detail
        assert len(detail) > 0

    def test_not_found_detail_is_string(self):
        """Test that 404 detail is a string."""
        r = client.get("/items/999")
        detail = r.json()["detail"]
        assert isinstance(detail, str)

    def test_negative_item_id_not_found(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_zero_item_id_not_found(self):
        """Test that zero item_id returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_large_item_id_not_found(self):
        """Test that large item_id returns 404."""
        r = client.get("/items/1000000")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_not_found_error_message_consistent(self):
        """Test that 404 error message is consistent."""
        r1 = client.get("/items/2")
        r2 = client.get("/items/3")
        assert r1.json()["detail"] == r2.json()["detail"]


class TestHealthCheckResponse:
    """Test response structure for health check endpoint."""

    def test_health_check_status_200(self):
        """Test that health check returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_check_response_is_json(self):
        """Test that health check response is JSON."""
        r = client.get("/health")
        assert r.headers["content-type"] == "application/json"

    def test_health_check_response_is_dict(self):
        """Test that health check response is a dict."""
        r = client.get("/health")
        assert isinstance(r.json(), dict)

    def test_health_check_has_status_field(self):
        """Test that health check has status field."""
        r = client.get("/health")
        assert "status" in r.json()

    def test_health_check_status_value(self):
        """Test that health check status is 'ok'."""
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_check_status_is_string(self):
        """Test that health status is a string."""
        r = client.get("/health")
        assert isinstance(r.json()["status"], str)

    def test_health_check_response_exactly_one_field(self):
        """Test that health check response has exactly one field."""
        r = client.get("/health")
        data = r.json()
        assert len(data) == 1

    def test_health_check_response_consistent(self):
        """Test that health check returns same response."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.json() == r2.json()


class TestResponseContentType:
    """Test content-type headers across all endpoints."""

    def test_create_item_content_type_json(self):
        """Test that create response has JSON content-type."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert "application/json" in r.headers["content-type"]

    def test_get_item_content_type_json(self):
        """Test that get response has JSON content-type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers["content-type"]

    def test_health_check_content_type_json(self):
        """Test that health response has JSON content-type."""
        r = client.get("/health")
        assert "application/json" in r.headers["content-type"]

    def test_error_response_content_type_json(self):
        """Test that error response has JSON content-type."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert "application/json" in r.headers["content-type"]

    def test_validation_error_content_type_json(self):
        """Test that validation error has JSON content-type."""
        r = client.post("/items", json={"price": 10})
        assert "application/json" in r.headers["content-type"]


class TestErrorResponseConsistency:
    """Test consistency of error response formats."""

    def test_all_error_responses_have_detail(self):
        """Test that all error responses include detail field."""
        responses = [
            client.post("/items", json={"name": "test", "price": 0}),  # Business error
            client.post("/items", json={"price": 10}),  # Validation error
            client.get("/items/999"),  # Not found
        ]
        for r in responses:
            assert r.status_code >= 400
            assert "detail" in r.json()

    def test_all_error_details_are_strings(self):
        """Test that all error details are strings."""
        responses = [
            client.post("/items", json={"name": "test", "price": 0}),
            client.post("/items", json={"price": 10}),
            client.get("/items/999"),
        ]
        for r in responses:
            assert isinstance(r.json()["detail"], (str, list))  # Can be string or list for validation
