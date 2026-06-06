import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def valid_item_payload():
    """Fixture providing a valid item creation payload."""
    return {"name": "Test Item", "price": 25.99}


@pytest.fixture
def invalid_price_payload():
    """Fixture providing item payload with invalid price."""
    return {"name": "Bad Item", "price": -10.0}


class TestCreateItemSuccess:
    def test_create_item_success(self):
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "book"
        assert data["price"] == 12.5

    @pytest.mark.parametrize("price", [0.01, 1, 100, 9999.99])
    def test_create_item_with_various_valid_prices(self, price):
        r = client.post("/items", json={"name": "product", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_very_long_name(self):
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_special_characters_in_name(self):
        special_name = "Product™ with™ émojis 🎉"
        r = client.post("/items", json={"name": special_name, "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name


class TestCreateItemPriceValidation:
    def test_create_item_rejects_zero_price(self):
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-1, -0.01, -100, -9999.99])
    def test_create_item_rejects_negative_prices(self, price):
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_accepts_very_large_price(self):
        large_price = 999999999.99
        r = client.post("/items", json={"name": "expensive", "price": large_price})
        assert r.status_code == 200
        assert r.json()["price"] == large_price


class TestCreateItemInputValidation:
    def test_create_item_missing_name_field(self):
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_price_field(self):
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_all_fields(self):
        r = client.post("/items", json={})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_invalid_json(self):
        r = client.post("/items", content="{invalid json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_create_item_with_null_name(self):
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_null_price(self):
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_numeric_string_price_accepted(self):
        # Pydantic coerces numeric strings to float
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_with_non_numeric_string_price(self):
        r = client.post("/items", json={"name": "item", "price": "abc"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_numeric_name(self):
        r = client.post("/items", json={"name": 12345, "price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_empty_name(self):
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_with_whitespace_name(self):
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_with_extra_fields(self):
        r = client.post("/items", json={"name": "item", "price": 10.0, "extra_field": "ignored"})
        assert r.status_code == 200
        assert "extra_field" not in r.json()


class TestGetItemSuccess:
    def test_get_item_found(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_structure(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_get_item_response_types(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_content_type(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemNotFound:
    def test_get_item_not_found(self):
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, 3, 999, 99999])
    def test_get_item_not_found_various_ids(self, item_id):
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_id_boundary_negative_one(self):
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_id_boundary_zero(self):
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_boundary_large(self):
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_get_item_error_response_structure(self):
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestGetItemPathParameterValidation:
    def test_get_item_with_string_path_param(self):
        r = client.get("/items/abc")
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_get_item_with_float_path_param(self):
        r = client.get("/items/1.5")
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_get_item_with_special_chars_in_path(self):
        r = client.get("/items/abc@123")
        assert r.status_code == 422

    def test_get_item_with_empty_path_param_matches_items_endpoint(self):
        # GET /items/ tries to match /items/{item_id} but no item_id provided
        # so it fails to match and tries the collection endpoint
        r = client.get("/items/")
        # 405 Method Not Allowed is correct - no GET on items collection
        assert r.status_code == 405

    def test_get_item_with_very_large_integer(self):
        large_int = 9223372036854775807  # max int64
        r = client.get(f"/items/{large_int}")
        assert r.status_code == 404

    def test_get_item_with_negative_large_integer(self):
        large_negative = -9223372036854775808  # min int64
        r = client.get(f"/items/{large_negative}")
        assert r.status_code == 404


class TestIntegrationScenarios:
    """Integration tests for complete workflows and API interactions."""

    def test_create_and_retrieve_workflow(self, valid_item_payload):
        """Test complete workflow: create item then retrieve it."""
        # Create the item
        create_response = client.post("/items", json=valid_item_payload)
        assert create_response.status_code == 200
        created_item = create_response.json()
        item_id = created_item["id"]

        # Retrieve the created item
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        assert retrieved_item["id"] == item_id
        assert retrieved_item["name"] == "sample"  # API returns hardcoded data
        assert isinstance(retrieved_item["price"], (int, float))

    def test_multiple_failed_creations_then_success(self, valid_item_payload):
        """Test multiple failed creations followed by successful one."""
        # Multiple failed attempts
        for invalid_price in [0, -5, -100]:
            r = client.post("/items", json={"name": "test", "price": invalid_price})
            assert r.status_code == 400

        # Successful creation after failures
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        assert r.json()["price"] == valid_item_payload["price"]

    def test_invalid_json_then_valid_request(self):
        """Test recovery from invalid JSON with subsequent valid request."""
        # Invalid request
        r = client.post("/items", content="{bad json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

        # Valid request succeeds
        r = client.post("/items", json={"name": "good", "price": 15.0})
        assert r.status_code == 200

    def test_retrieve_item_before_and_after_creation_attempts(self):
        """Test that item retrieval is consistent regardless of other API calls."""
        # Initial retrieval of item 1
        r1 = client.get("/items/1")
        data1 = r1.json()

        # Attempt to create items with various invalid payloads
        client.post("/items", json={"price": 0})  # Missing name
        client.post("/items", json={"name": "test"})  # Missing price
        client.post("/items", json={})  # Empty

        # Verify item 1 data unchanged
        r2 = client.get("/items/1")
        data2 = r2.json()
        assert data1 == data2


class TestResponseValidation:
    """Tests focused on validating complete response structures and metadata."""

    def test_create_response_has_all_required_fields(self):
        """Validate that create response includes all expected fields."""
        r = client.post("/items", json={"name": "Complete", "price": 29.99})
        assert r.status_code == 200
        data = r.json()

        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_get_response_has_all_required_fields(self):
        """Validate that get response includes all expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()

        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_error_response_has_detail_field(self):
        """Validate that error responses include detail field."""
        test_cases = [
            (400, "post", "/items", {"name": "bad", "price": -5}),
            (404, "get", "/items/999", None),
            (422, "post", "/items", {}),
        ]

        for expected_status, method, path, payload in test_cases:
            if method == "post":
                r = client.post(path, json=payload)
            else:
                r = client.get(path)
            
            if r.status_code == expected_status:
                assert "detail" in r.json(), f"Error response missing detail for {method} {path}"

    @pytest.mark.parametrize("test_name,price,expected_status", [
        ("valid_small_price", 0.01, 200),
        ("valid_medium_price", 50.00, 200),
        ("valid_large_price", 999999.99, 200),
        ("invalid_zero_price", 0, 400),
        ("invalid_negative_price", -1.50, 400),
    ])
    def test_price_validation_combinations(self, test_name, price, expected_status):
        """Parametrized test for various price validation scenarios."""
        r = client.post("/items", json={"name": test_name, "price": price})
        assert r.status_code == expected_status, f"Failed for {test_name}"


class TestResponseMetadata:
    """Tests for HTTP response metadata, headers, and status codes."""

    def test_success_response_status_codes(self):
        """Verify success status codes for valid requests."""
        # POST success
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code in [200, 201], "POST should return 200 or 201"

        # GET success
        r = client.get("/items/1")
        assert r.status_code == 200, "GET should return 200"

    def test_error_status_codes_are_appropriate(self):
        """Verify error status codes match the error type."""
        # 400 Bad Request
        r = client.post("/items", json={"name": "x", "price": -1})
        assert r.status_code == 400, "Invalid price should return 400"

        # 404 Not Found
        r = client.get("/items/999")
        assert r.status_code == 404, "Non-existent item should return 404"

        # 422 Unprocessable Entity
        r = client.post("/items", json={})
        assert r.status_code == 422, "Missing required fields should return 422"

    def test_json_content_type_on_responses(self):
        """Verify responses have JSON content type."""
        endpoints_and_methods = [
            ("post", "/items", {"name": "test", "price": 10.0}),
            ("get", "/items/1", None),
        ]

        for method, path, payload in endpoints_and_methods:
            if method == "post":
                r = client.post(path, json=payload)
            else:
                r = client.get(path)

            content_type = r.headers.get("content-type", "")
            assert "application/json" in content_type, f"Response should have JSON content type for {method} {path}"


class TestEdgeCasesCombinations:
    """Tests combining multiple edge cases for comprehensive coverage."""

    def test_max_valid_values(self):
        """Test with maximum valid values."""
        long_name = "a" * 5000
        large_price = 999999999.99

        r = client.post("/items", json={"name": long_name, "price": large_price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == large_price

    def test_unicode_and_special_chars_comprehensive(self):
        """Test various unicode and special characters in names."""
        test_names = [
            "Product™",
            "Café ☕",
            "Item © 2024",
            "Test\nNewline",  # Newlines
            "Test\tTab",  # Tabs
            "emoji🎉🎊",
        ]

        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_float_precision(self):
        """Test handling of floating point precision."""
        test_prices = [
            0.01,
            1.23,
            10.99,
            99.999,
            123.456789,
        ]

        for price in test_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            # Note: May lose some precision due to float representation
            assert abs(r.json()["price"] - price) < 0.001
