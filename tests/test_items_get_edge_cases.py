"""
Edge case and integration tests for the items API.

Tests cover:
- Item ID boundary values (negative, zero, large)
- Multiple item operations and sequencing
- Error recovery scenarios
- Integration patterns between endpoints
- HTTP method validation
- API consistency under edge conditions
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryIDs:
    """Tests for get_item with boundary value item IDs."""

    def test_get_item_with_id_one_succeeds(self):
        """Test that item_id=1 returns success."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_with_id_zero_returns_404(self):
        """Test that item_id=0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_with_negative_id_returns_404(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_with_large_negative_id_returns_404(self):
        """Test that large negative item_id returns 404."""
        r = client.get("/items/-9999")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 999999])
    def test_get_item_with_various_non_one_ids_returns_404(self, item_id):
        """Test that item IDs other than 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_with_max_int_returns_404(self):
        """Test that maximum int returns 404."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404


class TestGetItemIDTypeValidation:
    """Tests for path parameter type validation."""

    def test_get_item_with_float_id_path(self):
        """Test GET with float-like path parameter."""
        # FastAPI might accept or reject depending on conversion
        r = client.get("/items/1.0")
        # Could be 200, 404, or 422 depending on implementation
        assert r.status_code in [200, 404, 422]

    def test_get_item_with_non_numeric_id(self):
        """Test GET with non-numeric path parameter."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_with_string_id(self):
        """Test GET with string-like parameter."""
        r = client.get("/items/string123")
        assert r.status_code == 422

    def test_get_item_with_empty_id(self):
        """Test GET without ID parameter."""
        r = client.get("/items/")
        assert r.status_code == 404


class TestMultipleItemOperations:
    """Tests for sequences of operations."""

    def test_create_then_get_sequence(self):
        """Test creating an item and then retrieving it."""
        create_r = client.post("/items", json={"name": "book", "price": 15.0})
        assert create_r.status_code == 200
        
        item_id = create_r.json()["id"]
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == item_id

    def test_create_two_items_both_have_id(self):
        """Test that creating multiple items returns ids."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert "id" in r1.json()
        assert "id" in r2.json()

    def test_multiple_failed_creates_then_success(self):
        """Test recovery from multiple failed creates."""
        # Multiple invalid attempts
        r1 = client.post("/items", json={"name": "item", "price": -5})
        r2 = client.post("/items", json={"name": "item", "price": 0})
        
        assert r1.status_code == 400
        assert r2.status_code == 400
        
        # Successful create after failures
        r3 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r3.status_code == 200

    def test_failed_get_then_successful_get(self):
        """Test recovery from failed get."""
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_multiple_operations_maintain_data_integrity(self):
        """Test that data is maintained across multiple operations."""
        name = "integrity_test_item"
        price = 42.99
        
        create_r = client.post("/items", json={"name": name, "price": price})
        item_id = create_r.json()["id"]
        
        get_r = client.get(f"/items/{item_id}")
        data = get_r.json()
        
        assert data["name"] == name
        assert data["price"] == price


class TestPriceValidationEdgeCases:
    """Tests for price validation edge cases."""

    def test_price_exactly_at_zero_boundary(self):
        """Test price exactly at zero (boundary)."""
        r = client.post("/items", json={"name": "item", "price": 0.0})
        assert r.status_code == 400

    def test_price_just_above_zero(self):
        """Test price just above zero boundary."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_price_just_below_zero(self):
        """Test price just below zero boundary."""
        r = client.post("/items", json={"name": "item", "price": -0.0001})
        assert r.status_code == 400

    @pytest.mark.parametrize("price", [1e-10, 1e-6, 1e-3, 1e-1, 1e0, 1e3, 1e6])
    def test_price_various_magnitude_orders(self, price):
        """Test prices at different magnitude orders."""
        r = client.post("/items", json={"name": "item", "price": price})
        if price > 0:
            assert r.status_code == 200
        else:
            assert r.status_code == 400

    def test_price_with_trailing_zeros(self):
        """Test price with trailing zeros."""
        r = client.post("/items", json={"name": "item", "price": 10.00})
        assert r.status_code == 200

    def test_price_with_many_decimal_places(self):
        """Test price with many decimal places."""
        r = client.post("/items", json={"name": "item", "price": 10.123456789})
        assert r.status_code == 200
        assert r.json()["price"] == 10.123456789


