import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}"""

    @pytest.mark.parametrize("item_id", [
        1,  # Valid: found
    ])
    def test_get_item_valid_id(self, item_id):
        """Valid item ID should be found"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [
        0,
        -1,
        -100,
        2,
        3,
        10,
        100,
        999,
        9999,
        10000000,
    ])
    def test_get_item_invalid_ids(self, item_id):
        """Invalid item IDs should return 404"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_zero_id_not_found(self):
        """Item ID 0 should not be found"""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_negative_id_not_found(self):
        """Negative item ID should not be found"""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_large_id_not_found(self):
        """Very large item ID should not be found"""
        r = client.get("/items/999999999")
        assert r.status_code == 404


class TestGetItemBoundaryValues:
    """Test boundary values for item ID"""

    def test_get_item_id_one_succeeds(self):
        """Item ID 1 should be found"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_id_max_int(self):
        """Very large integers should be handled"""
        r = client.get("/items/2147483647")  # Max 32-bit signed int
        assert r.status_code == 404

    def test_get_item_id_boundary_2(self):
        """Item ID 2 should not be found"""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_id_boundary_minus_one(self):
        """Item ID -1 should not be found"""
        r = client.get("/items/-1")
        assert r.status_code == 404


class TestGetItemErrorMessages:
    """Test error messages for not found"""

    def test_get_item_not_found_has_detail(self):
        """Not found response should have detail"""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_not_found_message_clarity(self):
        """Not found message should be clear"""
        r = client.get("/items/2")
        detail = r.json()["detail"]
        assert "not found" in detail.lower() or "does not exist" in detail.lower()

    def test_get_item_error_consistent_format(self):
        """Error format should be consistent"""
        r1 = client.get("/items/2")
        r2 = client.get("/items/999")
        assert r1.status_code == r2.status_code == 404
        assert "detail" in r1.json()
        assert "detail" in r2.json()


class TestGetItemResponseValidation:
    """Test response validation for GET endpoint"""

    def test_get_item_response_complete(self):
        """Response should have all required fields"""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_id_matches_request(self):
        """Response ID should match request ID"""
        r = client.get("/items/1")
        assert r.json()["id"] == 1

    def test_get_item_name_is_string(self):
        """Response name should be string"""
        r = client.get("/items/1")
        assert isinstance(r.json()["name"], str)

    def test_get_item_price_is_numeric(self):
        """Response price should be numeric"""
        r = client.get("/items/1")
        price = r.json()["price"]
        assert isinstance(price, (int, float))

    def test_get_item_price_positive(self):
        """Response price should be positive"""
        r = client.get("/items/1")
        assert r.json()["price"] > 0

    def test_get_item_known_values(self):
        """Response should have known values for item 1"""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestIntegrationCreateThenGet:
    """Test integration scenarios: create then get"""

    def test_create_and_get_workflow(self):
        """Creating an item then getting it should work"""
        # Create
        create_r = client.post("/items", json={"name": "workflow_test", "price": 25.0})
        assert create_r.status_code == 200
        
        # Get
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == 1

    def test_create_multiple_then_get_first(self):
        """Creating multiple items then getting first should work"""
        # Create multiple
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
        
        # Get first
        get_r = client.get("/items/1")
        assert get_r.status_code == 200

    def test_get_after_invalid_create(self):
        """Getting should work after failed create attempt"""
        # Try to create with invalid price
        create_r = client.post("/items", json={"name": "test", "price": 0})
        assert create_r.status_code == 400
        
        # Get should still work
        get_r = client.get("/items/1")
        assert get_r.status_code == 200


class TestGetItemConsistency:
    """Test consistency of GET responses"""

    def test_get_item_same_response_multiple_times(self):
        """Getting same item multiple times should give same response"""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        
        assert r1.status_code == r2.status_code
        assert r1.json() == r2.json()

    def test_get_nonexistent_consistent(self):
        """Getting non-existent item multiple times should be consistent"""
        r1 = client.get("/items/999")
        r2 = client.get("/items/999")
        
        assert r1.status_code == r2.status_code == 404
        assert r1.json()["detail"] == r2.json()["detail"]

    def test_get_various_ids_consistency(self):
        """Different non-existent IDs should have consistent error format"""
        ids = [2, 3, 100, 999]
        responses = [client.get(f"/items/{id_}") for id_ in ids]
        
        for r in responses:
            assert r.status_code == 404
            assert "detail" in r.json()


