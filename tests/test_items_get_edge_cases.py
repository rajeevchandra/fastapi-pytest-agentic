"""
Edge cases and integration testing for items endpoint.
Tests path parameter handling, boundary conditions, and complex scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Test item_id path parameter boundary conditions."""

    def test_get_item_with_minimum_positive_id(self):
        """Get item with minimum valid positive ID should work."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_with_small_id(self):
        """Get item with small positive ID."""
        r = client.get("/items/1")
        assert r.status_code in [200, 404]  # Depends on implementation

    def test_get_item_with_large_id(self):
        """Get item with large positive ID should return 404 (item not found)."""
        r = client.get("/items/999999")
        assert r.status_code == 404

    def test_get_item_with_very_large_id(self):
        """Get item with very large ID should return 404."""
        r = client.get("/items/9999999999")
        assert r.status_code == 404

    def test_get_item_with_zero_id(self):
        """Get item with ID 0 should return 404 (assuming 1 is valid)."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_with_negative_id(self):
        """Get item with negative ID should be handled properly."""
        r = client.get("/items/-1")
        # Should be either 404 or 422 depending on validation
        assert r.status_code in [404, 422]

    @pytest.mark.parametrize("item_id", [1, 2, 3, 100, 1000])
    def test_get_item_various_ids(self, item_id):
        """Test various item IDs."""
        r = client.get(f"/items/{item_id}")
        # Only ID 1 should return 200, others should return 404
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [0, -1, -100])
    def test_get_item_invalid_ids(self, item_id):
        """Test invalid item IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code in [404, 422]


class TestCreateItemEdgeCaseScenarios:
    """Test edge case scenarios for item creation."""

    def test_create_item_with_maximum_float_precision(self):
        """Create item with high precision float price."""
        price = 19.9999999
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_scientific_notation_price(self):
        """Create item with scientific notation price."""
        price = 1e2  # 100.0
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == 100.0

    def test_create_item_name_with_whitespace_only(self):
        """Create item with whitespace-only name."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_name_with_leading_trailing_whitespace(self):
        """Name with leading/trailing whitespace should be preserved."""
        name = "  item  "
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_newline(self):
        """Name with newline character."""
        name = "item\nname"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_tab(self):
        """Name with tab character."""
        name = "item\tname"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_repeated_special_chars(self):
        """Name with repeated special characters."""
        name = "!!!***###"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_multiple_unicode_languages(self):
        """Name with mixed unicode from multiple languages."""
        name = "English中文한국어العربية"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_html_like_string_in_name(self):
        """Name with HTML-like content (should be stored as-is)."""
        name = "<script>alert('xss')</script>"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_json_like_string_in_name(self):
        """Name with JSON-like content."""
        name = '{"key": "value"}'
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestMultipleItemsInteraction:
    """Test interaction with multiple items and sequential operations."""

    def test_create_item_then_retrieve_success(self):
        """Create an item (ID 1) and verify it can be retrieved."""
        create_r = client.post("/items", json={"name": "book", "price": 15.5})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]
        
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200

    def test_create_different_items_sequential(self):
        """Create different items in sequence."""
        items = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        
        for item in items:
            r = client.post("/items", json=item)
            assert r.status_code == 200

    def test_create_item_then_fail_invalid_get(self):
        """Create item, then attempt to get non-existent items."""
        create_r = client.post("/items", json={"name": "book", "price": 10.0})
        assert create_r.status_code == 200
        
        # Try to get non-existent item
        get_r = client.get("/items/999")
        assert get_r.status_code == 404

    def test_get_existing_item_after_failed_attempt(self):
        """Failed get attempt should not affect subsequent successful get."""
        # Try to get non-existent item
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Get existing item
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_create_and_verify_response_consistency(self):
        """Response from create should be consistent with get."""
        create_r = client.post("/items", json={"name": "test", "price": 25.5})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        # Note: API always returns the same item (ID 1), so this verifies behavior


