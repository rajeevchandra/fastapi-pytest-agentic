import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price input validation for create_item endpoint."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 99999.99, 1000000])
    def test_create_item_accepts_valid_prices(self, price):
        """Test that valid positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_float_precision(self):
        """Test price with float precision edge case."""
        price = 10.999999
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert abs(r.json()["price"] - price) < 0.0001


class TestCreateItemNameValidation:
    """Test name input validation for create_item endpoint."""

    @pytest.mark.parametrize("name", ["", " ", "  "])
    def test_create_item_with_empty_or_whitespace_names(self, name):
        """Test that empty/whitespace names are handled (Pydantic accepts them by default)."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", ["A", "ab", "test item", "Test Item 123"])
    def test_create_item_with_valid_names(self, name):
        """Test that various valid names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_very_long_name(self):
        """Test with extremely long name."""
        long_name = "x" * 5000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    @pytest.mark.parametrize("name", [
        "name-with-dashes",
        "name_with_underscores",
        "name.with.dots",
        "name/with/slashes",
        "name!@#$%",
        "名前",
        "🎉emoji🎉"
    ])
    def test_create_item_with_special_characters(self, name):
        """Test that special characters in names are handled."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Test missing required fields for create_item endpoint."""

    def test_create_item_missing_price_field(self):
        """Test that missing price field returns validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422  # Pydantic validation error

    def test_create_item_missing_name_field(self):
        """Test that missing name field returns validation error."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422  # Pydantic validation error

    def test_create_item_missing_both_fields(self):
        """Test that missing both fields returns validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_with_null_values(self):
        """Test that null values for required fields return validation error."""
        r = client.post("/items", json={"name": None, "price": 10})
        assert r.status_code == 422

    def test_create_item_with_null_price(self):
        """Test that null price returns validation error."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for create_item endpoint."""

    def test_create_item_price_as_string(self):
        """Test that string price is rejected (or auto-converted if Pydantic allows)."""
        r = client.post("/items", json={"name": "test", "price": "10"})
        # Pydantic may auto-convert string to float
        if r.status_code == 200:
            assert r.json()["price"] == 10.0
        else:
            assert r.status_code == 422

    def test_create_item_price_as_boolean(self):
        """Test that boolean price is handled."""
        r = client.post("/items", json={"name": "test", "price": True})
        # Pydantic may convert boolean to 1
        if r.status_code == 200:
            # In Python, True == 1
            assert r.json()["price"] in [1, True]
        else:
            assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Test that number as name is handled."""
        r = client.post("/items", json={"name": 123, "price": 10})
        # Pydantic may auto-convert to string
        if r.status_code == 200:
            assert r.json()["name"] in [123, "123"]
        else:
            assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_fields(self):
        """Test that extra fields are ignored or handled gracefully."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10,
            "description": "extra field",
            "category": "books"
        })
        assert r.status_code == 200
        assert r.json()["name"] == "test"
        assert r.json()["price"] == 10

    def test_create_item_with_extra_numeric_field(self):
        """Test extra numeric field handling."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10,
            "quantity": 5
        })
        assert r.status_code == 200


class TestCreateItemEdgeCases:
    """Test edge cases for create_item endpoint."""

    def test_create_item_response_has_required_fields(self):
        """Test that response includes all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_id_is_always_one(self):
        """Test that created item always has id=1."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @pytest.mark.parametrize("price", [0.001, 0.0001, 0.00001])
    def test_create_item_with_tiny_prices(self, price):
        """Test with very small positive prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price
