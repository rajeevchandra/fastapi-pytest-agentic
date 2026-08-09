"""Response structure and error handling tests for items endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure and content type."""

    def test_response_is_json(self):
        """Test that response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.headers["content-type"] == "application/json"
        assert isinstance(r.json(), dict)

    def test_response_fields_are_correct_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_error_response_format(self):
        """Test that error responses have correct format."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_validation_error_response_format(self):
        """Test validation error response format."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for various scenarios."""

    @pytest.mark.parametrize("name,price,expected_status", [
        ("valid", 10.0, 200),
        ("valid", 0.01, 200),
        ("valid", 999999, 200),
        ("valid", 0, 400),
        ("valid", -10, 400),
        ("valid", -0.5, 400),
    ])
    def test_status_codes_for_various_prices(self, name, price, expected_status):
        """Test that correct status codes are returned for different prices."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == expected_status

    def test_missing_required_field_status_code(self):
        """Test that missing required fields return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422


class TestGetItemResponseStructure:
    """Test response structure for get_item endpoint."""

    def test_response_contains_all_fields(self):
        """Test that GET response contains id, name, price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_content_type(self):
        """Test that response content type is JSON."""
        r = client.get("/items/1")
        assert r.headers["content-type"] == "application/json"


class TestGetItemErrorResponses:
    """Test error responses for get_item endpoint."""

    def test_not_found_response_format(self):
        """Test not found error response format."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_not_found_for_multiple_ids(self, item_id):
        """Test not found for various item IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_invalid_item_id_type_in_url(self):
        """Test that invalid item ID type returns error."""
        r = client.get("/items/abc")
        # Path parameter validation should fail
        assert r.status_code in (422, 400)

    def test_found_item_returns_200(self):
        """Test that item ID 1 returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestGetItemConsistency:
    """Test consistency of get_item responses."""

    def test_get_item_1_always_returns_same_data(self):
        """Test that multiple calls to /items/1 return same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_get_item_1_expected_values(self):
        """Test that /items/1 returns expected fixed values."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_multiple_get_requests_same_data(self):
        """Test consistency across multiple requests."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1
            assert r.json()["name"] == "sample"