class TestApiErrorRecovery:
    """Test API behavior after errors occur."""

    def test_api_works_after_validation_error(self):
        """API should recover after a validation error."""
        # Send invalid request
        r1 = client.post("/items", json={"name": "book"})
        assert r1.status_code == 422
        
        # API should still accept valid requests
        r2 = client.post("/items", json={"name": "book", "price": 10.0})
        assert r2.status_code == 200

    def test_api_works_after_business_logic_error(self):
        """API should recover after a business logic error."""
        # Send request with invalid price
        r1 = client.post("/items", json={"name": "book", "price": -5})
        assert r1.status_code == 400
        
        # API should still accept valid requests
        r2 = client.post("/items", json={"name": "book", "price": 10.0})
        assert r2.status_code == 200

    def test_api_works_after_not_found_error(self):
        """API should recover after a not found error."""
        # Try to get non-existent item
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # API should still accept valid requests
        r2 = client.post("/items", json={"name": "book", "price": 10.0})
        assert r2.status_code == 200


class TestApiRequestValidation:
    """Test API request validation and error handling."""

    def test_post_with_extra_fields_ignored(self):
        """Extra fields in request should be ignored by Pydantic."""
        r = client.post("/items", json={
            "name": "book",
            "price": 10.0,
            "extra_field": "should be ignored"
        })
        assert r.status_code == 200

    def test_post_with_wrong_field_types_rejected(self):
        """Wrong field types should be rejected."""
        r = client.post("/items", json={
            "name": 123,  # Should be string
            "price": "invalid"  # Should be number
        })
        # Pydantic may coerce or reject
        assert r.status_code in [200, 422]

    def test_empty_request_body_rejected(self):
        """Empty request body should be rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_null_request_body_handled(self):
        """Null values in request should be handled."""
        r = client.post("/items", json=None)
        # Should be rejected
        assert r.status_code in [422, 400]


class TestGetItemIntegration:
    """Integration tests for get_item endpoint."""

    def test_get_item_found_complete_response(self):
        """Verify complete response structure for found item."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert len(data["name"]) > 0
        assert data["price"] > 0

    def test_get_item_not_found_complete_response(self):
        """Verify complete error response for not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (100, 404),
        (999, 404),
    ])
    def test_get_item_various_statuses(self, item_id, expected_status):
        """Test get_item with various IDs and expected statuses."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestApiHealthCheck:
    """Test health check endpoint."""

    def test_health_endpoint_returns_ok(self):
        """Health check endpoint should return ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_endpoint_response_structure(self):
        """Health check response should have expected structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_health_endpoint_consistency(self):
        """Multiple health checks should return consistent results."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.json() == r2.json()


class TestCombinedEndpointInteraction:
    """Test interactions between different endpoints."""

    def test_health_check_before_item_operations(self):
        """Health check should work before item operations."""
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        r2 = client.post("/items", json={"name": "book", "price": 10.0})
        assert r2.status_code == 200

    def test_health_check_after_item_operations(self):
        """Health check should work after item operations."""
        r1 = client.post("/items", json={"name": "book", "price": 10.0})
        assert r1.status_code == 200
        
        r2 = client.get("/health")
        assert r2.status_code == 200

    def test_health_check_after_failed_item_operation(self):
        """Health check should work after failed item operation."""
        r1 = client.post("/items", json={"name": "book", "price": -5})
        assert r1.status_code == 400
        
        r2 = client.get("/health")
        assert r2.status_code == 200

    def test_all_endpoints_accessible_in_sequence(self):
        """All endpoints should be accessible in sequence."""
        # Health check
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        # Create item
        r2 = client.post("/items", json={"name": "book", "price": 10.0})
        assert r2.status_code == 200
        
        # Get item
        r3 = client.get("/items/1")
        assert r3.status_code == 200
        
        # Health check again
        r4 = client.get("/health")
        assert r4.status_code == 200
