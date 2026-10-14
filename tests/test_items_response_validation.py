"""Response structure and error handling validation tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Tests for validating response structure from create_item."""

    def test_response_has_required_fields(self):
        """Test that response has all required fields."""
        r = client.post("/items", json={"name": "book", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    @pytest.mark.parametrize("field_name", ["id", "name", "price"])
    def test_response_contains_each_required_field(self, field_name):
        """Test that response contains specific required field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert field_name in data

    def test_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_id_is_integer(self):
        """Test that id field is an integer."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert data["id"] == int(data["id"])

    def test_response_name_is_string(self):
        """Test that name field is a string."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["name"], str)

    def test_response_price_is_numeric(self):
        """Test that price field is numeric."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], (int, float))

    @pytest.mark.parametrize("input_price,expected_type", [
        (10.5, (int, float)),
        (10, (int, float)),
        (0.01, (int, float)),
    ])
    def test_response_price_type_consistency(self, input_price, expected_type):
        """Test that price type is consistent regardless of input."""
        r = client.post("/items", json={"name": "item", "price": input_price})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], expected_type)


class TestGetItemResponseStructure:
    """Tests for validating response structure from get_item."""

    def test_get_response_has_required_fields(self):
        """Test that GET response has all required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    @pytest.mark.parametrize("field_name", ["id", "name", "price"])
    def test_get_response_contains_each_required_field(self, field_name):
        """Test that GET response contains specific required field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert field_name in data

    def test_get_response_field_types(self):
        """Test that GET response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_response_id_value(self):
        """Test that GET response has correct id value."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_get_response_name_value(self):
        """Test that GET response has correct name value."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "sample"

    def test_get_response_price_value(self):
        """Test that GET response has correct price value."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 10.0

    def test_get_response_consistency(self):
        """Test that multiple GET requests return consistent data."""
        responses = [client.get("/items/1") for _ in range(3)]
        data_list = [r.json() for r in responses]
        
        for data in data_list:
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0


class TestErrorResponseStructure:
    """Tests for error response structure and consistency."""

    def test_400_error_has_detail_field(self):
        """Test that 400 error response has detail field."""
        r = client.post("/items", json={"name": "bad", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_400_error_detail_is_string(self):
        """Test that error detail is a string."""
        r = client.post("/items", json={"name": "bad", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert isinstance(data["detail"], str)

    def test_400_error_detail_message(self):
        """Test the specific error message for negative price."""
        r = client.post("/items", json={"name": "bad", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "price" in data["detail"].lower()
        assert "0" in data["detail"]

    def test_404_error_has_detail_field(self):
        """Test that 404 error response has detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_404_error_detail_is_string(self):
        """Test that 404 error detail is a string."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data["detail"], str)

    def test_404_error_detail_message(self):
        """Test the specific error message for not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999999, -1])
    def test_404_error_for_invalid_item_ids(self, item_id):
        """Test that invalid item IDs return 404 with proper error."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.parametrize("price", [-1, -0.01, -100, -999.99])
    def test_400_error_for_negative_prices(self, price):
        """Test that negative prices return consistent error."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_422_error_missing_field(self):
        """Test 422 error for missing required field."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_422_error_invalid_type(self):
        """Test 422 error for invalid field type."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_error_response_is_json(self):
        """Test that error responses are valid JSON."""
        r = client.post("/items", json={"name": "bad", "price": -1})
        assert r.status_code == 400
        assert r.headers["content-type"].startswith("application/json")
        r.json()  # Should not raise


class TestHTTPStatusCodes:
    """Tests for correct HTTP status codes."""

    def test_create_success_status_200(self):
        """Test that successful create returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_get_success_status_200(self):
        """Test that successful get returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_health_success_status_200(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_create_validation_error_status_400(self):
        """Test that price validation error returns 400."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_get_not_found_status_404(self):
        """Test that non-existent item returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_create_missing_field_status_422(self):
        """Test that missing field returns 422."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_invalid_type_status_422(self):
        """Test that invalid type returns 422."""
        r = client.post("/items", json={"name": "item", "price": "invalid"})
        assert r.status_code == 422

    @pytest.mark.parametrize("status_code,test_func", [
        (200, lambda: client.get("/health")),
        (200, lambda: client.post("/items", json={"name": "item", "price": 10.0})),
        (200, lambda: client.get("/items/1")),
        (400, lambda: client.post("/items", json={"name": "item", "price": -1})),
        (404, lambda: client.get("/items/2")),
        (422, lambda: client.post("/items", json={"name": "item"})),
    ])
    def test_status_codes_match_expectations(self, status_code, test_func):
        """Test various status code expectations."""
        r = test_func()
        assert r.status_code == status_code


class TestResponseHeaders:
    """Tests for response headers."""

    def test_success_response_has_content_type(self):
        """Test that successful responses have content-type header."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "content-type" in r.headers

    def test_success_response_content_type_is_json(self):
        """Test that successful responses have JSON content-type."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")

    def test_error_response_content_type_is_json(self):
        """Test that error responses have JSON content-type."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert r.headers["content-type"].startswith("application/json")

    def test_get_response_has_content_type(self):
        """Test that GET responses have content-type header."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "content-type" in r.headers

    def test_get_response_content_type_is_json(self):
        """Test that GET responses have JSON content-type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")

    def test_404_response_content_type_is_json(self):
        """Test that 404 responses have JSON content-type."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.headers["content-type"].startswith("application/json")


class TestCreateItemErrorScenarios:
    """Tests for various error scenarios."""

    def test_zero_price_error(self):
        """Test error for zero price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_negative_price_error(self):
        """Test error for negative price."""
        r = client.post("/items", json={"name": "item", "price": -10.5})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("invalid_price", [0, -1, -0.01, -100])
    def test_invalid_prices_all_return_400(self, invalid_price):
        """Test that all invalid prices return 400."""
        r = client.post("/items", json={"name": "item", "price": invalid_price})
        assert r.status_code == 400

    def test_both_errors_scenario(self):
        """Test scenario where multiple errors could occur."""
        # Missing name should fail before price check
        r = client.post("/items", json={"price": -1})
        assert r.status_code == 422


class TestEndpointConsistency:
    """Tests for consistency across endpoints."""

    def test_all_endpoints_return_json(self):
        """Test that all endpoints return JSON responses."""
        endpoints = [
            ("GET", "/health", None),
            ("GET", "/items/1", None),
            ("POST", "/items", {"name": "item", "price": 10.0}),
        ]
        for method, endpoint, data in endpoints:
            if method == "GET":
                r = client.get(endpoint)
            else:
                r = client.post(endpoint, json=data)
            assert r.headers["content-type"].startswith("application/json")

    def test_successful_responses_are_objects(self):
        """Test that successful responses are JSON objects (not arrays)."""
        r1 = client.get("/health")
        assert isinstance(r1.json(), dict)

        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert isinstance(r2.json(), dict)

        r3 = client.get("/items/1")
        assert isinstance(r3.json(), dict)

    def test_error_responses_are_objects(self):
        """Test that error responses are JSON objects."""
        r1 = client.post("/items", json={"name": "item", "price": -1})
        assert isinstance(r1.json(), dict)

        r2 = client.get("/items/999")
        assert isinstance(r2.json(), dict)

        r3 = client.post("/items", json={"name": "item"})
        assert isinstance(r3.json(), dict)
