import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Tests for price field validation in create_item endpoint."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_item_rejects_non_positive_price(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize(
        "price",
        [0.01, 1, 100, 1000.99, 999999.99, 1e6, 1e10],
    )
    def test_create_item_accepts_valid_prices(self, price):
        """Test that positive prices are accepted."""
        r = client.post("/items", json={"name": "valid", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["id"] == 1
        assert data["name"] == "valid"

    def test_create_item_price_boundary_minimum_valid(self):
        """Test the minimum valid price (just above 0)."""
        r = client.post("/items", json={"name": "boundary", "price": 0.01})
        assert r.status_code == 200

    def test_create_item_price_boundary_maximum(self):
        """Test very large price values."""
        r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
        assert r.status_code == 200


class TestCreateItemNameValidation:
    """Tests for name field validation in create_item endpoint."""

    def test_create_item_empty_name(self):
        """Test that empty name is accepted by FastAPI but stored."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_single_character_name(self):
        """Test single character name."""
        r = client.post("/items", json={"name": "A", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "A"

    def test_create_item_long_name(self):
        """Test very long name (500+ characters)."""
        long_name = "x" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_special_characters_name(self):
        """Test name with special characters."""
        special_names = [
            "test@123",
            "item-with-dash",
            "item_with_underscore",
            "Item!With#Special$Chars",
            "item.with.dots",
            "item/with/slashes",
        ]
        for name in special_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_unicode_name(self):
        """Test name with unicode characters."""
        unicode_names = [
            "café",
            "日本語",
            "🎉 party 🎉",
            "Здравствуй",
            "mañana",
        ]
        for name in unicode_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_whitespace_name(self):
        """Test name with whitespace variations."""
        whitespace_names = [
            " ",
            "  ",
            "name with spaces",
            "  leading",
            "trailing  ",
            "  both  ",
            "\t",
            "\n",
        ]
        for name in whitespace_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Tests for missing required fields."""

    def test_create_item_missing_name(self):
        """Test request missing name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Unprocessable Entity

    def test_create_item_missing_price(self):
        """Test request missing price field."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Test request with neither required field."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Test request with null name."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test request with null price."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Tests for incorrect data types."""

    def test_create_item_price_as_string(self):
        """Test price provided as string instead of number."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        assert r.status_code == 422

    def test_create_item_price_as_string_non_numeric(self):
        """Test price as non-numeric string."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Test name provided as number instead of string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # FastAPI may coerce this or reject it
        result = r.json()
        # Just verify the response is reasonable
        assert r.status_code in [200, 422]

    def test_create_item_name_as_list(self):
        """Test name provided as list."""
        r = client.post("/items", json={"name": ["a", "b"], "price": 10.0})
        assert r.status_code == 422

    def test_create_item_price_as_array(self):
        """Test price provided as array."""
        r = client.post("/items", json={"name": "test", "price": [10, 20]})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Tests for extra/unexpected fields in request."""

    def test_create_item_with_extra_field(self):
        """Test request with extra field."""
        r = client.post(
            "/items",
            json={"name": "test", "price": 10.0, "extra": "field"},
        )
        # FastAPI by default ignores extra fields
        assert r.status_code == 200
        assert r.json()["name"] == "test"

    def test_create_item_with_multiple_extra_fields(self):
        """Test request with multiple extra fields."""
        r = client.post(
            "/items",
            json={
                "name": "test",
                "price": 10.0,
                "extra1": "value1",
                "extra2": "value2",
                "id": 999,  # Try to set id
            },
        )
        # Extra fields should be ignored
        assert r.status_code == 200
        # id should be 1 from the API, not 999
        assert r.json()["id"] == 1
