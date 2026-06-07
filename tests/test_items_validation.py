import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemInputValidation:
    """Enhanced tests for POST /items endpoint input validation."""

    def test_create_item_with_negative_price(self):
        """Test that negative prices are rejected."""
        r = client.post("/items", json={"name": "negative", "price": -1})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_with_very_negative_price(self):
        """Test rejection of very negative prices."""
        r = client.post("/items", json={"name": "item", "price": -999.99})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_missing_price_field(self):
        """Test that missing price field returns 422 validation error."""
        r = client.post("/items", json={"name": "no_price"})
        assert r.status_code == 422

    def test_create_item_missing_name_field(self):
        """Test that missing name field returns 422 validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Test that empty object returns 422 validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_with_string_price(self):
        """Test that string price is rejected with validation error."""
        r = client.post("/items", json={"name": "item", "price": "not_a_number"})
        assert r.status_code == 422

    def test_create_item_with_null_price(self):
        """Test that null price is rejected with validation error."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_with_null_name(self):
        """Test that null name is rejected with validation error."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_with_empty_name(self):
        """Test that empty string name is accepted (no validation restriction)."""
        r = client.post("/items", json={"name": "", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_with_whitespace_name(self):
        """Test that whitespace-only name is accepted."""
        r = client.post("/items", json={"name": "   ", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_with_very_long_name(self):
        """Test that very long names are accepted."""
        long_name = "x" * 10000
        r = client.post("/items", json={"name": long_name, "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_special_characters_in_name(self):
        """Test that special characters in name are accepted."""
        r = client.post("/items", json={"name": "!@#$%^&*()_+-={}[]|:;<>?,.~`", "price": 5.0})
        assert r.status_code == 200
        assert "!@#$" in r.json()["name"]

    def test_create_item_with_unicode_name(self):
        """Test that unicode characters in name are accepted."""
        r = client.post("/items", json={"name": "中文书籍 📚", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == "中文书籍 📚"

    def test_create_item_with_very_large_price(self):
        """Test that very large prices are accepted."""
        r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999999.99

    def test_create_item_with_very_small_positive_price(self):
        """Test that very small positive prices are accepted."""
        r = client.post("/items", json={"name": "cheap", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_item_with_price_exactly_one(self):
        """Test boundary case where price is exactly 1."""
        r = client.post("/items", json={"name": "item", "price": 1})
        assert r.status_code == 200
        assert r.json()["price"] == 1

    def test_create_item_with_integer_price(self):
        """Test that integer prices are accepted and work correctly."""
        r = client.post("/items", json={"name": "item", "price": 50})
        assert r.status_code == 200
        assert r.json()["price"] == 50

    def test_create_item_with_float_price(self):
        """Test that float prices work correctly."""
        r = client.post("/items", json={"name": "item", "price": 19.99})
        assert r.status_code == 200
        assert r.json()["price"] == 19.99

    def test_create_item_with_extra_fields(self):
        """Test that extra fields in request are ignored gracefully."""
        r = client.post(
            "/items",
            json={"name": "item", "price": 10.0, "extra_field": "ignored", "another": 123}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "item"
        assert data["price"] == 10.0

    def test_create_item_with_numeric_name_field(self):
        """Test that numeric name is rejected with validation error."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_with_boolean_price(self):
        """Test that boolean price is rejected with validation error."""
        r = client.post("/items", json={"name": "item", "price": True})
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Tests for response structure and content."""

    def test_create_item_response_has_id(self):
        """Test that response contains 'id' field."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.status_code == 200
        assert "id" in r.json()
        assert r.json()["id"] == 1

    def test_create_item_response_has_name(self):
        """Test that response contains 'name' field."""
        r = client.post("/items", json={"name": "test_item", "price": 5.0})
        assert r.status_code == 200
        assert "name" in r.json()
        assert r.json()["name"] == "test_item"

    def test_create_item_response_has_price(self):
        """Test that response contains 'price' field."""
        r = client.post("/items", json={"name": "test", "price": 15.5})
        assert r.status_code == 200
        assert "price" in r.json()
        assert r.json()["price"] == 15.5

    def test_create_item_response_content_type(self):
        """Test that response has correct content type."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_create_item_status_code_is_200(self):
        """Test that successful creation returns 200 OK."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.status_code == 200


class TestCreateItemEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_item_with_zero_decimal_price(self):
        """Test that 0.0 price is rejected."""
        r = client.post("/items", json={"name": "item", "price": 0.0})
        assert r.status_code == 400

    def test_create_item_with_scientific_notation_price(self):
        """Test that scientific notation prices work."""
        r = client.post("/items", json={"name": "item", "price": 1e2})
        assert r.status_code == 200
        assert r.json()["price"] == 100.0

    def test_create_item_with_negative_scientific_notation_price(self):
        """Test that negative scientific notation prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": -1e2})
        assert r.status_code == 400

    def test_create_item_repeated_calls(self):
        """Test that repeated calls succeed independently."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i + 1)})
            assert r.status_code == 200
            assert r.json()["name"] == f"item_{i}"

    @pytest.mark.parametrize("price", [0.001, 0.1, 1.0, 10.5, 100, 1000.99])
    def test_create_item_with_various_positive_prices(self, price):
        """Test creation with various positive price values."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [-0.01, -0.1, -1, -10, -999.99])
    def test_create_item_with_various_negative_prices(self, price):
        """Test that various negative prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    @pytest.mark.parametrize("name", ["a", "ab", "abc", "x" * 100, "x" * 1000])
    def test_create_item_with_various_name_lengths(self, name):
        """Test creation with various name lengths."""
        r = client.post("/items", json={"name": name, "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == name
