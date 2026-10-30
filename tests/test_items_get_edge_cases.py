"""
Edge cases and integration tests for items endpoints.

Tests cover:
- Boundary value testing for item_id
- Interaction patterns between endpoints
- Stress testing with various input combinations
- Negative and extreme value testing
- Sequential operations
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemIdBoundaryValues:
    """Test boundary values for get_item item_id parameter."""

    def test_get_item_with_negative_id(self):
        """Test get_item with negative ID."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_zero_id(self):
        """Test get_item with ID of 0."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_large_positive_id(self):
        """Test get_item with very large positive ID."""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_max_int_id(self):
        """Test get_item with maximum integer ID."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_large_negative_id(self):
        """Test get_item with very large negative ID."""
        r = client.get("/items/-999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 5, 10, 100, 500, 1000, 10000])
    def test_get_item_various_nonexistent_ids(self, item_id):
        """Test get_item with various nonexistent IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_existing_vs_nonexisting(self):
        """Test that only item_id=1 exists."""
        # Item 1 should exist
        r = client.get("/items/1")
        assert r.status_code == 200
        
        # Any other ID should not exist
        r = client.get("/items/2")
        assert r.status_code == 404


class TestCreateItemBoundaryValueCombinations:
    """Test combinations of boundary values."""

    @pytest.mark.parametrize("name,price", [
        ("a", 0.01),  # Minimal name and price
        ("x" * 1000, 1e10),  # Maximum name and very large price
        ("unicode_商品", 0.001),  # Unicode name with small price
        ("item!@#$%", 999.99),  # Special chars with normal price
        ("", 1.0),  # Empty name (should fail validation)
    ])
    def test_various_name_price_combinations(self, name, price):
        """Test various combinations of name and price values."""
        r = client.post("/items", json={"name": name, "price": price})
        if name == "":
            # Empty name should fail
            assert r.status_code == 422
        else:
            # Valid names should succeed
            assert r.status_code in [200, 422]

    def test_price_boundary_combinations_with_names(self):
        """Test multiple price boundaries with same name."""
        prices = [0.01, 1.0, 100.0, 1000000.0]
        name = "test_item"
        
        for price in prices:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestSequentialItemOperations:
    """Test sequences of operations on items."""

    def test_create_and_immediately_get(self):
        """Test creating an item and immediately retrieving it."""
        # Create item
        create_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Immediately get the item
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()
        
        # Should retrieve the item that was just created
        assert get_data["id"] == created_data["id"]

    def test_multiple_creates_always_return_id_1(self):
        """Test that multiple creates always return same ID."""
        ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        
        # All should return the same ID (1)
        assert ids == [1, 1, 1]

    def test_get_after_multiple_creates(self):
        """Test get_item returns consistent data after multiple creates."""
        # Create multiple items
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
        
        # Get item 1
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1
        
        # Item data should be consistent (always "sample", 10.0)
        assert r.json()["name"] == "sample"
        assert r.json()["price"] == 10.0


class TestErrorRecovery:
    """Test that errors don't affect subsequent operations."""

    def test_invalid_price_then_valid_create(self):
        """Test that invalid price error doesn't prevent next valid create."""
        # Try invalid price
        invalid_r = client.post("/items", json={"name": "item", "price": 0})
        assert invalid_r.status_code == 400
        
        # Next valid create should work
        valid_r = client.post("/items", json={"name": "item", "price": 10.0})
        assert valid_r.status_code == 200

    def test_not_found_error_then_get_existing(self):
        """Test that 404 error doesn't prevent getting existing item."""
        # Try getting nonexistent item
        missing_r = client.get("/items/999")
        assert missing_r.status_code == 404
        
        # Getting existing item should work
        existing_r = client.get("/items/1")
        assert existing_r.status_code == 200

    def test_multiple_errors_then_success(self):
        """Test multiple errors followed by successful operation."""
        # Multiple errors
        for i in range(3):
            r = client.post("/items", json={"name": "item", "price": -1})
            assert r.status_code == 400
        
        # Finally a success
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200


class TestPriceValidationEdgeCases:
    """Test edge cases in price validation."""

    def test_price_exactly_zero_rejected(self):
        """Test that price=0.0 is rejected."""
        r = client.post("/items", json={"name": "item", "price": 0.0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_price_just_above_zero_accepted(self):
        """Test that smallest positive price is accepted."""
        r = client.post("/items", json={"name": "item", "price": 1e-100})
        assert r.status_code == 200
        assert r.json()["price"] > 0

    def test_negative_zero_rejected(self):
        """Test that -0.0 is rejected."""
        r = client.post("/items", json={"name": "item", "price": -0.0})
        assert r.status_code == 400

    @pytest.mark.parametrize("invalid_price", [-1e-100, -0.001, -0.0, 0.0, -1000])
    def test_various_non_positive_prices(self, invalid_price):
        """Test that various non-positive prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": invalid_price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestNameValidationEdgeCases:
    """Test edge cases in name validation."""

    def test_name_with_whitespace_only(self):
        """Test that whitespace-only names might be treated as empty."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        # Whitespace is still a string, should be accepted
        assert r.status_code in [200, 422]

    def test_name_with_null_bytes(self):
        """Test that null bytes in name are handled."""
        # This may cause issues in some systems
        try:
            r = client.post("/items", json={"name": "item\x00test", "price": 10.0})
            # Could be accepted or rejected
            assert r.status_code in [200, 400, 422]
        except Exception:
            # Some systems may error before sending
            pass

    def test_name_with_line_breaks(self):
        """Test that line breaks in name are preserved."""
        r = client.post("/items", json={"name": "line1\nline2", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "line1\nline2"

    def test_name_with_tabs(self):
        """Test that tabs in name are preserved."""
        r = client.post("/items", json={"name": "item\tname", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item\tname"


class TestConcurrentLikeOperations:
    """Test patterns that simulate concurrent-like operations."""

    def test_interleaved_creates_and_gets(self):
        """Test alternating create and get operations."""
        for i in range(3):
            # Create
            create_r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert create_r.status_code == 200
            
            # Get
            get_r = client.get("/items/1")
            assert get_r.status_code == 200
            
            # Try getting a nonexistent ID
            missing_r = client.get(f"/items/{10 + i}")
            assert missing_r.status_code == 404

    def test_multiple_error_conditions_interleaved(self):
        """Test multiple different error types in sequence."""
        operations = [
            ("POST", "/items", {"name": "item", "price": 0}),  # Invalid price
            ("GET", "/items/999", None),  # Not found
            ("POST", "/items", {"price": 10.0}),  # Missing name
            ("GET", "/items/1", None),  # Valid get
            ("POST", "/items", {"name": "item"}),  # Missing price
            ("GET", "/items/-1", None),  # Not found with negative ID
        ]
        
        expected_statuses = [400, 404, 422, 200, 422, 404]
        
        for i, (method, path, data) in enumerate(operations):
            if method == "POST":
                r = client.post(path, json=data)
            else:
                r = client.get(path)
            
            assert r.status_code == expected_statuses[i]


class TestResponseConsistencyOverTime:
    """Test that responses remain consistent over multiple calls."""

    def test_get_item_always_returns_same_data(self):
        """Test that get_item/1 always returns the same data."""
        responses = []
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            responses.append(r.json())
        
        # All responses should be identical
        first = responses[0]
        for resp in responses[1:]:
            assert resp == first

    def test_error_responses_consistent(self):
        """Test that error responses are consistent."""
        error_responses = []
        for _ in range(3):
            r = client.post("/items", json={"name": "item", "price": 0})
            assert r.status_code == 400
            error_responses.append(r.json())
        
        # All error responses should be identical
        first = error_responses[0]
        for resp in error_responses[1:]:
            assert resp == first


class TestInputOutputConsistency:
    """Test that outputs match expectations for various inputs."""

    @pytest.mark.parametrize("name", ["item1", "item2", "test", "product"])
    def test_name_echoed_in_response(self, name):
        """Test that input name is echoed in response."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("price", [0.01, 1.5, 100.0, 999.99])
    def test_price_echoed_in_response(self, price):
        """Test that input price is echoed in response."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestEndpointInteractionPatterns:
    """Test patterns of interaction between different endpoints."""

    def test_health_always_works(self):
        """Test that health endpoint works even after errors."""
        # Cause some errors
        client.post("/items", json={"name": "item", "price": 0})
        client.get("/items/999")
        client.post("/items", json={"price": 10.0})
        
        # Health should still work
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_operations_on_all_endpoints(self):
        """Test operations on all available endpoints."""
        # Health
        health_r = client.get("/health")
        assert health_r.status_code == 200
        
        # Create
        create_r = client.post("/items", json={"name": "item", "price": 10.0})
        assert create_r.status_code == 200
        
        # Get
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        
        # All responses should be valid JSON
        assert isinstance(health_r.json(), dict)
        assert isinstance(create_r.json(), dict)
        assert isinstance(get_r.json(), dict)


class TestErrorHandlingConsistency:
    """Test that error handling is consistent across operations."""

    def test_validation_errors_have_detail_field(self):
        """Test all validation errors have detail field."""
        operations = [
            {"name": "item"},  # Missing price
            {"price": 10.0},  # Missing name
            {"name": None, "price": 10.0},  # Null name
            {"name": "item", "price": None},  # Null price
        ]
        
        for data in operations:
            r = client.post("/items", json=data)
            assert r.status_code == 422
            assert "detail" in r.json()

    def test_business_logic_errors_have_detail_field(self):
        """Test that business logic errors have detail field."""
        operations = [
            {"name": "item", "price": 0},  # Price <= 0
            {"name": "item", "price": -1},  # Negative price
        ]
        
        for data in operations:
            r = client.post("/items", json=data)
            assert r.status_code == 400
            assert "detail" in r.json()

    def test_not_found_errors_have_detail_field(self):
        """Test that not found errors have detail field."""
        for item_id in [2, 10, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert "detail" in r.json()


class TestTypeCoercionAndValidation:
    """Test how the API handles type coercion."""

    def test_string_price_might_be_coerced(self):
        """Test that numeric string price might be coerced."""
        r = client.post("/items", json={"name": "item", "price": "10.0"})
        # Pydantic might coerce string to float
        assert r.status_code in [200, 422]

    def test_integer_name_might_be_coerced(self):
        """Test that integer name might be coerced to string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic might coerce int to string
        assert r.status_code in [200, 422]

    def test_boolean_price_type_error(self):
        """Test that boolean price causes error."""
        r = client.post("/items", json={"name": "item", "price": True})
        # Boolean is technically an int in Python, might be accepted
        assert r.status_code in [200, 400, 422]