class TestNameFieldEdgeCases:
    """Tests for name field edge cases."""

    def test_name_single_character(self):
        """Test single character name."""
        r = client.post("/items", json={"name": "x", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "x"

    def test_name_very_long(self):
        """Test very long name."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_name_with_newlines(self):
        """Test name with newline characters."""
        r = client.post("/items", json={"name": "item\nname", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item\nname"

    def test_name_with_tabs(self):
        """Test name with tab characters."""
        r = client.post("/items", json={"name": "item\tname", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item\tname"

    def test_name_with_quotes(self):
        """Test name with quote characters."""
        r = client.post("/items", json={"name": 'item"name\'s', "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == 'item"name\'s'

    def test_name_with_backslash(self):
        """Test name with backslash."""
        r = client.post("/items", json={"name": "item\\name", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item\\name"

    def test_name_only_whitespace(self):
        """Test name with only whitespace."""
        r = client.post("/items", json={"name": "   \t\n  ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   \t\n  "

    def test_name_with_null_bytes(self):
        """Test name with null bytes."""
        r = client.post("/items", json={"name": "item\x00name", "price": 10.0})
        assert r.status_code == 200


class TestHTTPMethodValidation:
    """Tests for incorrect HTTP methods."""

    def test_get_on_create_endpoint_fails(self):
        """Test GET request to POST-only endpoint."""
        r = client.get("/items")
        # GET not allowed on /items (POST only)
        assert r.status_code == 405

    def test_post_on_get_endpoint_fails(self):
        """Test POST request to GET-only endpoint."""
        r = client.post("/items/1")
        # POST not allowed on /items/{id} (GET only)
        assert r.status_code == 405

    def test_put_on_create_endpoint_fails(self):
        """Test PUT request to POST-only endpoint."""
        r = client.put("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 405

    def test_delete_on_get_endpoint_fails(self):
        """Test DELETE request to GET-only endpoint."""
        r = client.delete("/items/1")
        assert r.status_code == 405

    def test_patch_on_create_endpoint_fails(self):
        """Test PATCH request to POST-only endpoint."""
        r = client.patch("/items", json={"name": "item"})
        assert r.status_code == 405


class TestAPIConsistency:
    """Tests for API consistency under edge conditions."""

    def test_repeated_operations_produce_consistent_results(self):
        """Test that repeated same operations give consistent results."""
        name = "consistency_test"
        price = 33.33
        
        # Create twice with same data
        r1 = client.post("/items", json={"name": name, "price": price})
        r2 = client.post("/items", json={"name": name, "price": price})
        
        assert r1.status_code == r2.status_code
        assert r1.json()["name"] == r2.json()["name"]
        assert r1.json()["price"] == r2.json()["price"]

    def test_get_same_id_produces_consistent_results(self):
        """Test that getting same ID multiple times gives consistent results."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        
        data1 = r1.json()
        data2 = r2.json()
        data3 = r3.json()
        
        assert data1 == data2 == data3

    def test_error_state_does_not_affect_subsequent_success(self):
        """Test that error doesn't corrupt state for next success."""
        # Cause error
        error_r = client.post("/items", json={"name": "item", "price": -1})
        assert error_r.status_code == 400
        
        # Try success
        success_r = client.post("/items", json={"name": "good", "price": 10.0})
        assert success_r.status_code == 200
        assert success_r.json()["name"] == "good"

    def test_not_found_does_not_affect_valid_get(self):
        """Test that 404 doesn't affect valid retrieval."""
        not_found_r = client.get("/items/9999")
        assert not_found_r.status_code == 404
        
        found_r = client.get("/items/1")
        assert found_r.status_code == 200
        assert found_r.json()["id"] == 1


class TestEndpointIntegration:
    """Tests for integration patterns between endpoints."""

    def test_create_and_list_pattern(self):
        """Test creating item and attempting to access it."""
        create_r = client.post("/items", json={"name": "testitem", "price": 25.50})
        assert create_r.status_code == 200
        
        created_item = create_r.json()
        assert created_item["name"] == "testitem"
        assert created_item["price"] == 25.50

    def test_implicit_create_creates_id_one(self):
        """Test that item creation always seems to create id 1."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_health_endpoint_independent_of_items(self):
        """Test that health check is independent of items operations."""
        # Health should work regardless
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_before_and_after_item_operations(self):
        """Test health endpoint before and after item operations."""
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        client.post("/items", json={"name": "test", "price": 10.0})
        
        r2 = client.get("/health")
        assert r2.status_code == 200
        assert r1.json() == r2.json()


class TestSequentialErrorHandling:
    """Tests for handling error sequences."""

    def test_multiple_validation_errors_then_success(self):
        """Test recovery after multiple validation errors."""
        # Invalid: missing price
        r1 = client.post("/items", json={"name": "item"})
        assert r1.status_code == 422
        
        # Invalid: invalid type
        r2 = client.post("/items", json={"name": 123, "price": "10"})
        assert r2.status_code in [422, 200]  # Pydantic might coerce
        
        # Invalid: negative price
        r3 = client.post("/items", json={"name": "item", "price": -5})
        assert r3.status_code == 400
        
        # Valid: should succeed
        r4 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r4.status_code == 200

    def test_multiple_not_found_then_found(self):
        """Test recovery after multiple 404s."""
        r1 = client.get("/items/100")
        r2 = client.get("/items/200")
        r3 = client.get("/items/300")
        
        assert r1.status_code == 404
        assert r2.status_code == 404
        assert r3.status_code == 404
        
        r4 = client.get("/items/1")
        assert r4.status_code == 200


class TestConcurrentLikeOperations:
    """Tests simulating concurrent-like patterns."""

    def test_interleaved_create_and_get_operations(self):
        """Test interleaving create and get operations."""
        c1 = client.post("/items", json={"name": "item1", "price": 10.0})
        g1 = client.get("/items/1")
        c2 = client.post("/items", json={"name": "item2", "price": 20.0})
        g2 = client.get("/items/1")
        
        assert c1.status_code == 200
        assert g1.status_code == 200
        assert c2.status_code == 200
        assert g2.status_code == 200

    def test_mixed_success_and_error_operations(self):
        """Test mixing successful and error operations."""
        operations = [
            client.post("/items", json={"name": "good", "price": 10.0}),  # success
            client.get("/items/999"),  # error
            client.post("/items", json={"name": "item", "price": 0}),  # error
            client.get("/items/1"),  # success
            client.post("/items", json={"name": "good2", "price": 20.0}),  # success
        ]
        
        assert operations[0].status_code == 200
        assert operations[1].status_code == 404
        assert operations[2].status_code == 400
        assert operations[3].status_code == 200
        assert operations[4].status_code == 200