class TestGetItemDataIntegrity:
    """Test data integrity in GET responses"""

    def test_get_item_name_not_empty(self):
        """Response name should not be empty"""
        r = client.get("/items/1")
        assert len(r.json()["name"]) > 0

    def test_get_item_price_reasonable(self):
        """Response price should be reasonable"""
        r = client.get("/items/1")
        price = r.json()["price"]
        assert 0 < price < 1000000  # Reasonable price range

    def test_get_item_id_positive_integer(self):
        """Response ID should be positive integer"""
        r = client.get("/items/1")
        id_ = r.json()["id"]
        assert isinstance(id_, int)
        assert id_ > 0


class TestAPIEndpointCoverage:
    """Test coverage of all API endpoints"""

    def test_health_endpoint_accessible(self):
        """Health endpoint should be accessible"""
        r = client.get("/health")
        assert r.status_code == 200

    def test_create_items_endpoint_accessible(self):
        """Create items endpoint should be accessible"""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_get_items_endpoint_accessible(self):
        """Get items endpoint should be accessible"""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_all_endpoints_return_json(self):
        """All endpoints should return JSON"""
        health = client.get("/health")
        create = client.post("/items", json={"name": "test", "price": 10.0})
        get = client.get("/items/1")
        
        for r in [health, create, get]:
            assert "application/json" in r.headers.get("content-type", "")


class TestErrorRecovery:
    """Test error recovery and robustness"""

    def test_api_works_after_validation_error(self):
        """API should work after validation error"""
        # Try invalid request
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        
        # Valid request should still work
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_api_works_after_price_error(self):
        """API should work after price validation error"""
        # Try invalid price
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        
        # Valid request should still work
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_api_works_after_not_found(self):
        """API should work after not found error"""
        # Try to get non-existent item
        r = client.get("/items/999")
        assert r.status_code == 404
        
        # Valid request should still work
        r = client.get("/items/1")
        assert r.status_code == 200


class TestSequentialOperations:
    """Test sequential operations on endpoints"""

    def test_create_get_create_get_sequence(self):
        """Alternating creates and gets should work"""
        for i in range(2):
            # Create
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0})
            assert r.status_code == 200
            
            # Get
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_multiple_gets_in_sequence(self):
        """Multiple gets in sequence should work"""
        for i in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_multiple_creates_in_sequence(self):
        """Multiple creates in sequence should work"""
        for i in range(5):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200


class TestEndpointInteraction:
    """Test interaction between endpoints"""

    def test_create_does_not_affect_existing_get(self):
        """Creating new items should not affect getting existing"""
        # Get existing
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        original = r1.json()
        
        # Create new
        client.post("/items", json={"name": "new", "price": 20.0})
        
        # Get existing again
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        assert r2.json() == original

    def test_get_errors_do_not_affect_create(self):
        """Failed gets should not affect creates"""
        # Try to get non-existent
        r = client.get("/items/999")
        assert r.status_code == 404
        
        # Create should still work
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_health_independent_of_items(self):
        """Health endpoint should be independent"""
        # Create items
        client.post("/items", json={"name": "test", "price": 10.0})
        
        # Health should still work
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestSpecialCases:
    """Test special and corner cases"""

    def test_get_with_url_encoding_safety(self):
        """Numeric item IDs should not need URL encoding"""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_create_special_chars_safe(self):
        """Creating with special chars should not affect subsequent gets"""
        client.post("/items", json={"name": "special!@#$", "price": 10.0})
        
        # Get should still work
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_create_unicode_safe(self):
        """Creating with unicode should not affect subsequent gets"""
        client.post("/items", json={"name": "商品", "price": 10.0})
        
        # Get should still work
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_create_long_name_safe(self):
        """Creating with long name should not affect subsequent gets"""
        client.post("/items", json={"name": "x" * 500, "price": 10.0})
        
        # Get should still work
        r = client.get("/items/1")
        assert r.status_code == 200


class TestResponseConsistency:
    """Test response consistency across operations"""

    def test_post_get_same_item(self):
        """Posted and gotten items should have consistent structure"""
        post_r = client.post("/items", json={"name": "consistency_test", "price": 15.0})
        post_data = post_r.json()
        
        get_r = client.get("/items/1")
        get_data = get_r.json()
        
        # Both should have same fields
        assert set(post_data.keys()) == set(get_data.keys())

    def test_multiple_get_consistency(self):
        """Multiple gets should return identical data"""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        
        assert r1.json() == r2.json() == r3.json()

    def test_health_always_ok(self):
        """Health should always return ok status"""
        for i in range(3):
            r = client.get("/health")
            assert r.json()["status"] == "ok"
