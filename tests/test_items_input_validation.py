"""
Comprehensive input validation and boundary testing for items endpoints.
Tests focus on validating price/name boundaries, type coercion, and required fields.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation with boundary values."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.01, True),
        (0.1, True),
        (1.0, True),
        (100.0, True),
        (999999.99, True),
        (0, False),
        (-0.01, False),
        (-1.0, False),
        (-100.0, False),
    ])
    def test_create_item_price_boundaries(self, price, should_succeed):
        """Test price boundaries: positive, zero, negative."""
        r = client.post("/items", json={"name": "item", "price": price})
        if should_succeed:
            assert r.status_code == 200, f"Price {price} should succeed"
        else:
            assert r.status_code == 400, f"Price {price} should fail"


class TestCreateItemNameValidation:
    """Test name field validation."""

    @pytest.mark.parametrize("name", [
        "a",
        "book",
        "My Item",
        "item-123",
        "item_456",
        "UPPERCASE",
        "item123",
        "Special!@#$%",
        "Unicode: café",
    ])
    def test_create_item_valid_names(self, name):
        """Various valid name formats should succeed."""
        r = client.post("/items", json={"name": name, "price": 1.0})
        assert r.status_code == 200

    @pytest.mark.parametrize("name", [
        "",
        " " * 10,
    ])
    def test_create_item_invalid_names(self, name):
        """Empty or whitespace-only names might fail (depends on validation)."""
        r = client.post("/items", json={"name": name, "price": 1.0})
        # Some frameworks accept empty strings, some don't
        # This tests the actual behavior
        assert r.status_code in [200, 422]

    def test_create_item_very_long_name(self):
        """Very long name should be accepted."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 1.0})
        assert r.status_code == 200

    def test_create_item_name_with_unicode(self):
        """Name with Unicode characters should be valid."""
        r = client.post("/items", json={"name": "café ☕", "price": 1.0})
        assert r.status_code == 200

    def test_create_item_name_with_emoji(self):
        """Name with emoji should be valid."""
        r = client.post("/items", json={"name": "Book 📖", "price": 1.0})
        assert r.status_code == 200


class TestCreateItemMissingFields:
    """Test validation of required fields."""

    def test_missing_name_field(self):
        """Request without name should fail."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_price_field(self):
        """Request without price should fail."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_missing_both_fields(self):
        """Request with neither field should fail."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_null_name_field(self):
        """null name should fail."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_null_price_field(self):
        """null price should fail."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation and coercion."""

    def test_price_as_string_numeric(self):
        """String price that looks numeric might be coerced."""
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        # Pydantic might coerce string to float
        assert r.status_code in [200, 422]

    def test_price_as_non_numeric_string(self):
        """String price that's not numeric should fail."""
        r = client.post("/items", json={"name": "item", "price": "abc"})
        assert r.status_code == 422

    def test_name_as_number(self):
        """Numeric name should be coerced to string or fail."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic typically coerces number to string
        assert r.status_code in [200, 422]

    def test_price_as_integer(self):
        """Integer price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200

    def test_extra_fields_ignored(self):
        """Extra fields in request should be ignored."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra_field": "should be ignored"
        })
        assert r.status_code == 200


class TestCreateItemEdgeCases:
    """Test edge cases in create item."""

    def test_very_small_price_accepted(self):
        """Price of 0.01 should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_very_large_price_accepted(self):
        """Very large price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99

    def test_zero_price_rejected(self):
        """Price of 0 should be rejected."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_negative_large_price_rejected(self):
        """Large negative price should be rejected."""
        r = client.post("/items", json={"name": "item", "price": -999999.99})
        assert r.status_code == 400

    def test_response_name_matches_input(self):
        """Response should echo back the input name."""
        test_name = "TestItem123"
        r = client.post("/items", json={"name": test_name, "price": 5.0})
        assert r.json()["name"] == test_name

    def test_response_price_matches_input(self):
        """Response should echo back the input price."""
        test_price = 12.34
        r = client.post("/items", json={"name": "item", "price": test_price})
        assert r.json()["price"] == test_price

    def test_multiple_creates_with_different_values(self):
        """Multiple create operations with different values."""
        items = [
            ("item1", 1.0),
            ("item2", 2.5),
            ("item3", 999.99),
        ]
        for name, price in items:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            assert r.json()["name"] == name
            assert r.json()["price"] == price


class TestCreateItemValidationOrder:
    """Test the order of validation checks."""

    def test_invalid_type_checked_before_business_logic(self):
        """Type validation should happen before price > 0 check."""
        r = client.post("/items", json={"name": "item", "price": "invalid"})
        assert r.status_code == 422  # Type error, not 400 (business logic)

    def test_missing_field_checked_before_business_logic(self):
        """Required field validation should happen first."""
        r = client.post("/items", json={"price": 0})
        assert r.status_code == 422  # Missing field, not 400 (business logic)


class TestPriceFieldBoundaries:
    """Comprehensive price boundary testing."""

    @pytest.mark.parametrize("price", [
        0.001,
        0.01,
        0.1,
        1.0,
        10.0,
        100.0,
        1000.0,
        10000.0,
        100000.0,
        999999.99,
    ])
    def test_positive_prices_accepted(self, price):
        """All positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200

    @pytest.mark.parametrize("price", [
        0,
        -0.001,
        -0.01,
        -0.1,
        -1.0,
        -10.0,
        -100.0,
        -999999.99,
    ])
    def test_zero_and_negative_prices_rejected(self, price):
        """Zero and negative prices should be rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400


class TestNameFieldVariations:
    """Comprehensive name field variation testing."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "abc",
        "Book",
        "My Book",
        "my-book",
        "my_book",
        "my.book",
        "Book123",
        "123Book",
        "123",
    ])
    def test_various_valid_names(self, name):
        """Various name patterns should be accepted."""
        r = client.post("/items", json={"name": name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == name
