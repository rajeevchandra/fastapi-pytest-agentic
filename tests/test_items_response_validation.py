"""
Response Validation Tests for all endpoints.
Tests for response structure, types, and consistency.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test /items POST response structure and types."""

    def test_create_item_response_has_required_fields(self):
        """Test create_item response contains id, name, price."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Test create_item response has correct field types."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_no_extra_fields(self):
        """Test create_item response doesn't have unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_create_item_response_id_always_1(self):
        """Test create_item always returns id=1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"test{i}", "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_item_response_name_echoed(self):
        """Test create_item echoes back the name."""
        names = ["alpha", "beta", "gamma", "δ", "中文"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_response_price_echoed(self):
        """Test create_item echoes back the price."""
        prices = [0.01, 1.5, 99.99, 100.0, 1000000.0]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestCreateItemErrorResponse:
    """Test /items POST error response format."""

    def test_create_item_error_response_format(self):
        """Test error response has detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_create_item_error_detail_type(self):
        """Test error detail is a string."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert isinstance(data["detail"], str)

    def test_create_item_error_detail_message(self):
        """Test error detail contains meaningful message."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "price" in data["detail"].lower()

    @pytest.mark.parametrize("price", [-1, -0.5, 0])
    def test_create_item_consistent_error_message(self, price):
        """Test all invalid prices return same error message."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemValidationErrorResponse:
    """Test /items POST validation error responses."""

    def test_create_item_missing_price_response(self):
        """Test missing price returns validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_missing_name_response(self):
        """Test missing name returns validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_type_error_response(self):
        """Test type mismatch returns validation error."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_validation_error_has_detail_list(self):
        """Test validation error detail is a list or string."""
        r = client.post("/items", json={"price": "invalid"})
        assert r.status_code == 422
        data = r.json()
        # FastAPI returns detail as list of error objects or string
        assert "detail" in data


class TestGetItemResponseStructure:
    """Test /items/{item_id} GET response structure and types."""

    def test_get_item_response_has_required_fields(self):
        """Test get_item response contains id, name, price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test get_item response has correct field types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_no_extra_fields(self):
        """Test get_item response doesn't have unexpected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_get_item_found_response_values(self):
        """Test get_item found returns consistent values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert isinstance(data["name"], str)
        assert data["price"] == 10.0


class TestGetItemErrorResponse:
    """Test /items/{item_id} GET error response format."""

    def test_get_item_not_found_response_format(self):
        """Test not found error has detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_get_item_not_found_detail_type(self):
        """Test 404 detail is a string."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data["detail"], str)

    def test_get_item_not_found_detail_message(self):
        """Test 404 detail contains meaningful message."""
        r = client.get("/items/100")
        assert r.status_code == 404
        data = r.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_item_not_found_consistent_message(self, item_id):
        """Test all not-found IDs return same error message."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestHealthEndpointResponse:
    """Test /health endpoint response."""

    def test_health_response_structure(self):
        """Test health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_health_response_type(self):
        """Test health response field type."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["status"], str)

    def test_health_response_value(self):
        """Test health response has expected value."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_health_response_fields_count(self):
        """Test health response has only expected fields."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"status"}

    def test_health_response_consistent(self):
        """Test health endpoint returns consistent response."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}


class TestResponseContentType:
    """Test response content types."""

    def test_create_item_response_content_type(self):
        """Test create_item returns JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]

    def test_get_item_response_content_type(self):
        """Test get_item returns JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]

    def test_health_response_content_type(self):
        """Test health endpoint returns JSON."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]

    def test_error_response_content_type(self):
        """Test error responses return JSON."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "application/json" in r.headers["content-type"]


class TestResponseConsistency:
    """Test response consistency across multiple calls."""

    def test_create_item_response_consistency(self):
        """Test multiple create requests produce consistent responses."""
        responses = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            responses.append(r.json())
        
        # All should have same structure
        for resp in responses:
            assert set(resp.keys()) == {"id", "name", "price"}
            assert isinstance(resp["id"], int)
            assert isinstance(resp["name"], str)

    def test_get_item_response_consistency(self):
        """Test multiple get requests produce consistent responses."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0

    def test_error_response_consistency(self):
        """Test error responses are consistent."""
        for price in [-1, -10, 0]:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            data = r.json()
            assert data["detail"] == "price must be > 0"


class TestHttpStatusCodes:
    """Test correct HTTP status codes."""

    def test_create_item_success_status(self):
        """Test successful create returns 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_validation_error_status(self):
        """Test validation error returns 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_business_error_status(self):
        """Test business logic error returns 400."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_get_item_found_status(self):
        """Test found item returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_status(self):
        """Test not found returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_health_success_status(self):
        """Test health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200


class TestJsonEncoding:
    """Test JSON encoding and special characters in responses."""

    def test_response_with_unicode_name(self):
        """Test response properly encodes unicode characters."""
        r = client.post("/items", json={"name": "café", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "café"

    def test_response_with_emoji_name(self):
        """Test response properly encodes emoji."""
        r = client.post("/items", json={"name": "🎉 party", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "🎉 party"

    def test_response_with_special_chars(self):
        """Test response properly encodes special characters."""
        special_name = 'test"with\'quotes'
        r = client.post("/items", json={"name": special_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == special_name


class TestPriceValuePreservation:
    """Test that price values are preserved exactly."""

    @pytest.mark.parametrize("price", [
        0.01, 0.1, 0.5, 1.0, 1.5, 10.0, 99.99, 100.0, 1000.0, 
        3.14, 2.71, 0.001, 0.0001
    ])
    def test_price_value_preserved(self, price):
        """Test price values are preserved in response."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price
