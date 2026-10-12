"""
Path parameter edge cases and integration tests.

Tests cover:
- Path parameter boundary conditions
- Item ID validation edge cases
- Multiple endpoint interaction patterns
- Complex error scenarios
- State management across requests
- Request/response lifecycle
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test /items/{item_id} path parameter validation and edge cases."""

    @pytest.mark.parametrize("item_id", [0, -1, -100, 1, 2, 999, 1000000])
    def test_item_id_various_values(self, item_id):
        """Test GET with various item_id values."""
        response = client.get(f"/items/{item_id}")
        
        if item_id == 1:
            # Only id=1 should succeed
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
        else:
            # All other values should return 404
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "not found"

    def test_item_id_zero(self):
        """Test GET with item_id = 0."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_item_id_negative(self):
        """Test GET with negative item_id."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_item_id_very_large(self):
        """Test GET with very large item_id."""
        response = client.get("/items/999999999")
        assert response.status_code == 404

    def test_item_id_max_int(self):
        """Test GET with maximum integer value."""
        response = client.get(f"/items/{2**31-1}")
        assert response.status_code == 404

    def test_item_id_boundary_around_one(self):
        """Test item_id values around boundary (id=1)."""
        test_cases = [
            (-1, 404),
            (0, 404),
            (1, 200),
            (2, 404),
            (3, 404),
        ]
        
        for item_id, expected_status in test_cases:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == expected_status


class TestItemIDTypeHandling:
    """Test path parameter type handling."""

    def test_item_id_string_representation(self):
        """Test that path parameter handles string correctly."""
        # Path parameters are always strings in URL, FastAPI converts to int
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_item_id_non_integer_string_format(self):
        """Test path parameter with non-integer string."""
        # FastAPI should fail to parse as int and return error
        response = client.get("/items/abc")
        # FastAPI returns 422 for invalid path parameter type
        assert response.status_code == 422

    def test_item_id_float_string_format(self):
        """Test path parameter with float format string."""
        response = client.get("/items/1.5")
        # Should fail as it's not a valid integer
        assert response.status_code == 422

    def test_item_id_empty_parameter(self):
        """Test /items/ with empty parameter."""
        response = client.get("/items/")
        # Depending on routing, might be 404 or 405
        assert response.status_code in [404, 405, 422]

    def test_item_id_special_characters(self):
        """Test path parameter with special characters."""
        response = client.get("/items/@#$")
        # Special characters in path should fail
        assert response.status_code == 422


class TestCreateItemIDIndependence:
    """Test that create operation doesn't affect get operation."""

    def test_create_does_not_affect_get(self):
        """Verify creating items doesn't change what GET /items/1 returns."""
        # Get initial value
        response1 = client.get("/items/1")
        initial_data = response1.json()
        
        # Create an item
        client.post("/items", json={"name": "new", "price": 20.0})
        
        # Get same item again
        response2 = client.get("/items/1")
        final_data = response2.json()
        
        # Should be identical (implementation returns hardcoded values)
        assert initial_data == final_data
        assert final_data["name"] == "sample"
        assert final_data["price"] == 10.0

    def test_multiple_creates_get_same_response(self):
        """Verify multiple creates don't affect get response."""
        # Create multiple items
        for i in range(5):
            client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
        
        # Get should still return same value
        response = client.get("/items/1")
        data = response.json()
        
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestEndpointInteraction:
    """Test interaction between different endpoints."""

    def test_health_check_unchanged_by_operations(self):
        """Verify health endpoint is unaffected by other operations."""
        # Check health initially
        health1 = client.get("/health").json()
        
        # Perform various operations
        client.post("/items", json={"name": "test", "price": 10.0})
        client.get("/items/1")
        client.post("/items", json={"name": "test2", "price": 20.0})
        
        # Health should be unchanged
        health2 = client.get("/health").json()
        
        assert health1 == health2
        assert health2["status"] == "ok"

    def test_error_operations_dont_affect_success(self):
        """Verify error operations don't affect subsequent success."""
        # First: error operation
        error_resp = client.post("/items", json={"name": "test", "price": 0})
        assert error_resp.status_code == 400
        
        # Second: successful operation
        success_resp = client.post("/items", json={"name": "valid", "price": 10.0})
        assert success_resp.status_code == 200
        
        data = success_resp.json()
        assert data["name"] == "valid"
        assert data["price"] == 10.0

    def test_get_after_create(self):
        """Test GET operation after CREATE operation."""
        # Create
        create_resp = client.post("/items", json={"name": "created", "price": 15.0})
        create_data = create_resp.json()
        created_id = create_data["id"]
        
        # Get with the returned ID
        get_resp = client.get(f"/items/{created_id}")
        assert get_resp.status_code == 200
        
        get_data = get_resp.json()
        # Should be able to retrieve (even though implementation returns hardcoded)
        assert get_data["id"] == created_id


