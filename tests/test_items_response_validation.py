"""
Response validation tests for items endpoints.

Tests cover:
- Response JSON structure consistency
- Data type validation for all fields
- Proper error response formats
- Edge cases for response values
- HTTP status codes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure from create_item endpoint."""

    def test_success_response_status_code(self):
        """Test that successful create returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_success_response_is_json(self):
        """Test that response is valid JSON."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_success_response_has_id_field(self):
        """Test that response includes id field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_success_response_has_name_field(self):
        """Test that response includes name field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "name" in r.json()

    def test_success_response_has_price_field(self):
        """Test that response includes price field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "price" in r.json()

    def test_success_response_id_equals_one(self):
        """Test that created item always has id=1."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_success_response_name_matches_input(self):
        """Test that response name matches input name."""
        input_name = "test_product"
        r = client.post("/items", json={"name": input_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == input_name

    def test_success_response_price_matches_input(self):
        """Test that response price matches input price."""
        input_price = 15.99
        r = client.post("/items", json={"name": "item", "price": input_price})
        assert r.status_code == 200
        assert r.json()["price"] == input_price


class TestCreateItemErrorResponse:
    """Test error response formats from create_item."""

    def test_invalid_price_error_status_code(self):
        """Test that invalid price returns 400."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_invalid_price_error_response_is_json(self):
        """Test that error response is valid JSON."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert isinstance(data, dict)

    def test_invalid_price_error_has_detail_field(self):
        """Test that error response has detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_invalid_price_error_message_content(self):
        """Test error message for invalid price."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail or "positive" in detail.lower()

    def test_zero_price_error_message(self):
        """Test exact error message for zero price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_negative_price_error_message(self):
        """Test error message for negative price."""
        r = client.post("/items", json={"name": "item", "price": -10})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_validation_error_status_code(self):
        """Test that validation errors return 422."""
        r = client.post("/items", json={"name": "item"})  # Missing price
        assert r.status_code == 422

    def test_validation_error_response_format(self):
        """Test format of validation error response."""
        r = client.post("/items", json={"price": 10.0})  # Missing name
        assert r.status_code == 422
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data


class TestCreateItemResponseDataTypes:
    """Test data types in create_item response."""

    def test_response_id_is_integer(self):
        """Test that id field is an integer."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_response_name_is_string(self):
        """Test that name field is a string."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_response_price_is_number(self):
        """Test that price field is a number."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        price = r.json()["price"]
        assert isinstance(price, (int, float))

    def test_response_price_is_positive(self):
        """Test that price in response is positive."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["price"] > 0

    @pytest.mark.parametrize("name", ["a", "item", "very_long_name_test_123"])
    def test_response_name_preserves_input_type(self, name):
        """Test that name field always remains string."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)


class TestGetItemResponseStructure:
    """Test response structure from get_item endpoint."""

    def test_get_item_success_status_code(self):
        """Test that get_item returns 200 for existing item."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_success_response_is_json(self):
        """Test that get_item response is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_response_has_id_field(self):
        """Test that get_item response has id field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "id" in r.json()

    def test_get_item_response_has_name_field(self):
        """Test that get_item response has name field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "name" in r.json()

    def test_get_item_response_has_price_field(self):
        """Test that get_item response has price field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "price" in r.json()

    def test_get_item_returns_correct_id(self):
        """Test that get_item returns the requested id."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_response_has_sample_data(self):
        """Test that get_item returns expected sample data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestGetItemResponseDataTypes:
    """Test data types in get_item response."""

    def test_get_item_response_id_is_integer(self):
        """Test that id is integer in get_item response."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_get_item_response_name_is_string(self):
        """Test that name is string in get_item response."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_get_item_response_price_is_number(self):
        """Test that price is number in get_item response."""
        r = client.get("/items/1")
        assert r.status_code == 200
        price = r.json()["price"]
        assert isinstance(price, (int, float))


class TestGetItemErrorResponse:
    """Test error responses from get_item endpoint."""

    def test_get_nonexistent_item_status_code(self):
        """Test that getting nonexistent item returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_nonexistent_item_error_is_json(self):
        """Test that 404 response is valid JSON."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data, dict)

    def test_get_nonexistent_item_has_detail_field(self):
        """Test that 404 response has detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_nonexistent_item_error_message(self):
        """Test error message for nonexistent item."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_various_nonexistent_ids(self):
        """Test 404 for various nonexistent item IDs."""
        for item_id in [2, 3, 10, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"


class TestConsistentResponseFormats:
    """Test that response formats are consistent across endpoints."""

    def test_successful_responses_all_have_detail_or_data(self):
        """Test structure consistency for success responses."""
        create_r = client.post("/items", json={"name": "item", "price": 10.0})
        get_r = client.get("/items/1")
        
        assert create_r.status_code == 200
        assert get_r.status_code == 200
        
        # Both return item data, not error structure
        create_data = create_r.json()
        get_data = get_r.json()
        
        assert "id" in create_data
        assert "id" in get_data

    def test_error_responses_all_have_detail_field(self):
        """Test that error responses consistently have detail field."""
        invalid_price_r = client.post("/items", json={"name": "item", "price": 0})
        not_found_r = client.get("/items/999")
        
        assert invalid_price_r.status_code == 400
        assert not_found_r.status_code == 404
        
        assert "detail" in invalid_price_r.json()
        assert "detail" in not_found_r.json()

    def test_all_responses_are_json(self):
        """Test that all responses are JSON."""
        endpoints = [
            ("POST", "/items", {"name": "item", "price": 10.0}),
            ("GET", "/items/1", None),
            ("GET", "/items/999", None),
        ]
        
        for method, path, data in endpoints:
            if method == "POST":
                r = client.post(path, json=data)
            else:
                r = client.get(path)
            
            # Should be valid JSON
            assert isinstance(r.json(), dict)


class TestResponseConsistencyAcrossValidInputs:
    """Test response consistency for various valid inputs."""

    @pytest.mark.parametrize("name,price", [
        ("item1", 10.0),
        ("item2", 0.01),
        ("item3", 1000.0),
    ])
    def test_response_structure_consistent_across_inputs(self, name, price):
        """Test that response structure is consistent for different inputs."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        
        # All responses should have these fields
        assert set(data.keys()) >= {"id", "name", "price"}
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestHealthEndpointResponse:
    """Test health endpoint response structure."""

    def test_health_returns_200(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_is_json(self):
        """Test that health response is valid JSON."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_health_response_has_status_field(self):
        """Test that health response has status field."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "status" in r.json()

    def test_health_response_status_value(self):
        """Test that health status is 'ok'."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_status_is_string(self):
        """Test that health status is a string."""
        r = client.get("/health")
        assert r.status_code == 200
        assert isinstance(r.json()["status"], str)
