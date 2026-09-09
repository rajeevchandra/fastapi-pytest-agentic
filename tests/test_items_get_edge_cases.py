"""
Path parameter edge cases and integration scenario tests.
Tests GET /items/{item_id} with boundary values and integration patterns.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    def test_get_item_with_valid_id(self):
        """Valid ID returns 200 or 404."""
        r = client.get("/items/1")
        assert r.status_code in [200, 404]

    def test_get_item_with_zero_id(self):
        """ID=0 should return 404 (not found)."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_with_negative_id(self):
        """Negative IDs should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-10, -1, 0])
    def test_get_item_non_positive_ids(self, item_id):
        """Non-positive IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1000, 999999, 2147483647])
    def test_get_item_large_ids(self, item_id):
        """Large IDs return 404 (not in database)."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestGetItemIDEdgeCases:
    """Test edge cases for item ID parameter."""

    def test_get_item_only_id_1_exists(self):
        """Only item ID 1 returns 200, others return 404."""
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        r2 = client.get("/items/2")
        assert r2.status_code == 404

    def test_get_item_boundary_values(self):
        """Test various boundary ID values."""
        # Min boundary
        r_zero = client.get("/items/0")
        assert r_zero.status_code == 404
        
        # Valid boundary
        r_one = client.get("/items/1")
        assert r_one.status_code == 200
        
        # Just above
        r_two = client.get("/items/2")
        assert r_two.status_code == 404

    def test_get_item_repeated_requests_same_result(self):
        """Multiple requests to same ID return same result."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.status_code == r2.status_code
        assert r1.json() == r2.json()

    def test_get_item_not_found_consistency(self):
        """Multiple 404s return consistent error."""
        for item_id in [2, 3, 5]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"


class TestGetItemResponseConsistency:
    """Test response consistency for GET /items/{item_id}."""

    def test_get_item_1_returns_sample_data(self):
        """Item 1 has consistent data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_1_always_same(self):
        """Multiple GETs of item 1 return same data."""
        responses = [client.get("/items/1").json() for _ in range(3)]
        assert all(r == responses[0] for r in responses)

    def test_get_item_response_format(self):
        """Response has correct structure."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data, dict)
        assert all(k in data for k in ["id", "name", "price"])

    def test_get_item_data_types(self):
        """Response data types are correct."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestCreateItemThenGet:
    """Integration tests: create item then get it."""

    def test_create_item_is_idempotent(self):
        """Creating multiple items uses same ID."""
        r1 = client.post("/items", json={"name": "book1", "price": 10.0})
        r2 = client.post("/items", json={"name": "book2", "price": 20.0})
        
        # Both return id=1 (simple mock API)
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1

    def test_get_item_after_create(self):
        """Can get item 1 after creating."""
        client.post("/items", json={"name": "test", "price": 10.0})
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_item_1_always_retrievable(self):
        """Item 1 is always available for GET."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestMultipleRequests:
    """Test patterns with multiple sequential requests."""

    def test_create_then_get_same_endpoint(self):
        """POST then GET works correctly."""
        post_r = client.post("/items", json={"name": "item", "price": 5.0})
        get_r = client.get("/items/1")
        
        assert post_r.status_code == 200
        assert get_r.status_code == 200

    def test_multiple_gets_different_ids(self):
        """Multiple GETs with different IDs."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/2")
        r3 = client.get("/items/1")
        
        assert r1.status_code == 200
        assert r2.status_code == 404
        assert r3.status_code == 200
        assert r1.json() == r3.json()

    def test_alternating_requests(self):
        """Alternating POST and GET requests."""
        p1 = client.post("/items", json={"name": "a", "price": 1.0})
        g1 = client.get("/items/1")
        p2 = client.post("/items", json={"name": "b", "price": 2.0})
        g2 = client.get("/items/2")
        
        assert p1.status_code == 200
        assert g1.status_code == 200
        assert p2.status_code == 200
        assert g2.status_code == 404


class TestErrorRecovery:
    """Test behavior after errors."""

    def test_invalid_request_then_valid(self):
        """Valid request works after invalid one."""
        # Invalid request
        r_invalid = client.post("/items", json={"name": "test", "price": 0})
        assert r_invalid.status_code == 400
        
        # Valid request should still work
        r_valid = client.post("/items", json={"name": "test", "price": 10.0})
        assert r_valid.status_code == 200

    def test_get_404_then_200(self):
        """Valid GET works after 404."""
        r_404 = client.get("/items/999")
        assert r_404.status_code == 404
        
        r_200 = client.get("/items/1")
        assert r_200.status_code == 200

    def test_error_doesnt_affect_item_1(self):
        """Errors don't affect retrieving item 1."""
        client.get("/items/5")  # 404
        client.get("/items/999")  # 404
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestBoundaryIntegration:
    """Test integration patterns with boundary values."""

    def test_extreme_price_then_get(self):
        """Creating with extreme price then get item 1."""
        client.post("/items", json={"name": "expensive", "price": 1e10})
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_invalid_price_then_get(self):
        """Invalid creation doesn't affect item 1 retrieval."""
        client.post("/items", json={"name": "cheap", "price": -5})
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_missing_field_then_get(self):
        """Validation error doesn't affect item 1."""
        client.post("/items", json={"price": 10.0})  # Missing name
        r = client.get("/items/1")
        assert r.status_code == 200


class TestIDParameterFormat:
    """Test various formats for ID parameter."""

    def test_get_item_string_id_converted_to_int(self):
        """Path parameter is converted to int."""
        r = client.get("/items/1")
        assert r.status_code in [200, 404]

    def test_get_item_invalid_id_type(self):
        """Non-numeric ID in path returns 422 or 404."""
        r = client.get("/items/abc")
        assert r.status_code in [422, 404]

    def test_get_item_float_id_in_path(self):
        """Float in path parameter."""
        r = client.get("/items/1.5")
        assert r.status_code in [422, 404]


class TestConcurrentBehavior:
    """Test behavior under repeated/rapid requests."""

    def test_rapid_get_requests(self):
        """Multiple rapid GETs return consistent results."""
        results = [client.get("/items/1").status_code for _ in range(5)]
        assert all(r == 200 for r in results)

    def test_rapid_invalid_ids(self):
        """Multiple rapid 404 requests."""
        results = [client.get(f"/items/{i}").status_code for i in range(2, 7)]
        assert all(r == 404 for r in results)

    def test_rapid_mixed_requests(self):
        """Mixed valid/invalid IDs in rapid succession."""
        requests = [1, 2, 1, 3, 1, 4]
        results = [client.get(f"/items/{i}").status_code for i in requests]
        expected = [200, 404, 200, 404, 200, 404]
        assert results == expected


class TestEndpointAvailability:
    """Test that endpoints are available and respond."""

    def test_health_always_available(self):
        """Health endpoint is always available."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_create_always_available(self):
        """POST /items is always available."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code in [200, 400, 422]

    def test_get_always_available(self):
        """GET /items/{id} is always available."""
        r = client.get("/items/1")
        assert r.status_code in [200, 404]

    def test_all_endpoints_working(self):
        """All endpoints respond without server errors."""
        r1 = client.get("/health")
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        r3 = client.get("/items/1")
        
        assert all(r.status_code < 500 for r in [r1, r2, r3])
