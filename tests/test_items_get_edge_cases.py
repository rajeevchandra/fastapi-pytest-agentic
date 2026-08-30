"""
Edge cases and integration tests for the items API.
Tests path parameter boundaries, integration scenarios, and complex workflows.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [2, 3, 10, 999, 9999])
    def test_get_nonexistent_item_returns_404(self, item_id):
        """Getting non-existent items returns 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [-1, -5, -999])
    def test_get_negative_item_id_returns_404(self, item_id):
        """Negative item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_id_zero_returns_404(self):
        """Item ID 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_existing_item_id_one_returns_200(self):
        """Item ID 1 (the only valid item) returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [1, 100, 1000000])
    def test_get_item_id_path_parameter_as_string(self, item_id):
        """Path parameter is converted to integer."""
        r = client.get(f"/items/{item_id}")
        # Only ID 1 exists, others should be 404
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    def test_get_item_boundary_condition_max_int(self):
        """Very large integer path parameter returns 404."""
        large_id = 2147483647  # Max 32-bit int
        r = client.get(f"/items/{large_id}")
        assert r.status_code == 404

    def test_get_item_boundary_condition_min_int(self):
        """Very small (negative) integer path parameter returns 404."""
        small_id = -2147483648  # Min 32-bit int
        r = client.get(f"/items/{small_id}")
        assert r.status_code == 404


class TestCreateItemWithVariousPrices:
    """Test POST /items with various price values and boundaries."""

    @pytest.mark.parametrize("price", [0.01, 0.1, 1, 10, 100, 1000, 10000])
    def test_create_item_positive_prices_succeed(self, price):
        """All positive prices are accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0, -0.01, -1, -10, -100, -1000])
    def test_create_item_non_positive_prices_fail(self, price):
        """All non-positive prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    @pytest.mark.parametrize("price", [0.001, 0.0001, 0.00001])
    def test_create_item_very_small_positive_prices(self, price):
        """Very small positive prices are accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_price_as_float_string(self):
        """Float as string is coerced to float by Pydantic."""
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_price_as_integer_string(self):
        """Integer as string is coerced to float by Pydantic."""
        r = client.post("/items", json={"name": "item", "price": "10"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.0

    def test_create_item_price_precision(self):
        """Price values maintain precision."""
        price = 99.99
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemWithVariousNames:
    """Test POST /items with various name values."""

    @pytest.mark.parametrize("name", ["", "a", "ab", "test item", "Product-123"])
    def test_create_item_various_name_lengths(self, name):
        """Accept various name lengths including empty strings."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_spaces(self):
        """Names with spaces are accepted."""
        name = "   spaced name   "
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_unicode(self):
        """Unicode names are accepted."""
        name = "商品"  # Japanese for "product"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_emojis(self):
        """Names with emojis are accepted."""
        name = "🎁 Gift Item"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_very_long_name(self):
        """Very long names are accepted."""
        name = "x" * 10000
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestIntegrationScenarios:
    """Test integration scenarios and workflows."""

    def test_get_health_endpoint(self):
        """Health endpoint works."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_endpoint_multiple_calls(self):
        """Health endpoint is consistent across calls."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.json() == r2.json()

    def test_api_endpoints_available(self):
        """All documented endpoints are available."""
        # Health endpoint
        health = client.get("/health")
        assert health.status_code == 200

        # Create item endpoint
        create = client.post("/items", json={"name": "test", "price": 10.0})
        assert create.status_code == 200

        # Get item endpoint
        get_item = client.get("/items/1")
        assert get_item.status_code == 200

    def test_create_then_get_item_flow(self):
        """Can create and retrieve item (hardcoded ID 1)."""
        # Create
        create_r = client.post("/items", json={"name": "book", "price": 12.5})
        assert create_r.status_code == 200
        created = create_r.json()

        # Get (only works for ID 1)
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        retrieved = get_r.json()

        # Verify structure
        assert created["id"] == 1
        assert created["name"] == "book"
        assert created["price"] == 12.5
        assert retrieved["id"] == 1

    def test_error_recovery_workflow(self):
        """Can recover from validation errors."""
        # Send invalid request
        invalid = client.post("/items", json={"name": "item", "price": -1})
        assert invalid.status_code == 400

        # Follow up with valid request
        valid = client.post("/items", json={"name": "item", "price": 10.0})
        assert valid.status_code == 200

        # Both requests work as expected
        assert invalid.json()["detail"] == "price must be > 0"
        assert valid.json()["price"] == 10.0


class TestPriceEdgeCases:
    """Test price field edge cases and boundary conditions."""

    def test_price_boundary_just_above_zero(self):
        """Price just above zero is accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_price_boundary_exactly_zero(self):
        """Price exactly zero is rejected."""
        r = client.post("/items", json={"name": "item", "price": 0.0})
        assert r.status_code == 400

    def test_price_boundary_just_below_zero(self):
        """Price just below zero is rejected."""
        r = client.post("/items", json={"name": "item", "price": -0.0001})
        assert r.status_code == 400

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.0, 1000.0])
    def test_price_valid_range_endpoints(self, price):
        """Valid price range endpoints work."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200

    def test_price_large_value(self):
        """Large price values are accepted."""
        large_price = 1e15
        r = client.post("/items", json={"name": "item", "price": large_price})
        assert r.status_code == 200
        assert r.json()["price"] == large_price

    def test_price_very_large_value(self):
        """Very large price values are accepted."""
        very_large_price = 1e30
        r = client.post("/items", json={"name": "item", "price": very_large_price})
        assert r.status_code == 200


class TestNameEdgeCases:
    """Test name field edge cases."""

    def test_name_empty_string(self):
        """Empty string name is allowed."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_name_single_character(self):
        """Single character name is allowed."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_name_whitespace_only(self):
        """Whitespace-only names are allowed."""
        name = "   "
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_name_special_characters(self):
        """Special characters in names are allowed."""
        name = "!@#$%^&*()"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_name_newline_characters(self):
        """Newline characters in names are handled."""
        name = "line1\nline2"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_name_tab_characters(self):
        """Tab characters in names are handled."""
        name = "col1\tcol2"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestValidationBoundaries:
    """Test validation at boundary conditions."""

    def test_price_zero_is_boundary_invalid(self):
        """Price = 0 is the boundary and invalid."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_price_just_above_zero_is_valid(self):
        """Price slightly above 0 is valid."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_item_id_boundary_zero_not_found(self):
        """Item ID = 0 returns 404 (boundary)."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_item_id_boundary_one_found(self):
        """Item ID = 1 returns 200 (valid boundary)."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_item_id_boundary_two_not_found(self):
        """Item ID = 2 returns 404 (boundary)."""
        r = client.get("/items/2")
        assert r.status_code == 404


class TestErrorConsistency:
    """Test error behavior consistency."""

    def test_same_error_returns_same_message(self):
        """Same error returns consistent message."""
        r1 = client.post("/items", json={"name": "item", "price": -1})
        r2 = client.post("/items", json={"name": "item", "price": -1})
        assert r1.json()["detail"] == r2.json()["detail"]

    def test_different_negative_prices_same_error(self):
        """Different negative prices get same error."""
        r1 = client.post("/items", json={"name": "item", "price": -1})
        r2 = client.post("/items", json={"name": "item", "price": -100})
        assert r1.status_code == r2.status_code == 400
        assert r1.json()["detail"] == r2.json()["detail"]

    def test_404_errors_consistent(self):
        """404 errors are consistent."""
        r1 = client.get("/items/99")
        r2 = client.get("/items/99")
        assert r1.json() == r2.json()

    def test_validation_error_format_consistent(self):
        """Validation errors have consistent format."""
        r1 = client.post("/items", json={"price": 10})
        r2 = client.post("/items", json={"price": 10})
        assert r1.status_code == r2.status_code == 422
        assert "detail" in r1.json()
        assert "detail" in r2.json()
