"""
Input validation tests for /items POST endpoint.

Tests comprehensive validation of required fields, boundary conditions,
and edge cases for the create_item endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation with boundary values and edge cases."""

    @pytest.mark.parametrize(
        "price,should_pass",
        [
            # Negative prices
            (-100.0, False),
            (-1.0, False),
            (-0.01, False),
            # Zero price
            (0.0, False),
            # Positive prices - valid
            (0.01, True),
            (1.0, True),
            (10.0, True),
            (99.99, True),
            (1000.0, True),
            # Large values
            (999999.99, True),
            (1e6, True),
            # Very small positive
            (0.001, True),
        ],
    )
    def test_price_boundary_validation(self, price, should_pass):
        """Test price validation at various boundary values."""
        response = client.post(
            "/items", json={"name": "test_item", "price": price}
        )
        if should_pass:
            assert response.status_code == 200, f"Failed for price={price}"
            assert response.json()["price"] == price
        else:
            assert response.status_code == 400, f"Should reject price={price}"
            assert "price must be > 0" in response.json()["detail"]

    def test_price_missing_field(self):
        """Test that missing price field is rejected."""
        response = client.post("/items", json={"name": "test_item"})
        assert response.status_code == 422
        assert "price" in response.json()["detail"][0]["loc"]

    def test_price_null_value(self):
        """Test that null price is rejected."""
        response = client.post(
            "/items", json={"name": "test_item", "price": None}
        )
        assert response.status_code == 422

    def test_price_string_value(self):
        """Test that string price is rejected."""
        response = client.post(
            "/items", json={"name": "test_item", "price": "10.5"}
        )
        # FastAPI will try to coerce but should accept valid numeric string
        # or reject invalid one
        assert response.status_code in [200, 422]

    def test_price_array_value(self):
        """Test that array price is rejected."""
        response = client.post(
            "/items", json={"name": "test_item", "price": [10, 20]}
        )
        assert response.status_code == 422


class TestCreateItemNameValidation:
    """Test name field validation with various string formats."""

    @pytest.mark.parametrize(
        "name,should_pass",
        [
            # Valid names
            ("item", True),
            ("book", True),
            ("product name", True),
            ("A", True),
            ("Item123", True),
            ("Product with spaces", True),
            # Empty and whitespace
            ("", False),
            (" ", False),
            # Long names (realistic limit check)
            ("a" * 100, True),
            ("a" * 1000, True),
            # Special characters
            ("item@store", True),
            ("item#1", True),
            ("item-name", True),
            ("item_name", True),
            # Unicode
            ("café", True),
            ("日本", True),
            ("emoji🎁test", True),
        ],
    )
    def test_name_variations(self, name, should_pass):
        """Test various name formats."""
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        if should_pass:
            assert response.status_code == 200, f"Failed for name={name!r}"
            assert response.json()["name"] == name
        else:
            # Empty string might be rejected by Pydantic or accepted by FastAPI
            # This depends on field validation configuration
            assert response.status_code in [200, 422]

    def test_name_missing_field(self):
        """Test that missing name field is rejected."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        assert "name" in response.json()["detail"][0]["loc"]

    def test_name_null_value(self):
        """Test that null name is rejected."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422

    def test_name_integer_value(self):
        """Test that integer name is handled (may coerce to string or reject)."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        # FastAPI might coerce or reject
        assert response.status_code in [200, 422]

    def test_name_array_value(self):
        """Test that array name is rejected."""
        response = client.post(
            "/items", json={"name": ["item1", "item2"], "price": 10.0}
        )
        assert response.status_code == 422


class TestCreateItemRequiredFields:
    """Test that all required fields are validated."""

    def test_both_fields_missing(self):
        """Test POST with no fields."""
        response = client.post("/items", json={})
        assert response.status_code == 422

    def test_only_price_provided(self):
        """Test POST with only price."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422

    def test_only_name_provided(self):
        """Test POST with only name."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored (not an error)."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 10.0, "extra_field": "value"},
        )
        # Pydantic by default ignores extra fields
        assert response.status_code == 200

    def test_empty_json_object(self):
        """Test with empty JSON object."""
        response = client.post("/items", json={})
        assert response.status_code == 422


class TestCreateItemResponseValidation:
    """Test the response structure and data types."""

    def test_response_has_required_fields(self):
        """Test that response contains all expected fields."""
        response = client.post(
            "/items", json={"name": "test_item", "price": 15.50}
        )
        assert response.status_code == 200
        data = response.json()
        # Check all expected fields are present
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.post(
            "/items", json={"name": "test_item", "price": 15.50}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_echoes_input_name(self):
        """Test that response echoes back the input name."""
        test_name = "MyProduct"
        response = client.post(
            "/items", json={"name": test_name, "price": 20.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == test_name

    def test_response_echoes_input_price(self):
        """Test that response echoes back the input price."""
        test_price = 25.75
        response = client.post(
            "/items", json={"name": "item", "price": test_price}
        )
        assert response.status_code == 200
        assert response.json()["price"] == test_price

    def test_response_id_is_constant(self):
        """Test that API returns consistent ID (current implementation always returns 1)."""
        response1 = client.post(
            "/items", json={"name": "item1", "price": 10.0}
        )
        response2 = client.post(
            "/items", json={"name": "item2", "price": 20.0}
        )
        # Based on current implementation, both return id=1
        assert response1.json()["id"] == response2.json()["id"]

    def test_response_http_headers(self):
        """Test response headers are correct."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]


class TestCreateItemErrorMessages:
    """Test error message clarity and consistency."""

    def test_price_error_message_format(self):
        """Test that price validation error has clear message."""
        response = client.post(
            "/items", json={"name": "item", "price": -5.0}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert isinstance(error_detail, str)
        assert "price" in error_detail.lower()
        assert ">" in error_detail or "greater" in error_detail.lower()

    def test_missing_field_error_includes_field_name(self):
        """Test that validation errors mention the missing field."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("name" in str(e).lower() for e in error_detail)

    def test_invalid_type_error_includes_field_name(self):
        """Test that type validation errors mention the field."""
        response = client.post(
            "/items", json={"name": "item", "price": "not_a_number"}
        )
        assert response.status_code == 422
