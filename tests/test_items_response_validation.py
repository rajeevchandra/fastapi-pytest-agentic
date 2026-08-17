"""
Response structure and error handling validation for FastAPI items endpoint.

Tests focus on HTTP status codes, response structure consistency,
error response formatting, and edge case error handling.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes returned by create_item endpoint."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 100.0, 999.99])
    def test_create_item_success_returns_200(self, price):
        """Test that valid items return 200 OK."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200

    @pytest.mark.parametrize("price", [0, -1, -0.01, -100])
    def test_create_item_invalid_price_returns_400(self, price):
        """Test that invalid prices return 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    @pytest.mark.parametrize("payload", [
        {"price": 10.0},           # Missing name
        {"name": "test"},          # Missing price
        {},                        # Missing both
        {"name": None, "price": 10.0},  # None name
    ])
    def test_create_item_validation_error_returns_422(self, payload):
        """Test that validation errors return 422."""
        r = client.post("/items", json=payload)
        assert r.status_code == 422

    def test_create_item_no_content_type_returns_422(self):
        """Test POST with invalid content-type returns 422."""
        r = client.post("/items", data="invalid", headers={"Content-Type": "text/plain"})
        assert r.status_code == 422

    def test_create_item_successful_response_headers(self):
        """Test successful response includes proper headers."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "").lower()

    def test_create_item_error_response_headers(self):
        """Test error response includes proper headers."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "application/json" in r.headers.get("content-type", "").lower()


class TestCreateItemErrorResponseFormat:
    """Test error response format consistency for create_item."""

    def test_create_item_price_error_has_detail(self):
        """Test that price validation error has detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0

    def test_create_item_price_error_message_content(self):
        """Test that price error message is informative."""
        r = client.post("/items", json={"name": "test", "price": -1})
        data = r.json()
        assert "price" in data["detail"].lower()
        assert "0" in data["detail"] or "positive" in data["detail"].lower()

    def test_create_item_validation_error_structure(self):
        """Test validation error response structure."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_create_item_validation_error_has_error_info(self):
        """Test validation error contains error details."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        errors = data.get("detail", [])
        assert len(errors) > 0
        for error in errors:
            assert "loc" in error
            assert "msg" in error
            assert "type" in error


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes returned by get_item endpoint."""

    def test_get_item_found_returns_200(self):
        """Test that found items return 200 OK."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0, 2, 3, 999, 1000000])
    def test_get_item_not_found_returns_404(self, item_id):
        """Test that missing items return 404 Not Found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("path", ["abc", "1.5", "test", "1a"])
    def test_get_item_invalid_param_returns_422(self, path):
        """Test that invalid path parameters return 422."""
        r = client.get(f"/items/{path}")
        assert r.status_code in [404, 422]  # FastAPI may return 404 or 422 depending on config

    def test_get_item_found_response_headers(self):
        """Test successful get_item response has proper headers."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "").lower()

    def test_get_item_not_found_response_headers(self):
        """Test 404 response has proper headers."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "").lower()


class TestGetItemErrorResponseFormat:
    """Test error response format consistency for get_item."""

    def test_get_item_not_found_has_detail(self):
        """Test that 404 error has detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_get_item_not_found_message_content(self):
        """Test that 404 message is informative."""
        r = client.get("/items/2")
        data = r.json()
        assert "not found" in data["detail"].lower()

    def test_get_item_not_found_consistent_message(self):
        """Test that not found message is consistent across different IDs."""
        messages = []
        for item_id in [2, 999, 1000]:
            r = client.get(f"/items/{item_id}")
            if r.status_code == 404:
                messages.append(r.json()["detail"])
        
        # All messages should be identical
        assert len(set(messages)) == 1


