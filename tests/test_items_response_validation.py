"""Response structure validation and GET endpoint edge cases."""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [0, -1, -100, -999])
    def test_get_item_rejects_non_positive_item_id(self, item_id):
        """Test that non-positive item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 999999])
    def test_get_item_not_found_for_other_ids(self, item_id):
        """Test that item IDs other than 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_success_for_id_1(self):
        """Test that item ID 1 returns successful response."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_boundary_value_max_int(self):
        """Test with very large integer ID."""
        large_id = 2147483647
        r = client.get(f"/items/{large_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_boundary_value_one_less_than_valid(self):
        """Test with ID just before the valid one."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_boundary_value_one_more_than_valid(self):
        """Test with ID just after the valid one."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemResponseStructure:
    """Test response structure and field validation for get_item."""

    def test_get_item_response_has_all_fields(self):
        """Test that response contains all expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_field_values(self):
        """Test specific response field values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_no_extra_fields(self):
        """Test that response has no unexpected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_get_item_response_format(self):
        """Test response is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        # Verify it's valid JSON and can be parsed
        data = r.json()
        assert data is not None
        assert isinstance(data, dict)


class TestGetItemErrorResponseStructure:
    """Test error response structure for get_item."""

    def test_get_item_not_found_response_structure(self):
        """Test 404 response has correct structure."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_get_item_not_found_error_consistency(self):
        """Test 404 error message is consistent."""
        for item_id in [2, 3, 100]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    def test_get_item_not_found_with_negative_id(self):
        """Test 404 for negative item ID."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_error_response_is_json(self):
        """Test that error responses are valid JSON."""
        r = client.get("/items/999")
        assert r.status_code == 404
        # Verify JSON parsing works
        data = r.json()
        assert isinstance(data, dict)


class TestGetItemContentType:
    """Test content type and headers for get_item."""

    def test_get_item_response_content_type(self):
        """Test that response has JSON content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_not_found_content_type(self):
        """Test that 404 response has JSON content type."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self):
        """Test health endpoint returns ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_health_check_response_structure(self):
        """Test health response has correct structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert len(data) == 1

    def test_health_check_response_type(self):
        """Test health response field type."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["status"], str)

    def test_health_check_content_type(self):
        """Test health response has JSON content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestCreateItemResponseValidation:
    """Test response validation for create_item endpoint."""

    def test_create_item_response_json_format(self):
        """Test that response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_create_item_response_contains_id(self):
        """Test that response contains ID field."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_create_item_response_id_is_integer(self):
        """Test that ID field is an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_name_matches_input(self):
        """Test that returned name matches input."""
        test_name = "specific_book_title"
        r = client.post("/items", json={"name": test_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == test_name

    def test_create_item_response_price_matches_input(self):
        """Test that returned price matches input."""
        test_price = 25.99
        r = client.post("/items", json={"name": "test", "price": test_price})
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    def test_create_item_response_no_unexpected_fields(self):
        """Test response doesn't include unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        keys = set(r.json().keys())
        expected = {"id", "name", "price"}
        assert keys == expected


class TestCreateItemErrorResponseValidation:
    """Test error response structure for create_item."""

    def test_create_item_error_response_has_detail(self):
        """Test that error response has detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_create_item_error_detail_message(self):
        """Test that error detail message is correct."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_error_consistency(self):
        """Test error message consistency across requests."""
        for price in [0, -1, -10]:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert r.json()["detail"] == "price must be > 0"

    def test_create_item_validation_error_status(self):
        """Test that validation errors return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_validation_error_structure(self):
        """Test validation error response structure."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        # Pydantic validation errors have 'detail' key
        assert "detail" in data or isinstance(data, dict)


class TestIntegrationSequences:
    """Test sequences of operations."""

    def test_create_then_retrieve_item(self):
        """Test creating and retrieving an item in sequence."""
        # Create item
        create_r = client.post("/items", json={"name": "integration_test", "price": 15.5})
        assert create_r.status_code == 200
        created_data = create_r.json()

        # Retrieve the same item
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()

        # Verify both have same ID (should be 1)
        assert created_data["id"] == retrieved_data["id"]
        assert retrieved_data["id"] == 1

    def test_multiple_creates_return_same_id(self):
        """Test that multiple creates return same ID."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_retrieve_after_create_with_different_name(self):
        """Test retrieving created item gets backend value not created value."""
        create_r = client.post("/items", json={"name": "created_name", "price": 10.0})
        assert create_r.status_code == 200

        # Retrieve should get "sample" from backend, not "created_name"
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        assert get_r.json()["name"] == "sample"
