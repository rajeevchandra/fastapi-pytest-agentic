import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Boundary testing for price parameter validation."""

    @pytest.mark.parametrize("price", [
        -1.0,           # negative
        -100.0,         # large negative
        -0.01,          # small negative
        0,              # zero (already tested but included for completeness)
    ])
    def test_create_item_negative_and_zero_prices(self, price):
        """Verify that negative and zero prices are rejected with 400 status."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [
        0.01,           # very small positive
        0.001,          # tiny positive
        1.0,            # standard
        10.5,           # decimal
        99999.99,       # very large
        1000000.0,      # very very large
    ])
    def test_create_item_valid_positive_prices(self, price):
        """Verify that positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["name"] == "test"
        assert data["id"] == 1

    @pytest.mark.parametrize("price", [
        float('inf'),       # infinity
        float('-inf'),      # negative infinity
        float('nan'),       # NaN
    ])
    def test_create_item_special_float_values(self, price):
        """Verify that special float values (inf, -inf, nan) are handled."""
        # Note: These may be rejected by Pydantic or JSON serialization
        r = client.post("/items", json={"name": "test", "price": price})
        # Should either be rejected or handled appropriately
        # FastAPI/Pydantic may reject these
        assert r.status_code in [400, 422]


class TestCreateItemNameValidation:
    """Boundary testing for name parameter validation."""

    @pytest.mark.parametrize("name", [
        "",                                # empty string
        " ",                               # single space
        "   ",                             # multiple spaces
        "\t",                              # tab
        "\n",                              # newline
    ])
    def test_create_item_empty_or_whitespace_names(self, name):
        """Verify that empty or whitespace-only names are accepted by FastAPI."""
        # Note: Pydantic doesn't validate string length by default
        # These will be accepted by the API
        r = client.post("/items", json={"name": name, "price": 1.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 1.0

    @pytest.mark.parametrize("name", [
        "a",                                           # single char
        "Book",                                        # normal
        "Product with spaces",                         # spaces
        "Item-123",                                    # hyphens
        "Item_456",                                    # underscores
        "item@example.com",                            # special chars
        "Item #1 (Premium)",                           # mixed special chars
        "Café",                                        # unicode
        "日本語",                                        # Japanese
        "😀 Emoji Item",                               # emoji
        "a" * 100,                                     # 100 chars
        "a" * 500,                                     # 500 chars
        "a" * 1000,                                    # 1000 chars
    ])
    def test_create_item_various_valid_names(self, name):
        """Verify that diverse name values are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 10.0


class TestCreateItemMissingFields:
    """Test missing required fields in request."""

    def test_create_item_missing_price(self):
        """Verify that missing price field returns validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422  # Validation error
        assert "price" in str(r.json())

    def test_create_item_missing_name(self):
        """Verify that missing name field returns validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Validation error
        assert "name" in str(r.json())

    def test_create_item_missing_both_fields(self):
        """Verify that missing all fields returns validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422  # Validation error

    def test_create_item_empty_json(self):
        """Verify that empty JSON body returns validation error."""
        r = client.post("/items")
        assert r.status_code == 422  # Validation error


class TestCreateItemInvalidTypes:
    """Test invalid data types for request fields."""

    def test_create_item_price_as_string(self):
        """Verify that string price is handled by Pydantic validation."""
        r = client.post("/items", json={"name": "test", "price": "ten"})
        assert r.status_code == 422  # Validation error - string cannot convert to float

    def test_create_item_price_as_null(self):
        """Verify that null price is rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422  # Validation error

    def test_create_item_name_as_number(self):
        """Verify that numeric name is accepted (Pydantic coerces to string)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic will coerce 123 to "123"
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "123"

    def test_create_item_name_as_null(self):
        """Verify that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422  # Validation error

    def test_create_item_price_as_list(self):
        """Verify that list price is rejected."""
        r = client.post("/items", json={"name": "test", "price": [10, 20]})
        assert r.status_code == 422  # Validation error

    def test_create_item_extra_fields_ignored(self):
        """Verify that extra fields are ignored by Pydantic."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should be ignored",
            "another_field": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test"
        assert data["price"] == 10.0
        assert "extra_field" not in data
        assert "another_field" not in data


class TestCreateItemResponseStructure:
    """Test response structure and field types."""

    def test_create_item_response_has_required_fields(self):
        """Verify that response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Verify that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_id_is_one(self):
        """Verify that created item has id = 1."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_create_item_echo_name(self):
        """Verify that response echoes the provided name."""
        name = "Special Book Title 📚"
        r = client.post("/items", json={"name": name, "price": 15.99})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name

    def test_create_item_echo_price(self):
        """Verify that response echoes the provided price."""
        price = 99.99
        r = client.post("/items", json={"name": "book", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price


class TestCreateItemErrorHandling:
    """Test error handling and error messages."""

    def test_error_response_has_detail_field(self):
        """Verify that error responses have a detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_validation_error_response_structure(self):
        """Verify that validation errors have expected structure."""
        r = client.post("/items", json={"name": "test"})  # missing price
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_price_error_message_clarity(self):
        """Verify that price error message is clear."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail or "positive" in detail.lower()

    def test_multiple_requests_same_response(self):
        """Verify that multiple similar requests get similar responses."""
        for price in [-1, -10, 0]:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert "price" in r.json()["detail"].lower()
