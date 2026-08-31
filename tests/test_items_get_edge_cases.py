"""
Edge cases and integration tests for items API.
Tests path parameter boundaries, integration scenarios, and complex edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_accepts_valid_id(self, item_id):
        """Valid item_id (1) should be accepted."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0, 2, -1, 999999, 2147483647])
    def test_get_item_returns_404_for_invalid_ids(self, item_id):
        """Item IDs other than 1 should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_with_negative_id(self):
        """Negative item IDs should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_with_zero_id(self):
        """Zero item ID should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_with_max_int_id(self):
        """Very large integer IDs should return 404."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404


class TestCreateItemWithVariousPrices:
    """Test create_item with various price values."""

    @pytest.mark.parametrize("price", [
        0.01,           # minimum valid
        0.1,            # decimal
        1,              # integer
        1.5,            # float
        100,            # large integer
        100.50,         # large decimal
        999999.99,      # very large
        1e6,            # scientific notation large
    ])
    def test_create_item_with_valid_prices(self, price):
        """All valid positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [
        -0.01,          # small negative
        -1,             # negative integer
        -100.5,         # negative decimal
        -1e10,          # scientific notation negative
    ])
    def test_create_item_with_negative_prices(self, price):
        """All negative prices should be rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestCreateItemWithVariousNames:
    """Test create_item with various name values."""

    @pytest.mark.parametrize("name", [
        "a",                        # single character
        "ab",                       # two characters
        "item",                     # simple
        "Item Name",                # with space
        "item-123",                 # with hyphen
        "item_name",                # with underscore
        "Item 123",                 # numbers and space
        "book (hardcover)",         # parentheses
        "item@store",               # special chars
        "名前",                      # unicode
        "🎉 Party",                 # emoji
        "x" * 50,                   # medium length
        "x" * 200,                  # long string
    ])
    def test_create_item_with_various_valid_names(self, name):
        """Various valid names should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestPriceEdgeCases:
    """Test boundary conditions for price validation."""

    def test_price_exactly_zero_rejected(self):
        """Price of exactly 0 should be rejected."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_price_just_above_zero_accepted(self):
        """Price just above zero (0.01) should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200

    def test_price_very_small_accepted(self):
        """Very small positive price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200

    def test_price_very_large_accepted(self):
        """Very large price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 1e15})
        assert r.status_code == 200


class TestRequestResponseCycle:
    """Test complete request-response cycles."""

    def test_create_then_get_same_item(self):
        """Creating an item with id=1 then getting it returns same data."""
        # Create
        create_r = client.post("/items", json={"name": "test-item", "price": 25.50})
        assert create_r.status_code == 200
        create_data = create_r.json()
        
        # Get the same item
        get_r = client.get(f"/items/{create_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()
        
        # Compare
        assert create_data["id"] == get_data["id"]
        assert create_data["name"] == get_data["name"]
        assert create_data["price"] == get_data["price"]

    def test_multiple_creates_return_different_data(self):
        """Multiple create requests with different data return correct responses."""
        # First create
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        data1 = r1.json()
        
        # Second create
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        data2 = r2.json()
        
        # Names should differ
        assert data1["name"] != data2["name"]
        assert data1["price"] != data2["price"]


class TestErrorRecovery:
    """Test API behavior after errors."""

    def test_api_recovers_after_invalid_create(self):
        """API should work normally after an invalid request."""
        # Invalid request
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400
        
        # Valid request after
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200

    def test_api_recovers_after_missing_item_get(self):
        """API should work normally after a 404 GET."""
        # 404 request
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Valid request after
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_get_missing_item_multiple_times(self):
        """Getting missing item multiple times consistently returns 404."""
        for _ in range(3):
            r = client.get("/items/999")
            assert r.status_code == 404


class TestTypeCoercion:
    """Test Pydantic's type coercion behavior."""

    def test_string_number_price_coerced_to_float(self):
        """Numeric string price should be coerced to float."""
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5
        assert isinstance(r.json()["price"], float)

    def test_integer_price_accepted(self):
        """Integer price should be accepted and preserved."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200
        assert r.json()["price"] == 10


class TestResponseConsistency:
    """Test consistency of API responses."""

    def test_multiple_gets_of_same_item_consistent(self):
        """Multiple GET requests for same item return identical data."""
        results = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            results.append(r.json())
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[0] == results[i]

    def test_error_responses_consistent(self):
        """Error responses for same request are consistent."""
        results = []
        for _ in range(3):
            r = client.post("/items", json={"name": "item", "price": 0})
            assert r.status_code == 400
            results.append(r.json()["detail"])
        
        # All error messages should be identical
        for i in range(1, len(results)):
            assert results[0] == results[i]


class TestResponseFieldPresence:
    """Test that all expected fields are present in responses."""

    def test_create_success_response_has_all_fields(self):
        """Successful create response has id, name, price."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert all(field in data for field in ["id", "name", "price"])

    def test_get_success_response_has_all_fields(self):
        """Successful get response has id, name, price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert all(field in data for field in ["id", "name", "price"])

    def test_error_response_has_detail(self):
        """Error responses include detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "detail" in r.json()


class TestBoundaryBehavior:
    """Test behavior at API boundaries."""

    def test_boundary_id_zero_not_found(self):
        """Item ID 0 should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_boundary_id_one_found(self):
        """Item ID 1 should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_boundary_id_two_not_found(self):
        """Item ID 2 should return 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_boundary_price_zero_rejected(self):
        """Price 0 should be rejected."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_boundary_price_near_zero_accepted(self):
        """Price 0.00001 should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.00001})
        assert r.status_code == 200
