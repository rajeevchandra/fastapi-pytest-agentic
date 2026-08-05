"""Path parameter and integration edge case tests.

Tests for:
- Path parameter boundary values
- Item ID edge cases
- Integration scenarios
- Negative test cases
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test GET /items/{item_id} with various item_id values."""

    @pytest.mark.parametrize("item_id", [
        1,          # Valid ID
        1,          # Valid ID (repeated)
    ])
    def test_get_item_valid_id(self, item_id):
        """Test getting item with valid ID."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @pytest.mark.parametrize("item_id", [
        0,          # Zero
        -1,         # Negative
        -100,       # Negative large
        2,          # Not found
        999,        # Large ID
        1000000,    # Very large ID
    ])
    def test_get_item_invalid_id(self, item_id):
        """Test getting item with non-existent ID."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]


class TestGetItemBoundaryValues:
    """Test boundary value testing for path parameters."""

    @pytest.mark.parametrize("item_id", [
        -2147483648,    # MIN_INT32
        -1,             # Just before valid range
        0,              # Boundary: zero
        1,              # Valid boundary
        2,              # Just after valid ID
        2147483647,     # MAX_INT32
    ])
    def test_get_item_boundary_ids(self, item_id):
        """Test boundary item_id values."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestIntegrationScenarios:
    """Test integration and sequential scenarios."""

    def test_create_then_get_item(self):
        """Test creating item then retrieving it."""
        # Create item
        create_r = client.post("/items", json={"name": "integration_test", "price": 25.0})
        assert create_r.status_code == 200
        created_data = create_r.json()

        # Get item
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()

        # Verify consistent ID
        assert get_data["id"] == created_data["id"]

    def test_multiple_create_requests(self):
        """Test multiple create requests return consistent structure."""
        responses = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
            responses.append(r.json())

        # All should have same ID (backend always returns 1)
        for data in responses:
            assert data["id"] == 1

    def test_create_with_different_prices(self):
        """Test creating items with different prices."""
        prices = [0.01, 1.0, 10.5, 999.99]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_get_then_get_consistency(self):
        """Test multiple GET requests return consistent data."""
        responses = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            responses.append(r.json())

        # All should be identical
        assert responses[0] == responses[1] == responses[2]


class TestErrorHandlingEdgeCases:
    """Test error handling in edge cases."""

    def test_negative_price_provides_clear_error(self):
        """Test negative price error message is clear."""
        r = client.post("/items", json={"name": "test", "price": -50})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"].lower()

    def test_zero_price_provides_clear_error(self):
        """Test zero price error message."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "price must be > 0" in data["detail"]

    def test_invalid_json_payload(self):
        """Test invalid JSON payload handling."""
        r = client.post("/items", content="{invalid json", headers={"content-type": "application/json"})
        assert r.status_code in [400, 422]

    def test_missing_content_type(self):
        """Test request without proper content-type."""
        import json
        r = client.post("/items", data=json.dumps({"name": "test", "price": 10}))
        # May work or return error depending on client
        assert r.status_code in [200, 400, 415, 422]


class TestConcurrentRequests:
    """Test behavior with concurrent-like patterns."""

    def test_rapid_create_requests(self):
        """Test multiple rapid create requests."""
        for i in range(5):
            r = client.post("/items", json={"name": f"rapid_{i}", "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_get_requests(self):
        """Test multiple rapid get requests."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1


class TestInputValidationEdgeCases:
    """Additional edge cases for input validation."""

    def test_very_long_name(self):
        """Test with extremely long name."""
        long_name = "A" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 10000

    def test_price_with_many_decimals(self):
        """Test price with many decimal places."""
        r = client.post("/items", json={"name": "test", "price": 10.123456789})
        assert r.status_code == 200
        # Price should be stored/returned
        assert r.json()["price"] == pytest.approx(10.123456789, rel=1e-6)

    def test_name_with_newlines(self):
        """Test name containing newlines."""
        name_with_newline = "Line1\nLine2\nLine3"
        r = client.post("/items", json={"name": name_with_newline, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_newline

    def test_name_with_tabs(self):
        """Test name with tab characters."""
        name_with_tabs = "Col1\tCol2\tCol3"
        r = client.post("/items", json={"name": name_with_tabs, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_tabs

    def test_extremely_large_price(self):
        """Test with extremely large price."""
        large_price = 1e308  # Near float max
        r = client.post("/items", json={"name": "test", "price": large_price})
        assert r.status_code == 200

    def test_very_small_positive_price(self):
        """Test with very small positive price."""
        small_price = 1e-10
        r = client.post("/items", json={"name": "test", "price": small_price})
        assert r.status_code == 200


class TestResponseConsistency:
    """Test response consistency across different scenarios."""

    def test_response_keys_consistent(self):
        """Test that all success responses have same keys."""
        keys_set = None
        for i in range(3):
            r = client.post("/items", json={"name": f"test_{i}", "price": 10.0 + i})
            keys = set(r.json().keys())
            if keys_set is None:
                keys_set = keys
            else:
                assert keys == keys_set

    def test_get_response_consistency(self):
        """Test GET response consistency."""
        expected_keys = {"id", "name", "price"}
        r = client.get("/items/1")
        assert set(r.json().keys()) == expected_keys

    def test_error_response_always_has_detail(self):
        """Test all error responses have detail field."""
        error_cases = [
            ("/items", "POST", {"name": "test", "price": 0}),
            ("/items/999", "GET", None),
        ]
        for path, method, data in error_cases:
            if method == "POST":
                r = client.post(path, json=data)
            else:
                r = client.get(path)
            if r.status_code >= 400:
                assert "detail" in r.json(), f"Error response missing detail: {r.json()}"
