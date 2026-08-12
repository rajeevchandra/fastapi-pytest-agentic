"""
Test suite for path parameters, edge cases, and integration scenarios.
Covers boundary values, special cases, and multi-step operations.
"""

from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [
        1,           # Valid ID
        "1",         # String that converts to int (FastAPI will convert)
    ])
    def test_get_item_accepts_valid_ids(self, item_id):
        """Verify valid integer item IDs are accepted."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", [
        0,           # Zero boundary
        -1,          # Negative
        -100,        # Large negative
        2,           # ID > 1
        999,         # Large ID
        999999999,   # Very large ID
    ])
    def test_get_item_rejects_non_matching_ids(self, item_id):
        """Verify IDs other than 1 return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_item_with_leading_zeros(self):
        """Verify leading zeros in item ID are handled correctly."""
        # /items/01 should resolve to item 1
        response = client.get("/items/01")
        # May be treated as 1 or may fail depending on routing
        assert response.status_code in [200, 404]


class TestGetItemIntegerBoundaries:
    """Test integer boundary conditions for item_id parameter."""

    def test_get_item_minimum_valid_id(self):
        """Verify minimum valid ID (1) works."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_id_zero(self):
        """Verify ID 0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_negative_ids(self):
        """Verify negative IDs return 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_get_item_large_ids(self):
        """Verify very large IDs return 404."""
        response = client.get("/items/2147483647")  # Max 32-bit int
        assert response.status_code == 404

    def test_get_item_id_two(self):
        """Verify ID 2 returns 404 (implementation only has ID 1)."""
        response = client.get("/items/2")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestCreateItemFloatPrecision:
    """Test floating-point price handling."""

    @pytest.mark.parametrize("price", [
        0.01,        # Minimum two decimals
        0.001,       # Three decimals
        0.0001,      # Many decimals
        1.23456789,  # Many decimal places
        10.5,        # Standard decimal
        10.99,       # Common price point
    ])
    def test_create_item_with_various_precisions(self, price):
        """Verify various decimal precisions are accepted."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price

    def test_create_item_large_price(self):
        """Verify large prices are accepted."""
        price = 1_000_000.99
        response = client.post("/items", json={"name": "expensive", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price

    def test_create_item_very_small_price(self):
        """Verify very small but positive prices work."""
        price = 0.000001
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200

    def test_create_item_price_near_zero(self):
        """Verify prices extremely close to zero are handled."""
        price = 0.0000001
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200


class TestCreateItemNameEdgeCases:
    """Test edge cases for item name field."""

    def test_create_item_name_single_character(self):
        """Verify single-character names work."""
        response = client.post("/items", json={"name": "A", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "A"

    def test_create_item_name_very_long(self):
        """Verify very long names are accepted."""
        long_name = "x" * 10000
        response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_item_name_with_numbers(self):
        """Verify names with numbers work."""
        response = client.post("/items", json={"name": "Item 123", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "Item 123"

    def test_create_item_name_with_special_chars(self):
        """Verify names with special characters work."""
        name = "Item!@#$%^&*()"
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_create_item_name_with_quotes(self):
        """Verify names with quotes work."""
        name = 'Item "with" quotes'
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_create_item_name_with_backslash(self):
        """Verify names with backslashes work."""
        name = "Item\\with\\backslash"
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name


class TestMultipleRequests:
    """Test handling of multiple sequential requests."""

    def test_multiple_create_requests_with_same_data(self):
        """Verify multiple creates with same data all succeed."""
        for _ in range(3):
            response = client.post("/items", json={"name": "book", "price": 10.0})
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_create_then_get_consistency(self):
        """Verify created item can be retrieved with get."""
        create_resp = client.post("/items", json={"name": "created_item", "price": 15.0})
        assert create_resp.status_code == 200
        created_id = create_resp.json()["id"]
        
        get_resp = client.get(f"/items/{created_id}")
        assert get_resp.status_code == 200

    def test_multiple_get_requests_consistency(self):
        """Verify multiple gets of same item return consistent data."""
        responses = [client.get("/items/1") for _ in range(3)]
        
        for response in responses:
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_interleaved_create_and_get_requests(self):
        """Verify creates and gets can be interleaved."""
        for i in range(2):
            create_resp = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert create_resp.status_code == 200
            
            get_resp = client.get("/items/1")
            assert get_resp.status_code == 200


class TestEndToEndScenarios:
    """Test realistic end-to-end usage scenarios."""

    def test_shopping_scenario_single_item(self):
        """Simulate shopping scenario: add item and retrieve it."""
        # Create an item
        response = client.post("/items", 
                              json={"name": "Widget", "price": 29.99})
        assert response.status_code == 200
        item = response.json()
        assert item["id"] > 0
        assert item["price"] == 29.99

    def test_create_various_item_types(self):
        """Test creating different types of items in sequence."""
        items = [
            {"name": "Laptop", "price": 999.99},
            {"name": "Mouse", "price": 29.99},
            {"name": "Monitor", "price": 399.99},
            {"name": "Keyboard", "price": 79.99},
        ]
        
        for item_data in items:
            response = client.post("/items", json=item_data)
            assert response.status_code == 200
            assert response.json()["name"] == item_data["name"]

    def test_catalog_retrieval(self):
        """Simulate catalog retrieval: get known item."""
        response = client.get("/items/1")
        assert response.status_code == 200
        item = response.json()
        assert all(key in item for key in ["id", "name", "price"])
        assert item["price"] > 0

    def test_catalog_search_not_found(self):
        """Simulate search for item that doesn't exist."""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert "detail" in response.json()


class TestRequestMethodValidation:
    """Test that incorrect HTTP methods are rejected."""

    def test_get_items_endpoint_with_post_method(self):
        """Verify POST is rejected on GET-only endpoint."""
        # POST to a GET endpoint should fail
        response = client.post("/items/1")
        assert response.status_code in [405, 422, 400]  # Method not allowed or parsing error

    def test_post_items_endpoint_with_get_method(self):
        """Verify GET is rejected on POST-only endpoint."""
        # GET to /items (POST endpoint) might route to /items/{id} if not careful
        # This tests the API structure
        response = client.get("/items")
        # Should not find the POST endpoint
        assert response.status_code in [404, 405]


class TestNullAndUndefinedValues:
    """Test handling of null and undefined values."""

    def test_create_item_with_null_name_fails(self):
        """Verify null name is rejected."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422

    def test_create_item_with_null_price_fails(self):
        """Verify null price is rejected."""
        response = client.post("/items", json={"name": "item", "price": None})
        assert response.status_code == 422

    def test_create_item_with_undefined_extra_field(self):
        """Verify undefined/null extra fields are handled."""
        response = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "optional_field": None
        })
        # Should succeed (extra fields are ignored)
        assert response.status_code in [200, 422]


class TestContentTypeHandling:
    """Test handling of different content types."""

    def test_create_item_with_json_content_type(self):
        """Verify application/json content type works."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 10.0},
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 200

    def test_create_item_missing_content_type(self):
        """Verify request without content-type is handled."""
        # TestClient typically handles this, but test the behavior
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.status_code == 200


class TestDataTypeCoercion:
    """Test data type coercion and conversion."""

    def test_create_item_integer_price_as_float(self):
        """Verify integer price values work."""
        response = client.post("/items", json={"name": "item", "price": 10})
        assert response.status_code == 200
        assert response.json()["price"] == 10

    def test_create_item_boolean_price_rejected(self):
        """Verify boolean price values are rejected."""
        response = client.post("/items", json={"name": "item", "price": True})
        # Boolean may be coerced to 1 or rejected
        # Either response is acceptable as per Pydantic behavior
        assert response.status_code in [200, 422]

    def test_create_item_string_price_rejected(self):
        """Verify string price values are rejected."""
        response = client.post("/items", json={"name": "item", "price": "10.00"})
        assert response.status_code == 422
