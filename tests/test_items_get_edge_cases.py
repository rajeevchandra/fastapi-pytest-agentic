"""Edge case and integration tests for comprehensive coverage."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================================
# Test Class 1: Item ID Boundary Value Testing
# ============================================================================
class TestGetItemIdBoundaries:
    """Test GET /items/{id} with boundary value IDs."""

    def test_get_item_with_id_one(self):
        """Test GET /items/1 returns found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @pytest.mark.parametrize("item_id", [0, -1, -100, -999])
    def test_get_item_with_non_positive_ids(self, item_id):
        """Test GET /items/{id} with non-positive IDs returns 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 999999])
    def test_get_item_with_positive_non_one_ids(self, item_id):
        """Test GET /items/{id} with positive non-1 IDs returns 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_very_large_id(self):
        """Test GET /items with very large ID."""
        r = client.get("/items/9999999999")
        assert r.status_code == 404

    def test_get_item_with_max_int_id(self):
        """Test GET /items with max integer ID."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404


# ============================================================================
# Test Class 2: Price Boundary Edge Cases
# ============================================================================
class TestPriceBoundaryEdgeCases:
    """Test price handling at boundary conditions."""

    @pytest.mark.parametrize("price", [0.001, 0.01, 0.1, 1.0, 10.0])
    def test_create_item_accepts_small_positive_prices(self, price):
        """Test POST /items accepts various small positive prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0, -0.01, -0.1, -1.0])
    def test_create_item_rejects_non_positive_prices_consistently(self, price):
        """Test POST /items rejects non-positive prices consistently."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_with_float_precision(self):
        """Test POST /items handles float precision."""
        prices = [1.11, 2.22, 3.33, 9.99, 99.99]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [1e-10, 1e-20, 1e-100])
    def test_create_item_with_very_small_positive_prices(self, price):
        """Test POST /items with very small positive prices."""
        r = client.post("/items", json={"name": "tiny", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [1e6, 1e10, 1e20, 1e100])
    def test_create_item_with_very_large_prices(self, price):
        """Test POST /items with very large prices."""
        r = client.post("/items", json={"name": "expensive", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


# ============================================================================
# Test Class 3: Name Field Boundary Conditions
# ============================================================================
class TestNameBoundaryConditions:
    """Test name field with various lengths and content."""

    def test_create_item_with_single_character_name(self):
        """Test POST /items with single character name."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_create_item_with_two_character_name(self):
        """Test POST /items with two character name."""
        r = client.post("/items", json={"name": "ab", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "ab"

    @pytest.mark.parametrize("length", [10, 50, 100, 500, 1000])
    def test_create_item_with_various_length_names(self, length):
        """Test POST /items with various name lengths."""
        name = "x" * length
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name
        assert len(r.json()["name"]) == length

    def test_create_item_with_very_long_name(self):
        """Test POST /items with extremely long name."""
        name = "a" * 10000
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 10000

    @pytest.mark.parametrize("name", ["name with spaces", "name-with-dashes", "name_with_underscores"])
    def test_create_item_with_various_characters(self, name):
        """Test POST /items with various character types."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


# ============================================================================
# Test Class 4: Integration: Create Then Get
# ============================================================================
class TestCreateThenGetIntegration:
    """Test create-then-retrieve workflow."""

    def test_create_item_then_get(self):
        """Test POST /items followed by GET /items/1."""
        # Create item
        create_r = client.post("/items", json={"name": "book", "price": 15.5})
        assert create_r.status_code == 200
        create_data = create_r.json()
        
        # Retrieve item
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        get_data = get_r.json()
        
        # Both responses should have same structure
        assert "id" in create_data
        assert "id" in get_data

    def test_get_before_create_returns_404(self):
        """Test GET /items/2 returns 404 before any item is created."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_multiple_creates_with_same_endpoint(self):
        """Test multiple POST /items calls."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        r3 = client.post("/items", json={"name": "item3", "price": 30.0})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 200
        
        assert r1.json()["name"] == "item1"
        assert r2.json()["name"] == "item2"
        assert r3.json()["name"] == "item3"

    def test_get_specific_item_id(self):
        """Test GET /items/1 always returns specific item."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        
        assert r1.json() == r2.json()
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1


# ============================================================================
# Test Class 5: Health Check Independence
# ============================================================================
class TestHealthCheckIndependence:
    """Test health check is independent of other operations."""

    def test_health_check_works_after_create(self):
        """Test GET /health works after POST /items."""
        client.post("/items", json={"name": "test", "price": 10.0})
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_check_works_after_get(self):
        """Test GET /health works after GET /items/1."""
        client.get("/items/1")
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_check_works_after_error(self):
        """Test GET /health works after error response."""
        client.post("/items", json={"name": "test", "price": 0})
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_check_before_and_after_operations(self):
        """Test health check consistency before/after operations."""
        r1 = client.get("/health")
        
        client.post("/items", json={"name": "test", "price": 10.0})
        client.get("/items/1")
        client.post("/items", json={"name": "test", "price": 0})
        
        r2 = client.get("/health")
        
        assert r1.json() == r2.json() == {"status": "ok"}


# ============================================================================
# Test Class 6: Error Recovery and Consistency
# ============================================================================
class TestErrorRecoveryAndConsistency:
    """Test API behavior after errors."""

    def test_system_operates_after_validation_error(self):
        """Test system continues after validation error."""
        # Trigger validation error
        r1 = client.post("/items", json={"name": "test"})
        assert r1.status_code == 422
        
        # System should still work
        r2 = client.get("/health")
        assert r2.status_code == 200

    def test_system_operates_after_business_error(self):
        """Test system continues after business rule error."""
        # Trigger business error
        r1 = client.post("/items", json={"name": "test", "price": -1})
        assert r1.status_code == 400
        
        # System should still work
        r2 = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r2.status_code == 200

    def test_system_operates_after_404_error(self):
        """Test system continues after 404 error."""
        # Trigger 404
        r1 = client.get("/items/99999")
        assert r1.status_code == 404
        
        # System should still work
        r2 = client.get("/health")
        assert r2.status_code == 200

    def test_error_does_not_affect_success_path(self):
        """Test error in one request doesn't affect next request."""
        # Create successful item
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        assert r1.status_code == 200
        
        # Attempt error request
        r2 = client.post("/items", json={"name": "item2", "price": -5})
        assert r2.status_code == 400
        
        # Next valid request should succeed
        r3 = client.post("/items", json={"name": "item3", "price": 20.0})
        assert r3.status_code == 200
        assert r3.json()["name"] == "item3"


# ============================================================================
# Test Class 7: HTTP Method Validation
# ============================================================================
class TestHTTPMethodValidation:
    """Test HTTP method enforcement."""

    def test_post_to_health_endpoint(self):
        """Test POST /health is not allowed or returns error."""
        r = client.post("/health")
        assert r.status_code in [404, 405, 422]

    def test_put_to_items_endpoint(self):
        """Test PUT /items is not allowed."""
        r = client.put("/items", json={"name": "test", "price": 10.0})
        assert r.status_code in [404, 405]

    def test_delete_to_items_endpoint(self):
        """Test DELETE /items is not allowed."""
        r = client.delete("/items")
        assert r.status_code in [404, 405]

    def test_patch_to_get_items_endpoint(self):
        """Test PATCH /items/1 is not allowed."""
        r = client.patch("/items/1")
        assert r.status_code in [404, 405]

    def test_options_to_items_endpoint(self):
        """Test OPTIONS /items returns appropriate response."""
        r = client.options("/items")
        # OPTIONS may or may not be allowed depending on implementation
        assert r.status_code in [200, 404, 405]


# ============================================================================
# Test Class 8: Data Isolation and Independence
# ============================================================================
class TestDataIsolationAndIndependence:
    """Test data isolation between requests."""

    def test_different_get_requests_independent(self):
        """Test GET requests for different IDs are independent."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/2")
        
        assert r1.status_code == 200
        assert r2.status_code == 404
        
        # Data should not leak
        assert r1.json()["id"] == 1
        assert "id" in r2.json()["detail"] is False  # 404 response

    def test_post_requests_independent(self):
        """Test POST requests don't interfere with each other."""
        responses = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 * (i + 1)})
            responses.append(r.json())
        
        # Verify each response is independent
        assert responses[0]["name"] == "item0"
        assert responses[1]["name"] == "item1"
        assert responses[2]["name"] == "item2"

    def test_interleaved_get_post_operations(self):
        """Test interleaved GET and POST operations."""
        r1 = client.get("/items/1")
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        r3 = client.get("/items/1")
        r4 = client.post("/items", json={"name": "test2", "price": 20.0})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 200
        assert r4.status_code == 200

    def test_mixed_success_and_error_operations(self):
        """Test mixed success and error operations."""
        responses = []
        
        responses.append(client.post("/items", json={"name": "valid1", "price": 10.0}))
        responses.append(client.post("/items", json={"name": "invalid", "price": -5}))
        responses.append(client.post("/items", json={"name": "valid2", "price": 20.0}))
        responses.append(client.get("/items/99"))
        responses.append(client.get("/items/1"))
        
        assert responses[0].status_code == 200
        assert responses[1].status_code == 400
        assert responses[2].status_code == 200
        assert responses[3].status_code == 404
        assert responses[4].status_code == 200