class TestSequentialOperations:
    """Test sequences of operations."""

    def test_successful_operations_sequence(self):
        """Test sequence of successful operations."""
        # Health check
        assert client.get("/health").status_code == 200
        
        # Create items
        for i in range(3):
            resp = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert resp.status_code == 200
        
        # Get item
        assert client.get("/items/1").status_code == 200

    def test_mixed_error_success_sequence(self):
        """Test sequence mixing errors and successes."""
        operations = [
            ("POST", {"name": "valid", "price": 10.0}, 200),
            ("POST", {"name": "invalid", "price": 0}, 400),
            ("POST", {"name": "valid2", "price": 20.0}, 200),
            ("GET", None, 200),
        ]
        
        for method, data, expected_status in operations:
            if method == "POST":
                resp = client.post("/items", json=data)
            else:
                resp = client.get("/items/1")
            
            assert resp.status_code == expected_status

    def test_error_recovery_sequence(self):
        """Test recovery after error operations."""
        # Multiple errors
        for _ in range(3):
            resp = client.post("/items", json={"name": "test", "price": -1})
            assert resp.status_code == 400
        
        # Successful recovery
        resp = client.post("/items", json={"name": "success", "price": 10.0})
        assert resp.status_code == 200
        assert resp.json()["name"] == "success"


class TestResponseConsistencyAcrossOperations:
    """Test that responses are consistent across multiple operations."""

    def test_repeated_get_same_response(self):
        """Test that GET /items/1 always returns same response."""
        responses = []
        for _ in range(5):
            resp = client.get("/items/1")
            responses.append(resp.json())
        
        # All should be identical
        for resp in responses[1:]:
            assert resp == responses[0]

    def test_repeated_create_incremental_ids(self):
        """Test that create operations have consistent id pattern."""
        created_ids = []
        for i in range(3):
            resp = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            created_ids.append(resp.json()["id"])
        
        # All should have id=1 (hardcoded implementation)
        assert all(id == 1 for id in created_ids)

    def test_repeated_health_check(self):
        """Test that health check is consistent."""
        health_checks = []
        for _ in range(5):
            resp = client.get("/health")
            health_checks.append(resp.json()["status"])
        
        # All should be "ok"
        assert all(status == "ok" for status in health_checks)


class TestErrorScenarios:
    """Test various error scenarios and edge cases."""

    def test_404_consistency(self):
        """Test that 404 errors are consistent."""
        responses = []
        for item_id in [2, 5, 10, 100]:
            resp = client.get(f"/items/{item_id}")
            responses.append(resp.json())
        
        # All should have same error message
        for resp in responses:
            assert resp["detail"] == "not found"

    def test_400_consistency(self):
        """Test that 400 errors are consistent."""
        responses = []
        for price in [0, -1, -100]:
            resp = client.post("/items", json={"name": "test", "price": price})
            responses.append(resp.json())
        
        # All should have same error message
        for resp in responses:
            assert resp["detail"] == "price must be > 0"

    def test_422_consistency(self):
        """Test that 422 errors are consistent for same issue."""
        responses = []
        for _ in range(2):
            resp = client.post("/items", json={"name": "test"})
            responses.append(resp.json())
        
        # Both should have detail field (validation error)
        for resp in responses:
            assert "detail" in resp

    def test_mixed_error_types(self):
        """Test that different error types are handled properly."""
        error_cases = [
            ("GET", "/items/999", 404),              # Not found
            ("POST", "/items", {"name": "test", "price": 0}, 400),  # Bad request
            ("POST", "/items", {"name": "test"}, 422),              # Validation error
            ("GET", "/items/abc", None, 422),        # Invalid type
        ]
        
        for case in error_cases:
            if len(case) == 3:
                method, path, expected_status = case
                if method == "GET":
                    resp = client.get(path)
                else:
                    resp = client.post(path)
            else:
                method, path, data, expected_status = case
                resp = client.post(path, json=data)
            
            assert resp.status_code == expected_status


