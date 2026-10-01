from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemResponseStructure:
    """Test response structure validation for get_item endpoint."""

    def test_response_has_all_required_fields(self):
        """Verify response contains all expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) >= 3

    def test_response_field_types_are_correct(self):
        """Verify each response field has the correct type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_returns_expected_values(self):
        """Verify get_item returns the expected hardcoded values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_response_json_serializable(self):
        """Verify response is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/json"
        # Verify we can serialize/deserialize
        data = r.json()
        assert data is not None

    def test_response_no_extra_fields(self):
        """Verify response only contains expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        # Only id, name, price should be present
        assert set(data.keys()) == {"id", "name", "price"}


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    def test_found_item_returns_200(self):
        """Verify existing item returns 200 OK."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_not_found_items_return_404(self, item_id):
        """Verify non-existent items return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_negative_item_id_returns_404(self):
        """Verify negative item IDs return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_zero_item_id_returns_404(self):
        """Verify item ID 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [0, -1, -100, 2, 999, 1000000])
    def test_only_item_1_exists(self, item_id):
        """Verify only item_id=1 returns 200, all others 404."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestNotFoundErrorResponse:
    """Test error response structure for 404 errors."""

    def test_not_found_error_has_detail(self):
        """Verify 404 response has detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_not_found_error_message(self):
        """Verify 404 error message is correct."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_not_found_error_consistency(self):
        """Verify 404 error message is consistent across requests."""
        for item_id in [2, 999, 1000000]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    def test_error_response_json_structure(self):
        """Verify error response is valid JSON with standard structure."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    def test_valid_item_returns_200(self):
        """Verify successful creation returns 200 OK."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200

    def test_invalid_price_returns_400(self):
        """Verify invalid price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    @pytest.mark.parametrize("price", [-1, -100, 0, -0.5])
    def test_non_positive_prices_return_400(self, price):
        """Verify all non-positive prices return 400."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    def test_missing_field_returns_422(self):
        """Verify missing required field returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_invalid_type_returns_422(self):
        """Verify invalid type returns 422."""
        r = client.post("/items", json={"name": "item", "price": "invalid"})
        assert r.status_code == 422

    def test_malformed_json_returns_422(self):
        """Verify malformed JSON returns 422."""
        r = client.post("/items", content="{not valid json}")
        assert r.status_code == 422


class TestCreateItemErrorMessages:
    """Test error messages for create_item endpoint."""

    def test_price_validation_error_message(self):
        """Verify price validation error message is clear."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_price_error_consistency(self):
        """Verify error message is consistent for price violations."""
        for price in [0, -1, -100]:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert "price must be > 0" in r.json()["detail"]

    def test_validation_error_has_detail_array(self):
        """Verify validation errors include detailed error array."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

    def test_validation_error_includes_field_location(self):
        """Verify validation error specifies which field failed."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert any(e["loc"][1] == "price" for e in errors)

    def test_validation_error_includes_error_type(self):
        """Verify validation error includes error type."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert any("type" in e for e in errors)

    def test_multiple_field_errors(self):
        """Verify multiple field errors are all reported."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        errors = r.json()["detail"]
        # Both name and price should be missing
        assert len(errors) >= 2


class TestResponseContentType:
    """Test response content type headers."""

    def test_create_item_response_content_type(self):
        """Verify create_item response is application/json."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]

    def test_get_item_response_content_type(self):
        """Verify get_item response is application/json."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]

    def test_health_response_content_type(self):
        """Verify health endpoint response is application/json."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]

    def test_error_response_content_type(self):
        """Verify error responses are application/json."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "application/json" in r.headers["content-type"]


class TestHealthEndpointResponse:
    """Test health endpoint response structure."""

    def test_health_returns_status_ok(self):
        """Verify health endpoint returns status ok."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_response_has_status_field(self):
        """Verify health response has status field."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "status" in r.json()

    def test_health_status_value(self):
        """Verify status field has correct value."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_endpoint_always_200(self):
        """Verify health endpoint always returns 200."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200


class TestResponseConsistency:
    """Test that responses are consistent across multiple requests."""

    def test_create_item_response_consistency(self):
        """Verify create_item response is consistent."""
        responses = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            responses.append(r.json())
        
        # All responses should have the same structure
        for resp in responses:
            assert set(resp.keys()) == {"id", "name", "price"}
            assert isinstance(resp["id"], int)
            assert isinstance(resp["name"], str)
            assert isinstance(resp["price"], (int, float))

    def test_get_item_response_consistency(self):
        """Verify get_item response is consistent."""
        responses = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            responses.append(r.json())
        
        # All responses should be identical (since it's hardcoded)
        first = responses[0]
        for resp in responses[1:]:
            assert resp == first

    def test_error_response_consistency(self):
        """Verify error responses have consistent structure."""
        test_cases = [
            ("/items", {"name": "test"}, 422),
            ("/items", {"price": 10.0}, 422),
            ("/items", {"name": "test", "price": 0}, 400),
        ]
        
        for endpoint, data, expected_status in test_cases:
            r = client.post(endpoint, json=data)
            assert r.status_code == expected_status
            assert "detail" in r.json()


class TestResponseTypes:
    """Test response type validation and handling."""

    def test_price_is_number_in_create_response(self):
        """Verify price in create response is numeric."""
        test_prices = [1.5, 10, 99.99, 0.01, 1000.0]
        for price in test_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert isinstance(r.json()["price"], (int, float))

    def test_price_is_float_in_get_response(self):
        """Verify price in get response is numeric."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))

    def test_name_is_string_in_responses(self):
        """Verify name is always a string in responses."""
        test_names = ["test", "item123", "a", "very long name" * 10]
        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert isinstance(r.json()["name"], str)

    def test_id_is_integer(self):
        """Verify ID is always an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)
        assert r.json()["id"] == 1

    def test_get_response_id_is_integer(self):
        """Verify get response ID is integer."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)


class TestErrorFieldValidation:
    """Test that error responses contain required fields."""

    def test_business_error_has_detail_field(self):
        """Verify business logic error has detail field."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_validation_error_has_detail_array(self):
        """Verify validation error has detail array."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_validation_error_includes_type_field(self):
        """Verify each validation error includes type field."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert all("type" in e for e in errors)

    def test_validation_error_includes_location_field(self):
        """Verify each validation error includes location."""
        r = client.post("/items", json={"price": "invalid"})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert all("loc" in e for e in errors)

    def test_validation_error_location_is_list(self):
        """Verify location in error is a list."""
        r = client.post("/items", json={"price": "invalid"})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert all(isinstance(e["loc"], list) for e in errors)
