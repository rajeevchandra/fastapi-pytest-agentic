"""Response structure and error handling tests for items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for various create item scenarios."""

    @pytest.mark.parametrize("price,expected_status", [
        (1.0, 200),
        (10.5, 200),
        (999.99, 200),
        (0, 400),
        (-1, 400),
        (-100.5, 400),
    ])
    def test_create_item_status_codes(self, price, expected_status):
        """Test status codes for different price values."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == expected_status

    def test_create_item_invalid_json_status(self):
        """Test status code when sending invalid JSON."""
        r = client.post("/items", content="invalid json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    @pytest.mark.parametrize("missing_field", ["name", "price"])
    def test_create_item_missing_field_status(self, missing_field):
        """Test status code when required field is missing."""
        payload = {"name": "test", "price": 10.0}
        del payload[missing_field]
        r = client.post("/items", json=payload)
        assert r.status_code == 422


class TestCreateItemResponseFormat:
    """Test response format and structure."""

    def test_create_item_success_response_is_json(self):
        """Test that success response is valid JSON."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/json"

    def test_create_item_error_response_is_json(self):
        """Test that error response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        assert r.headers["content-type"] == "application/json"

    def test_create_item_success_response_structure(self):
        """Test success response has expected structure."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert set(data.keys()) >= {"id", "name", "price"}

    def test_create_item_error_response_has_detail(self):
        """Test error response contains detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestCreateItemErrorMessages:
    """Test error message content and clarity."""

    def test_create_item_zero_price_error_message(self):
        """Test error message for zero price."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_negative_price_error_message(self):
        """Test error message for negative price."""
        r = client.post("/items", json={"name": "test", "price": -5.0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_validation_error_has_detail(self):
        """Test validation error response structure."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        # Pydantic validation errors have detail as list or string
        assert data["detail"]

    def test_create_item_price_type_error_message(self):
        """Test error message for invalid price type."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        assert "detail" in r.json()


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get item endpoint."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),      # Valid item
        (2, 404),      # Non-existent item
        (0, 404),      # Invalid item
        (-1, 404),     # Negative ID
        (999, 404),    # Large non-existent ID
    ])
    def test_get_item_status_codes(self, item_id, expected_status):
        """Test status codes for different item IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status

    def test_get_item_invalid_id_format(self):
        """Test getting item with invalid ID format."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_missing_id(self):
        """Test getting item without ID."""
        r = client.get("/items/")
        # FastAPI routes this differently, typically 307 or 404
        assert r.status_code in [307, 404]


class TestGetItemResponseFormat:
    """Test response format for get item endpoint."""

    def test_get_item_found_response_is_json(self):
        """Test that found response is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/json"

    def test_get_item_not_found_response_is_json(self):
        """Test that not found response is valid JSON."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.headers["content-type"] == "application/json"

    def test_get_item_success_response_structure(self):
        """Test success response has expected structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_error_response_structure(self):
        """Test error response structure."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestGetItemErrorMessages:
    """Test error message content for get item endpoint."""

    def test_get_item_not_found_error_message(self):
        """Test error message when item not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_invalid_id_type_error(self):
        """Test error when item ID has invalid type."""
        r = client.get("/items/abc")
        assert r.status_code == 422


class TestCreateItemDataPersistence:
    """Test that created items are accessible via get endpoint."""

    def test_create_and_retrieve_item(self):
        """Test that created item can be retrieved."""
        # Create an item
        create_r = client.post("/items", json={"name": "testbook", "price": 15.0})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]
        
        # Retrieve the created item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify retrieved data matches created data
        assert retrieved["id"] == created_id

    def test_created_item_accessible_via_correct_id(self):
        """Test that created item is accessible with correct ID."""
        create_r = client.post("/items", json={"name": "unique_item", "price": 25.5})
        assert create_r.status_code == 200
        item_id = create_r.json()["id"]
        
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == item_id


class TestResponseFieldTypes:
    """Test that response field types are correct."""

    def test_create_item_id_is_integer(self):
        """Test that created item ID is an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert data["id"] > 0

    def test_create_item_name_is_string(self):
        """Test that response name is a string."""
        r = client.post("/items", json={"name": "testname", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["name"], str)

    def test_create_item_price_is_number(self):
        """Test that response price is a number."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_field_types(self):
        """Test field types in get item response."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestResponseContentConsistency:
    """Test consistency between request and response."""

    def test_create_item_name_preserved(self):
        """Test that name is preserved in response."""
        test_names = ["book", "laptop", "coffee cup", "item-123", "item_456"]
        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_price_preserved(self):
        """Test that price is preserved in response."""
        test_prices = [1.0, 10.5, 99.99, 0.01, 1000.0]
        for price in test_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_create_item_special_chars_preserved(self):
        """Test special characters are preserved in name."""
        special_name = "item!@#$%^&*()"
        r = client.post("/items", json={"name": special_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name

    def test_create_item_unicode_preserved(self):
        """Test unicode is preserved in name."""
        unicode_name = "café ☕ 北京"
        r = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == unicode_name


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint_returns_200(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_endpoint_returns_status_ok(self):
        """Test that health endpoint returns status ok."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"

    def test_health_endpoint_response_is_json(self):
        """Test that health endpoint response is JSON."""
        r = client.get("/health")
        assert r.headers["content-type"] == "application/json"


class TestHTTPMethods:
    """Test appropriate HTTP methods are supported."""

    def test_create_item_requires_post(self):
        """Test that create item requires POST."""
        # GET should not be allowed
        r = client.get("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 404 or r.status_code == 405

    def test_get_item_requires_get(self):
        """Test that get item requires GET."""
        # POST should not work (might return different error)
        r = client.post("/items/1")
        # POST to /items/{id} might return 405 Method Not Allowed or other error
        assert r.status_code != 200

    def test_create_items_endpoint_exists(self):
        """Test that /items POST endpoint exists."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code != 404

    def test_get_item_endpoint_exists(self):
        """Test that /items/{id} GET endpoint exists."""
        r = client.get("/items/1")
        assert r.status_code != 404


class TestErrorResponseConsistency:
    """Test consistency in error response format."""

    def test_all_errors_have_detail_field(self):
        """Test that all error responses include detail field."""
        # Test various error scenarios
        error_requests = [
            ("POST", "/items", {"name": "test", "price": 0}),           # Business logic error
            ("POST", "/items", {"price": 10.0}),                         # Validation error
            ("GET", "/items/999", None),                                  # Not found error
        ]
        
        for method, path, json_data in error_requests:
            if method == "POST":
                r = client.post(path, json=json_data)
            else:
                r = client.get(path)
            
            if r.status_code >= 400:
                assert "detail" in r.json()

    def test_error_response_always_json(self):
        """Test that all error responses are JSON."""
        error_requests = [
            ("POST", "/items", {"price": 10.0}),
            ("GET", "/items/999", None),
            ("GET", "/items/abc", None),
        ]
        
        for method, path, json_data in error_requests:
            if method == "POST":
                r = client.post(path, json=json_data)
            else:
                r = client.get(path)
            
            if r.status_code >= 400:
                assert "application/json" in r.headers["content-type"]