class TestCreateItemResponseContent:
    """Test response content validation for create_item."""

    def test_create_item_response_json_valid(self):
        """Test response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        try:
            data = r.json()
            assert isinstance(data, dict)
        except ValueError:
            pytest.fail("Response is not valid JSON")

    def test_create_item_response_has_all_fields(self):
        """Test response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 19.99})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_has_only_required_fields(self):
        """Test response contains exactly the expected fields."""
        r = client.post("/items", json={"name": "book", "price": 19.99})
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_create_item_response_name_matches_input(self):
        """Test response name matches input name."""
        names = ["book", "pen", "notebook", "item123"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.json()["name"] == name

    def test_create_item_response_price_matches_input(self):
        """Test response price matches input price."""
        prices = [0.01, 1.0, 10.5, 100.0, 999.99]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.json()["price"] == price

    def test_create_item_response_id_always_one(self):
        """Test response always returns id=1."""
        for _ in range(5):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            assert r.json()["id"] == 1

    def test_create_item_response_null_values(self):
        """Test response contains no null values."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        data = r.json()
        for key, value in data.items():
            assert value is not None, f"Field '{key}' should not be null"


class TestGetItemResponseContent:
    """Test response content validation for get_item."""

    def test_get_item_response_json_valid(self):
        """Test response is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        try:
            data = r.json()
            assert isinstance(data, dict)
        except ValueError:
            pytest.fail("Response is not valid JSON")

    def test_get_item_response_has_all_fields(self):
        """Test response contains all required fields."""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_has_only_required_fields(self):
        """Test response contains exactly the expected fields."""
        r = client.get("/items/1")
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_get_item_response_values_consistent(self):
        """Test get_item returns consistent values on multiple calls."""
        results = []
        for _ in range(3):
            r = client.get("/items/1")
            results.append(r.json())
        
        # All results should be identical
        assert results[0] == results[1] == results[2]

    def test_get_item_response_expected_values(self):
        """Test get_item returns expected hardcoded values."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_null_values(self):
        """Test response contains no null values."""
        r = client.get("/items/1")
        data = r.json()
        for key, value in data.items():
            assert value is not None, f"Field '{key}' should not be null"


class TestErrorResponseConsistency:
    """Test consistency of error responses across different error types."""

    def test_error_responses_have_consistent_structure(self):
        """Test all error responses follow same structure."""
        error_responses = [
            client.post("/items", json={"name": "test", "price": 0}),      # 400
            client.post("/items", json={"price": 10.0}),                   # 422
            client.get("/items/999"),                                       # 404
        ]
        
        for r in error_responses:
            if r.status_code >= 400:
                data = r.json()
                assert "detail" in data, f"Error response missing 'detail' field: {data}"

    def test_success_responses_have_consistent_structure(self):
        """Test all success responses follow same structure."""
        success_responses = [
            client.post("/items", json={"name": "test", "price": 10.0}),
            client.get("/items/1"),
            client.get("/health"),
        ]
        
        for r in success_responses:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, dict)

    def test_error_detail_is_always_string_or_list(self):
        """Test detail field is either string or list of error objects."""
        # 400 error - should be string
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert isinstance(r1.json()["detail"], str)
        
        # 422 error - should be list
        r2 = client.post("/items", json={"price": 10.0})
        assert isinstance(r2.json()["detail"], list)
        
        # 404 error - should be string
        r3 = client.get("/items/999")
        assert isinstance(r3.json()["detail"], str)


class TestResponseContentTypes:
    """Test response content-type headers."""

    def test_json_responses_have_json_content_type(self):
        """Test all JSON responses have correct content-type."""
        endpoints = [
            ("GET", "/health"),
            ("POST", "/items", {"name": "test", "price": 10.0}),
            ("GET", "/items/1"),
        ]
        
        for method, path, *data in endpoints:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.post(path, json=data[0] if data else None)
            
            if r.status_code != 500:  # Skip server errors
                assert "application/json" in r.headers.get("content-type", "").lower()

    def test_error_responses_have_json_content_type(self):
        """Test error responses have JSON content-type."""
        error_responses = [
            client.post("/items", json={"name": "test", "price": 0}),
            client.post("/items", json={}),
            client.get("/items/999"),
        ]
        
        for r in error_responses:
            assert r.status_code >= 400
            assert "application/json" in r.headers.get("content-type", "").lower()


class TestHTTPMethodValidation:
    """Test HTTP method validation and allowed methods."""

    def test_items_get_method_not_allowed_on_create(self):
        """Test that GET is not allowed on create endpoint."""
        # POST /items should work, but calling root path might differ
        r = client.get("/items", params={"name": "test", "price": 10.0})
        # Should either return 405 Method Not Allowed or 404
        assert r.status_code in [404, 405]

    def test_items_post_required_for_create(self):
        """Test that POST works for create_item."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_items_put_not_supported(self):
        """Test that PUT is not supported on items."""
        r = client.put("/items/1", json={"name": "test", "price": 20.0})
        assert r.status_code in [404, 405, 422]

    def test_items_delete_not_supported(self):
        """Test that DELETE is not supported on items."""
        r = client.delete("/items/1")
        assert r.status_code in [404, 405]
