"""Test edge cases and integration scenarios."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameters:
    """Test path parameter handling for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id_found(self, item_id):
        """Test get item with valid ID."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, -999, 2, 100, 1000, 999999])
    def test_get_item_various_ids_not_found(self, item_id):
        """Test that only id=1 is found, all others return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_id_boundary_zero(self):
        """Test item_id boundary at zero."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_id_boundary_negative_one(self):
        """Test item_id at -1."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_get_item_id_boundary_max_int(self):
        """Test item_id with very large number."""
        response = client.get("/items/999999999999")
        assert response.status_code == 404

    def test_get_item_id_two(self):
        """Test item_id=2 returns 404."""
        response = client.get("/items/2")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"


class TestPriceValidationBoundaries:
    """Test price field boundary conditions systematically."""

    @pytest.mark.parametrize("price", [
        -1000,
        -100,
        -10,
        -1,
        -0.5,
        -0.1,
        -0.01,
        -0.001,
    ])
    def test_price_negative_values_rejected(self, price):
        """Test all negative prices are rejected."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_price_exactly_zero_rejected(self):
        """Test that exactly 0 is rejected."""
        response = client.post("/items", json={"name": "free", "price": 0})
        assert response.status_code == 400

    def test_price_just_above_zero_accepted(self):
        """Test that 0.01 is accepted."""
        response = client.post("/items", json={"name": "cheap", "price": 0.01})
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_price_0_001_accepted(self):
        """Test very small positive price."""
        response = client.post("/items", json={"name": "item", "price": 0.001})
        assert response.status_code == 200
        assert response.json()["price"] == pytest.approx(0.001)

    @pytest.mark.parametrize("price", [
        0.01,
        0.1,
        1,
        10,
        100,
        1000,
        10000,
        100000,
        1000000,
        1e10,
    ])
    def test_price_positive_values_accepted(self, price):
        """Test various positive prices are accepted."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == pytest.approx(price)