# ============================================================================
# Test Class 9: Response Type Consistency
# ============================================================================
class TestResponseTypeConsistency:
    """Test response types are consistent across similar operations."""

    def test_successful_responses_have_same_structure(self):
        """Test all successful responses follow same structure."""
        # Test POST success
        post_r = client.post("/items", json={"name": "test", "price": 10.0})
        post_data = post_r.json()
        
        # Test GET success
        get_r = client.get("/items/1")
        get_data = get_r.json()
        
        # Both should have id, name, price
        assert set(post_data.keys()) >= {"id", "name", "price"}
        assert set(get_data.keys()) >= {"id", "name", "price"}

    @pytest.mark.parametrize("price", [0, -1, -10])
    def test_error_responses_consistent(self, price):
        """Test error responses follow same format."""
        responses = []
        for p in [0, -1, -10]:
            r = client.post("/items", json={"name": "test", "price": p})
            responses.append(r.json())
        
        for resp in responses:
            assert "detail" in resp
            assert isinstance(resp["detail"], str)

    def test_404_responses_consistent(self):
        """Test 404 responses follow same format."""
        responses = []
        for item_id in [2, 3, 100]:
            r = client.get(f"/items/{item_id}")
            responses.append(r.json())
        
        for resp in responses:
            assert "detail" in resp
            assert resp["detail"] == "not found"

    def test_validation_error_responses_consistent(self):
        """Test validation error responses are consistent."""
        responses = []
        
        # Missing price
        responses.append(client.post("/items", json={"name": "test"}).json())
        # Wrong price type
        responses.append(client.post("/items", json={"name": "test", "price": "abc"}).json())
        # Missing name
        responses.append(client.post("/items", json={"price": 10.0}).json())
        
        for resp in responses:
            assert "detail" in resp
            assert isinstance(resp["detail"], (str, list, dict))
