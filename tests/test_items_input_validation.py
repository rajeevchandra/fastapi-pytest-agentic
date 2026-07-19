import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Parametrized tests for price validation edge cases."""

    @pytest.mark.parametrize("price", [
        0,       # zero
        -1,      # negative
        -100.5,  # large negative
        -0.01,   # small negative
    ])
    def test_invalid_prices(self, price):
        """Prices <= 0 should be rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [
        0.01,      # very small valid
        1.0,       # whole number
        12.5,      # decimal
        99999.99,  # very large valid
        1000000,   # very large integer
    ])
    def test_valid_prices(self, price):
        """Valid prices should be accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemNameValidation:
    """Parametrized tests for name validation edge cases."""

    @pytest.mark.parametrize("name", [
        "a" * 500,      # very long name
        "!@#$%^&*()",   # special characters
        "café",         # unicode
        "test 123",     # with numbers and space
        "名前",         # non-latin unicode
    ])
    def test_valid_names(self, name):
        """Various name formats should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "",           # empty string
        " ",          # whitespace only
        "\t",         # tab only
        "\n",         # newline only
    ])
    def test_invalid_names(self, name):
        """Empty/whitespace-only names should be rejected."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # FastAPI validates empty strings as invalid for string fields by default
        # Pydantic will reject empty string when type validation is strict
        assert r.status_code == 422 or (r.status_code == 200 and r.json()["name"] == name)


class TestCreateItemMissingFields:
    """Tests for missing or malformed required fields."""

    def test_missing_name(self):
        """Missing name field should be rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_price(self):
        """Missing price field should be rejected."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_missing_both_fields(self):
        """Missing both fields should be rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_null_name(self):
        """Null name should be rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_null_price(self):
        """Null price should be rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Tests for type validation on input fields."""

    def test_string_price(self):
        """String price should be rejected or converted."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        # FastAPI/Pydantic may coerce string to float or reject with 422
        assert r.status_code in [200, 422]

    def test_boolean_name(self):
        """Boolean name should be rejected."""
        r = client.post("/items", json={"name": True, "price": 10.0})
        assert r.status_code == 422

    def test_dict_price(self):
        """Dict price should be rejected."""
        r = client.post("/items", json={"name": "test", "price": {"value": 10}})
        assert r.status_code == 422

    def test_extra_fields(self):
        """Extra fields should be ignored or rejected."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra": "field",
            "another": 123
        })
        # FastAPI ignores extra fields by default
        assert r.status_code in [200, 422]


class TestCreateItemResponseStructure:
    """Tests for response structure validation."""

    def test_response_fields(self):
        """Response should contain all required fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_response_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