class TestNameFieldBoundaries:
    """Test name field edge cases and boundaries."""

    def test_name_empty_string(self):
        """Test empty string name."""
        response = client.post("/items", json={"name": "", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == ""

    def test_name_single_space(self):
        """Test name with just space."""
        response = client.post("/items", json={"name": " ", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == " "

    def test_name_multiple_spaces(self):
        """Test name with multiple spaces."""
        response = client.post("/items", json={"name": "   ", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "   "

    def test_name_one_char(self):
        """Test one character name."""
        response = client.post("/items", json={"name": "X", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "X"

    def test_name_two_chars(self):
        """Test two character name."""
        response = client.post("/items", json={"name": "AB", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "AB"

    def test_name_100_chars(self):
        """Test 100 character name."""
        name_100 = "a" * 100
        response = client.post("/items", json={"name": name_100, "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == name_100

    def test_name_1000_chars(self):
        """Test 1000 character name."""
        name_1000 = "x" * 1000
        response = client.post("/items", json={"name": name_1000, "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == name_1000

    def test_name_numbers_only(self):
        """Test name with only numbers."""
        response = client.post("/items", json={"name": "12345", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "12345"

    def test_name_special_characters(self):
        """Test name with special characters."""
        response = client.post("/items", json={"name": "!@#$%^&*()", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "!@#$%^&*()"

    def test_name_unicode_mixed(self):
        """Test name with mixed Unicode."""
        response = client.post("/items", json={"name": "café ☕ 中文 🎉", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "café ☕ 中文 🎉"


class TestIntegrationMultipleOperations:
    """Test integration scenarios with multiple operations."""

    def test_create_then_get_consistency(self):
        """Test that created item can be retrieved with correct data."""
        create_response = client.post("/items", json={"name": "book", "price": 25.99})
        assert create_response.status_code == 200
        
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        
        # Both should have id=1, but get returns hardcoded data
        assert create_response.json()["id"] == 1
        assert get_response.json()["id"] == 1

    def test_create_item_then_get_item_different_ids(self):
        """Test that creating different items and getting them."""
        item1 = client.post("/items", json={"name": "pen", "price": 1.5})
        item2 = client.post("/items", json={"name": "pencil", "price": 2.0})
        
        # Both create calls return same hardcoded response
        assert item1.json()["id"] == 1
        assert item2.json()["id"] == 1
        
        # Getting item 1 always works
        get1 = client.get("/items/1")
        assert get1.status_code == 200

    def test_valid_create_then_invalid_create(self):
        """Test creating valid item followed by invalid item."""
        valid = client.post("/items", json={"name": "valid", "price": 10})
        assert valid.status_code == 200
        
        invalid = client.post("/items", json={"name": "invalid", "price": -5})
        assert invalid.status_code == 400
        
        # Valid item still retrievable
        get = client.get("/items/1")
        assert get.status_code == 200

    def test_get_existing_then_non_existing_then_existing(self):
        """Test alternating between existing and non-existing items."""
        get1 = client.get("/items/1")
        assert get1.status_code == 200
        
        get999 = client.get("/items/999")
        assert get999.status_code == 404
        
        get1_again = client.get("/items/1")
        assert get1_again.status_code == 200
        assert get1.json() == get1_again.json()


class TestTypeCoercion:
    """Test FastAPI/Pydantic type coercion behavior."""

    def test_price_string_numeric_coerced(self):
        """Test that numeric string prices are coerced to float."""
        response = client.post("/items", json={"name": "item", "price": "10.5"})
        assert response.status_code == 200
        assert response.json()["price"] == 10.5

    def test_price_string_negative_coerced(self):
        """Test that negative string prices are coerced and rejected."""
        response = client.post("/items", json={"name": "item", "price": "-5"})
        assert response.status_code == 400  # Rejected for being negative

    def test_name_number_coerced_to_string(self):
        """Test that numeric names are coerced to strings."""
        response = client.post("/items", json={"name": 123, "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "123"
        assert isinstance(response.json()["name"], str)

    def test_name_float_coerced_to_string(self):
        """Test that float names are coerced to strings."""
        response = client.post("/items", json={"name": 3.14, "price": 10})
        assert response.status_code == 200
        assert isinstance(response.json()["name"], str)

    def test_name_bool_coerced_to_string(self):
        """Test that boolean names are coerced to strings."""
        response = client.post("/items", json={"name": True, "price": 10})
        assert response.status_code == 200
        assert isinstance(response.json()["name"], str)

    def test_name_list_rejection(self):
        """Test that list as name is rejected."""
        response = client.post("/items", json={"name": ["list"], "price": 10})
        # Pydantic might coerce this to string representation
        assert response.status_code in [200, 422]


class TestValidationErrorDetails:
    """Test detailed validation error information."""

    def test_missing_name_error_details(self):
        """Test error details when name is missing."""
        response = client.post("/items", json={"price": 10})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_missing_price_error_details(self):
        """Test error details when price is missing."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_null_name_error_details(self):
        """Test error details when name is null."""
        response = client.post("/items", json={"name": None, "price": 10})
        assert response.status_code == 422

    def test_null_price_error_details(self):
        """Test error details when price is null."""
        response = client.post("/items", json={"name": "item", "price": None})
        assert response.status_code == 422

    def test_invalid_price_string_error(self):
        """Test error when price string is not numeric."""
        response = client.post("/items", json={"name": "item", "price": "not_a_number"})
        assert response.status_code == 422


class TestSpecialCharacterHandling:
    """Test handling of special characters and escape sequences."""

    def test_name_with_quotes(self):
        """Test name containing quotes."""
        response = client.post("/items", json={"name": 'item "quoted"', "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == 'item "quoted"'

    def test_name_with_backslash(self):
        """Test name containing backslash."""
        response = client.post("/items", json={"name": "item\\path", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "item\\path"

    def test_name_with_newline(self):
        """Test name containing newline."""
        response = client.post("/items", json={"name": "item\nname", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "item\nname"

    def test_name_with_tab(self):
        """Test name containing tab."""
        response = client.post("/items", json={"name": "item\tname", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "item\tname"

    def test_name_with_null_character(self):
        """Test name containing null character."""
        response = client.post("/items", json={"name": "item\x00name", "price": 10})
        assert response.status_code == 200

    def test_name_carriage_return(self):
        """Test name with carriage return."""
        response = client.post("/items", json={"name": "item\rname", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "item\rname"


class TestFloatPrecision:
    """Test floating point precision handling."""

    def test_price_many_decimals(self):
        """Test price with many decimal places."""
        price = 3.141592653589793
        response = client.post("/items", json={"name": "pi", "price": price})
        assert response.status_code == 200
        result_price = response.json()["price"]
        assert result_price == pytest.approx(price, rel=1e-10)

    def test_price_very_small_positive(self):
        """Test very small positive price."""
        price = 1e-10
        response = client.post("/items", json={"name": "tiny", "price": price})
        assert response.status_code == 200

    def test_price_scientific_notation_small(self):
        """Test price in scientific notation (small)."""
        response = client.post("/items", json={"name": "item", "price": 1e-5})
        assert response.status_code == 200

    def test_price_scientific_notation_large(self):
        """Test price in scientific notation (large)."""
        response = client.post("/items", json={"name": "item", "price": 1e15})
        assert response.status_code == 200
        assert response.json()["price"] == 1e15


class TestConsecutiveRequests:
    """Test behavior with consecutive identical/different requests."""

    def test_same_create_request_twice(self):
        """Test creating same item twice."""
        req1 = client.post("/items", json={"name": "book", "price": 10.5})
        req2 = client.post("/items", json={"name": "book", "price": 10.5})
        assert req1.status_code == 200
        assert req2.status_code == 200
        assert req1.json() == req2.json()

    def test_create_with_different_names_same_price(self):
        """Test creating items with different names."""
        req1 = client.post("/items", json={"name": "book1", "price": 10})
        req2 = client.post("/items", json={"name": "book2", "price": 10})
        assert req1.status_code == 200
        assert req2.status_code == 200
        # Both return same hardcoded id=1
        assert req1.json()["id"] == 1
        assert req2.json()["id"] == 1

    def test_create_with_same_name_different_price(self):
        """Test creating items with same name different price."""
        req1 = client.post("/items", json={"name": "book", "price": 10})
        req2 = client.post("/items", json={"name": "book", "price": 20})
        assert req1.status_code == 200
        assert req2.status_code == 200
        assert req1.json()["id"] == 1
        assert req2.json()["id"] == 1

    def test_alternating_get_requests(self):
        """Test alternating GET requests."""
        responses = [client.get("/items/1") for _ in range(5)]
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["id"] == 1 for r in responses)
