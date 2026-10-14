"""Input validation and boundary testing for create_item endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Tests for price field validation and boundaries."""

    @pytest.mark.parametrize("price,expected_status,should_fail", [
        (0, 400, True),
        (-1, 400, True),
        (-0.01, 400, True),
        (-100, 400, True),
        (-999999.99, 400, True),
    ])
    def test_non_positive_prices(self, price, expected_status, should_fail):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == expected_status
        if should_fail:
            assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [
        0.01,
        0.1,
        1.0,
        10.5,
        100.99,
        999999.99,
        1000000.0,
    ])
    def test_positive_prices_accepted(self, price):
        """Test that positive prices are accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["id"] == 1
        assert data["name"] == "item"

    @pytest.mark.parametrize("price,name", [
        (0.01, "cheap"),
        (0.99, "penny"),
        (1.5, "normal"),
        (99.99, "expensive"),
    ])
    def test_various_valid_prices_with_names(self, price, name):
        """Test various valid price and name combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["name"] == name


class TestCreateItemNameValidation:
    """Tests for name field validation."""

    @pytest.mark.parametrize("name", [
        "book",
        "laptop",
        "single letter",
        "name with spaces",
        "123numbers",
        "UPPERCASE",
        "MixedCase",
        "special!chars@here#",
        "emoji😀test",
        "unicode_café",
        "newline\ntest",
        "tab\ttest",
    ])
    def test_various_names_accepted(self, name):
        """Test that various name values are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 10.0

    def test_very_long_name(self):
        """Test very long name string."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name
        assert len(data["name"]) == 1000

    def test_empty_name(self):
        """Test empty name string."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == ""

    def test_name_with_quotes(self):
        """Test name with various quote characters."""
        r = client.post("/items", json={"name": 'name with "quotes"', "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == 'name with "quotes"'

    def test_name_with_apostrophe(self):
        """Test name with apostrophe."""
        r = client.post("/items", json={"name": "it's", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "it's"

    def test_name_with_newlines_and_whitespace(self):
        """Test name with various whitespace characters."""
        r = client.post("/items", json={"name": "  \n  \t  ", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "  \n  \t  "


class TestCreateItemMissingFields:
    """Tests for missing required fields."""

    def test_missing_name_field(self):
        """Test request without name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Validation error

    def test_missing_price_field(self):
        """Test request without price field."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422  # Validation error

    def test_missing_both_fields(self):
        """Test request with empty JSON object."""
        r = client.post("/items", json={})
        assert r.status_code == 422  # Validation error

    def test_extra_fields_ignored(self):
        """Test that extra fields in request are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should be ignored",
            "another": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test"
        assert data["price"] == 10.0
        assert "extra_field" not in data
        assert "another" not in data


class TestCreateItemTypeValidation:
    """Tests for type validation."""

    def test_price_as_string_number(self):
        """Test price as string representation of number."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        # FastAPI should coerce string numbers to float
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 10.5

    def test_price_as_integer(self):
        """Test price as integer."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 10
        assert isinstance(data["price"], (int, float))

    def test_price_as_string_invalid(self):
        """Test price as non-numeric string."""
        r = client.post("/items", json={"name": "test", "price": "not a number"})
        assert r.status_code == 422  # Validation error

    def test_price_as_null(self):
        """Test price as null value."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422  # Validation error

    def test_name_as_null(self):
        """Test name as null value."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422  # Validation error

    def test_name_as_number(self):
        """Test name as number (should be coerced to string)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == 123 or data["name"] == "123"

    def test_price_as_boolean(self):
        """Test price as boolean."""
        r = client.post("/items", json={"name": "test", "price": True})
        # In Python/JSON, True is 1, False is 0
        assert r.status_code in [200, 400]  # Depends on validation

    def test_price_as_list(self):
        """Test price as list."""
        r = client.post("/items", json={"name": "test", "price": [10.0]})
        assert r.status_code == 422  # Validation error

    def test_name_as_list(self):
        """Test name as list."""
        r = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert r.status_code in [200, 422]  # Depends on validation

    def test_name_as_dict(self):
        """Test name as dict."""
        r = client.post("/items", json={"name": {"value": "item"}, "price": 10.0})
        assert r.status_code == 422  # Validation error


class TestCreateItemResponseStructure:
    """Tests for response structure validation."""

    def test_response_has_all_required_fields(self):
        """Test that response contains id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_id_is_always_one(self):
        """Test that created items always have id=1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1

    def test_response_fields_match_request(self):
        """Test that response name and price match request."""
        test_data = [
            {"name": "book", "price": 12.99},
            {"name": "pen", "price": 0.99},
            {"name": "", "price": 100.0},
            {"name": "x" * 100, "price": 0.01},
        ]
        for item in test_data:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == item["name"]
            assert data["price"] == item["price"]

    def test_response_is_json(self):
        """Test that response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
        data = r.json()  # Should not raise
        assert isinstance(data, dict)

    def test_error_response_structure(self):
        """Test error response structure."""
        r = client.post("/items", json={"name": "bad", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestCreateItemSequentialOperations:
    """Tests for sequential create operations."""

    def test_multiple_creates_all_succeed(self):
        """Test that multiple sequential creates all succeed."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1

    def test_create_after_failed_create(self):
        """Test that a successful create can follow a failed create."""
        # First create should fail
        r1 = client.post("/items", json={"name": "bad", "price": -5})
        assert r1.status_code == 400

        # Second create should succeed
        r2 = client.post("/items", json={"name": "good", "price": 10})
        assert r2.status_code == 200
        data = r2.json()
        assert data["name"] == "good"

    def test_create_with_boundary_values_sequence(self):
        """Test sequence of creates with boundary values."""
        prices = [0.01, 1.0, 100.0, 999999.99]
        for price in prices:
            r = client.post("/items", json={"name": f"item_{price}", "price": price})
            assert r.status_code == 200
            data = r.json()
            assert data["price"] == price


class TestCreateItemEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_price_zero_point_zero_zero_one(self):
        """Test minimum positive price."""
        r = client.post("/items", json={"name": "cheap", "price": 0.001})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 0.001

    def test_price_with_many_decimals(self):
        """Test price with many decimal places."""
        r = client.post("/items", json={"name": "precise", "price": 10.123456789})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], float)

    def test_name_single_character(self):
        """Test single character name."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "a"

    def test_name_with_backslash(self):
        """Test name with backslash."""
        r = client.post("/items", json={"name": "path\\to\\file", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "path\\to\\file"

    def test_name_with_html_tags(self):
        """Test name with HTML tags."""
        r = client.post("/items", json={"name": "<script>alert('xss')</script>", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "<script>alert('xss')</script>"

    def test_name_with_sql_injection_attempt(self):
        """Test name with SQL injection attempt."""
        r = client.post("/items", json={"name": "'; DROP TABLE items; --", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "'; DROP TABLE items; --"

    def test_malformed_json_not_accepted(self):
        """Test that malformed JSON is rejected."""
        r = client.post("/items", data="{invalid json}", content_type="application/json")
        assert r.status_code in [400, 422]  # Parsing error

    def test_null_json_not_accepted(self):
        """Test that null JSON is rejected."""
        r = client.post("/items", json=None)
        assert r.status_code in [400, 422]  # Invalid request

    def test_array_instead_of_object(self):
        """Test that array instead of object is rejected."""
        r = client.post("/items", json=[{"name": "item", "price": 10}])
        assert r.status_code == 422  # Validation error