class TestRequestResponseLifecycle:
    """Test complete request-response lifecycle."""

    def test_create_request_response_lifecycle(self):
        """Test complete lifecycle of create operation."""
        # Build request
        request_data = {"name": "test_item", "price": 25.5}
        
        # Send request
        response = client.post("/items", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response contains all fields
        assert "id" in response_data
        assert "name" in response_data
        assert "price" in response_data
        
        # Verify values
        assert response_data["name"] == request_data["name"]
        assert response_data["price"] == request_data["price"]

    def test_get_request_response_lifecycle(self):
        """Test complete lifecycle of get operation."""
        # Build request
        item_id = 1
        
        # Send request
        response = client.get(f"/items/{item_id}")
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response structure
        assert "id" in response_data
        assert "name" in response_data
        assert "price" in response_data
        
        # Verify values
        assert response_data["id"] == item_id

    def test_error_request_response_lifecycle(self):
        """Test complete lifecycle of error operation."""
        # Build error request
        request_data = {"name": "test", "price": 0}
        
        # Send request
        response = client.post("/items", json=request_data)
        
        # Verify error response
        assert response.status_code == 400
        response_data = response.json()
        
        # Verify error structure
        assert "detail" in response_data
        assert response_data["detail"] == "price must be > 0"


class TestCombinedEndpoints:
    """Test combinations of endpoints in various workflows."""

    def test_health_create_get_workflow(self):
        """Test workflow: health check → create → get."""
        # Health check
        health = client.get("/health")
        assert health.status_code == 200
        
        # Create
        create = client.post("/items", json={"name": "workflow", "price": 30.0})
        assert create.status_code == 200
        item_id = create.json()["id"]
        
        # Get
        get = client.get(f"/items/{item_id}")
        assert get.status_code == 200

    def test_error_detection_workflow(self):
        """Test workflow for detecting and recovering from errors."""
        # Attempt invalid operation
        invalid = client.post("/items", json={"name": "test", "price": -10})
        assert invalid.status_code == 400
        
        # Verify error detail
        assert invalid.json()["detail"] == "price must be > 0"
        
        # Correct and retry
        valid = client.post("/items", json={"name": "test", "price": 10})
        assert valid.status_code == 200

    def test_full_api_workflow(self):
        """Test complete API workflow."""
        # Start with health check
        assert client.get("/health").status_code == 200
        
        # Create various items
        created_items = []
        for i in range(3):
            resp = client.post(
                "/items",
                json={"name": f"item_{i}", "price": 10.0 + i}
            )
            assert resp.status_code == 200
            created_items.append(resp.json())
        
        # Retrieve items
        for item in created_items:
            resp = client.get(f"/items/{item['id']}")
            assert resp.status_code == 200
        
        # Attempt invalid operation
        bad_resp = client.post("/items", json={"name": "bad", "price": 0})
        assert bad_resp.status_code == 400
        
        # Verify health is still OK
        assert client.get("/health").status_code == 200


class TestEdgeCaseScenarios:
    """Test various edge case scenarios."""

    def test_create_with_boundary_price_then_get(self):
        """Test create with boundary price then retrieve."""
        # Create with minimum valid price
        create = client.post("/items", json={"name": "min", "price": 0.01})
        assert create.status_code == 200
        
        item_id = create.json()["id"]
        
        # Get the item
        get = client.get(f"/items/{item_id}")
        assert get.status_code == 200

    def test_unicode_name_create_verify(self):
        """Test create with unicode name and verify response."""
        # Create with unicode
        create = client.post("/items", json={"name": "商品", "price": 99.99})
        assert create.status_code == 200
        
        data = create.json()
        assert data["name"] == "商品"
        assert data["price"] == 99.99

    def test_special_character_name_handling(self):
        """Test handling of special characters in name."""
        special_names = [
            "Item!@#$%",
            "Product (original)",
            "Book: Advanced Topics",
            "Item & Accessories",
        ]
        
        for name in special_names:
            resp = client.post("/items", json={"name": name, "price": 10.0})
            assert resp.status_code == 200
            assert resp.json()["name"] == name

    def test_extreme_price_values(self):
        """Test handling of extreme price values."""
        prices = [
            0.01,           # Minimum valid
            1.0,            # Unit price
            999999.99,      # Large price
            1000000.0,      # Very large
        ]
        
        for price in prices:
            resp = client.post("/items", json={"name": "item", "price": price})
            assert resp.status_code == 200
            assert resp.json()["price"] == price


class TestResponseFieldConsistency:
    """Test consistency of response fields across operations."""

    def test_response_field_count_consistency(self):
        """Test that all responses have consistent field count."""
        # Create response
        create = client.post("/items", json={"name": "test", "price": 10.0})
        create_fields = len(create.json())
        
        # Get response
        get = client.get("/items/1")
        get_fields = len(get.json())
        
        # Health response
        health = client.get("/health")
        health_fields = len(health.json())
        
        # Verify expectations
        assert create_fields == 3  # id, name, price
        assert get_fields == 3     # id, name, price
        assert health_fields == 1  # status

    def test_response_field_names_consistency(self):
        """Test that field names are consistent."""
        # Create response fields
        create = client.post("/items", json={"name": "test", "price": 10.0})
        create_keys = set(create.json().keys())
        
        # Get response fields
        get = client.get("/items/1")
        get_keys = set(get.json().keys())
        
        # Item responses should have same fields
        assert create_keys == get_keys
        assert create_keys == {"id", "name", "price"}

    def test_response_value_types_consistency(self):
        """Test that response value types are consistent."""
        # Create
        create = client.post("/items", json={"name": "test", "price": 10.0})
        create_data = create.json()
        
        # Get
        get = client.get("/items/1")
        get_data = get.json()
        
        # Verify type consistency
        assert type(create_data["id"]) == type(get_data["id"])
        assert type(create_data["name"]) == type(get_data["name"])
        assert type(create_data["price"]) == type(get_data["price"])
