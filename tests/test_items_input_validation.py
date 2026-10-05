"""Input validation and boundary testing for /items POST endpoint."""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation with boundary values and edge cases."""

    @pytest.mark.parametrize("price", [-100, -1, 0, 0.01, 1e10])
    def test_price_boundary_values(self, price):
        """Test various price values including boundaries."""
        r = client.post("/items", json={"name": "test", "price": price})
        if price > 0:
            assert r.status_code == 200
            assert r.json()["price"] == price
        else:
            assert r.status_code == 400
            assert "price must be > 0" in r.json()["detail"]

    def test_negative_price(self):
        """Test explicit negative price rejection."""
        r = client.post("/items", json={"name": "book", "price": -10.5})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_zero_price(self):
        """Test zero price rejection."""
        r = client.post("/items", json={"name": "book", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_very_small_positive_price(self):
        """Test very small but positive price acceptance."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_very_large_price(self):
        """Test very large price values."""
        r = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99


class TestCreateItemNameValidation:
    """Test name field validation with various inputs."""

    def test_valid_name(self):
        """Test standard valid name."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_empty_string_name(self):
        """Test empty string as name."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        # Empty string is still a valid string in Pydantic
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_single_character_name(self):
        """Test single character name."""
        r = client.post("/items", json={"name": "A", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "A"

    def test_long_name(self):
        """Test very long name string."""
        long_name = "x" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_name_with_special_characters(self):
        """Test name with special characters."""
        r = client.post("/items", json={"name": "book!@#$%^&*()", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book!@#$%^&*()"

    def test_name_with_unicode(self):
        """Test name with unicode characters."""
        r = client.post("/items", json={"name": "本 书 📚", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "本 书 📚"

    def test_name_with_spaces(self):
        """Test name with spaces."""
        r = client.post("/items", json={"name": "my book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "my book"

    def test_name_with_newlines(self):
        """Test name with newline characters."""
        r = client.post("/items", json={"name": "line1\nline2", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "line1\nline2"


class TestCreateItemRequiredFields:
    """Test that required fields are validated properly."""

    def test_missing_name_field(self):
        """Test POST without name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Validation error
        assert "name" in str(r.json())

    def test_missing_price_field(self):
        """Test POST without price field."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422  # Validation error
        assert "price" in str(r.json())

    def test_missing_both_fields(self):
        """Test POST with empty JSON body."""
        r = client.post("/items", json={})
        assert r.status_code == 422  # Validation error


class TestCreateItemTypeValidation:
    """Test type validation for request fields."""

    def test_price_as_string(self):
        """Test price provided as string instead of number."""
        r = client.post("/items", json={"name": "book", "price": "10.5"})
        # Pydantic coerces string to float if possible
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_price_as_invalid_string(self):
        """Test price provided as non-numeric string."""
        r = client.post("/items", json={"name": "book", "price": "invalid"})
        assert r.status_code == 422

    def test_name_as_number(self):
        """Test name provided as number instead of string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic coerces number to string
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_name_as_null(self):
        """Test name as null value."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_price_as_null(self):
        """Test price as null value."""
        r = client.post("/items", json={"name": "book", "price": None})
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Test that response has expected structure and fields."""

    def test_response_has_id_field(self):
        """Test that response includes id field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert "id" in r.json()
        assert r.json()["id"] == 1

    def test_response_has_name_field(self):
        """Test that response includes name field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert "name" in r.json()

    def test_response_has_price_field(self):
        """Test that response includes price field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert "price" in r.json()

    def test_response_no_extra_fields(self):
        """Test response contains only expected fields."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_response_field_types(self):
        """Test that response fields have expected types."""
        r = client.post("/items", json={"name": "book", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestCreateItemContentType:
    """Test HTTP content type handling."""

    def test_json_content_type_header(self):
        """Test that default content type is JSON."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_response_is_json(self):
        """Test that response can be parsed as JSON."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        # Should not raise an exception
        json_data = r.json()
        assert json_data is not None
