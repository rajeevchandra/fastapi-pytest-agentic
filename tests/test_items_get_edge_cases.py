import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [
        1,
        "1",
    ])
    def test_valid_item_ids_accepted(self, item_id):
        """Valid item IDs should be accepted."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [
        2,
        3,
        100,
        999,
        10000,
    ])
    def test_non_existent_item_ids_return_404(self, item_id):
        """Non-existent item IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemPathParameterBoundaryValues:
    """Test boundary value handling for item_id path parameter."""

    def test_item_id_zero_returns_404(self):
        """Item ID 0 should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_item_id_negative_returns_404(self):
        """Negative item IDs should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_item_id_large_returns_404(self):
        """Very large item IDs should return 404."""
        r = client.get("/items/999999999")
        assert r.status_code == 404

    def test_item_id_max_int_returns_404(self):
        """Maximum integer values should return 404."""
        r = client.get("/items/9223372036854775807")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [
        -1,
        -10,
        -100,
        -999,
    ])
    def test_negative_item_ids_all_return_404(self, item_id):
        """All negative item IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestGetItemPathParameterInvalidFormats:
    """Test invalid path parameter formats."""

    def test_non_integer_path_param_returns_422(self):
        """Non-integer path parameters should return 422."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_float_path_param_returns_422(self):
        """Float path parameters should return 422."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_empty_path_param_returns_404(self):
        """Empty path parameter should return 404 or 422."""
        r = client.get("/items/")
        assert r.status_code in [404, 405]

    def test_special_char_path_param_returns_422(self):
        """Special characters in path should return 422."""
        r = client.get("/items/!@#$%")
        assert r.status_code == 422


class TestCreateItemBoundaryPrices:
    """Test boundary value pricing for POST /items."""

    def test_minimum_positive_price(self):
        """Minimum positive price should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_price_just_above_zero(self):
        """Price just above zero should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200

    def test_very_large_price(self):
        """Very large prices should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e15})
        assert r.status_code == 200

    def test_scientific_notation_price(self):
        """Scientific notation should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 1.5e5})
        assert r.status_code == 200
        assert r.json()["price"] == 150000.0

    @pytest.mark.parametrize("price", [
        0.00001,
        0.001,
        0.01,
        0.1,
        1.0,
    ])
    def test_small_positive_prices_accepted(self, price):
        """Small positive prices should all be accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemNameBoundaryValues:
    """Test boundary values for name field."""

    def test_single_char_name(self):
        """Single character name should be accepted."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_very_long_name(self):
        """Very long name (1000+ chars) should be accepted."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_name_with_only_spaces(self):
        """Name with only spaces should be accepted (not empty string)."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_name_with_newlines(self):
        """Name with newline characters should be accepted."""
        name = "line1\nline2"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_name_with_tabs(self):
        """Name with tab characters should be accepted."""
        name = "col1\tcol2"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestSequentialOperations:
    """Test sequential API operations and interactions."""

    def test_create_then_retrieve_item(self):
        """Create item then retrieve using GET."""
        # Create item
        create_r = client.post("/items", json={"name": "test_item", "price": 99.99})
        assert create_r.status_code == 200
        create_data = create_r.json()
        
        # Retrieve item
        get_r = client.get(f"/items/{create_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()
        
        # Created ID should be 1
        assert create_data["id"] == 1
        assert get_data["id"] == 1

    def test_multiple_post_operations(self):
        """Multiple POST operations should all return 200."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i + 10)})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_post_then_get_nonexistent(self):
        """Create item then try to get non-existent item."""
        # Create
        create_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_r.status_code == 200
        
        # Try to get non-existent
        get_r = client.get("/items/999")
        assert get_r.status_code == 404


class TestMethodsAndPaths:
    """Test HTTP method handling and path variations."""

    def test_post_to_items_endpoint(self):
        """POST to /items should work."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_get_to_items_endpoint_fails(self):
        """GET to /items (without ID) should fail."""
        r = client.get("/items")
        assert r.status_code in [404, 405]

    def test_delete_to_items_endpoint_fails(self):
        """DELETE to /items should fail."""
        r = client.delete("/items")
        assert r.status_code in [404, 405]

    def test_put_to_items_endpoint_fails(self):
        """PUT to /items should fail."""
        r = client.put("/items", json={"name": "test", "price": 10.0})
        assert r.status_code in [404, 405]

    def test_post_to_items_with_id_fails(self):
        """POST to /items/{id} should fail."""
        r = client.post("/items/1", json={"name": "test", "price": 10.0})
        assert r.status_code in [404, 405]

    def test_get_to_items_with_id_succeeds(self):
        """GET to /items/{id} should work."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestRequestBodyFormats:
    """Test different request body formats."""

    def test_empty_request_body_fails(self):
        """Empty request body should fail."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_extra_fields_ignored(self):
        """Extra fields should be ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra": "ignored",
            "another": 123,
            "nested": {"field": "value"}
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra" not in data
        assert "another" not in data

    def test_fields_in_different_order(self):
        """Field order should not matter."""
        r1 = client.post("/items", json={"name": "test", "price": 10.0})
        r2 = client.post("/items", json={"price": 10.0, "name": "test"})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["name"] == r2.json()["name"]
        assert r1.json()["price"] == r2.json()["price"]


class TestConsistency:
    """Test API consistency across requests."""

    def test_repeated_requests_same_result(self):
        """Repeated requests with same input should return same data."""
        input_data = {"name": "consistent_test", "price": 42.5}
        
        r1 = client.post("/items", json=input_data)
        r2 = client.post("/items", json=input_data)
        
        assert r1.status_code == r2.status_code == 200
        assert r1.json()["name"] == r2.json()["name"]
        assert r1.json()["price"] == r2.json()["price"]

    def test_get_same_item_twice_same_result(self):
        """Getting same item twice should return same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        
        assert r1.status_code == r2.status_code == 200
        assert r1.json() == r2.json()

    def test_404_consistency(self):
        """Non-existent items should consistently return 404."""
        nonexistent_ids = [99, 100, 101]
        
        for item_id in nonexistent_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestErrorConsistency:
    """Test error response consistency."""

    def test_price_validation_error_consistent(self):
        """Price validation errors should be consistent."""
        invalid_prices = [-1, -10, 0]
        
        for price in invalid_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert "detail" in r.json()

    def test_not_found_error_format(self):
        """Not found errors should have consistent format."""
        not_found_ids = [2, 3, 10]
        
        for item_id in not_found_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            data = r.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)

    def test_validation_error_format_consistent(self):
        """Validation errors should have consistent format."""
        invalid_inputs = [
            {"name": "test"},  # missing price
            {"price": 10.0},   # missing name
            {"name": None, "price": 10.0},  # null name
        ]
        
        for input_data in invalid_inputs:
            r = client.post("/items", json=input_data)
            assert r.status_code == 422
            assert "detail" in r.json()


class TestHealthEndpoint:
    """Test /health endpoint behavior."""

    def test_health_always_returns_200(self):
        """Health endpoint should always return 200."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200

    def test_health_response_consistent(self):
        """Health endpoint should return consistent response."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        
        assert r1.json() == r2.json()
        assert r1.json()["status"] == "ok"

    def test_health_post_method_not_allowed(self):
        """POST to /health should fail."""
        r = client.post("/health")
        assert r.status_code in [404, 405]
