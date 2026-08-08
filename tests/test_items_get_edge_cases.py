"""
Edge cases, path parameter validation, and integration scenario tests.
Tests focus on boundary values, error recovery, and multi-step workflows.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get item endpoint."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (0, 404),
        (-1, 404),
        (999, 404),
        (999999, 404),
    ])
    def test_get_item_various_ids(self, item_id, expected_status):
        """Test various item IDs including boundaries."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestGetItemBoundaryValues:
    """Test boundary value handling for item IDs."""

    def test_get_item_id_zero(self):
        """Item ID 0 should not be found."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_negative(self):
        """Negative item ID should not be found."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_id_very_large(self):
        """Very large item ID should not be found."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_get_item_id_one_is_found(self):
        """Item ID 1 should be found."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_id_two_not_found(self):
        """Item ID 2 should not be found."""
        r = client.get("/items/2")
        assert r.status_code == 404


class TestGetItemInvalidPathParameters:
    """Test invalid path parameter formats."""

    def test_non_numeric_item_id(self):
        """Non-numeric item_id should return error."""
        r = client.get("/items/abc")
        assert r.status_code in [400, 422]

    def test_float_item_id(self):
        """Float item_id might fail or be truncated."""
        r = client.get("/items/1.5")
        assert r.status_code in [200, 400, 404, 422]

    def test_special_chars_in_item_id(self):
        """Special characters in item_id should return error."""
        r = client.get("/items/1!@#")
        assert r.status_code in [400, 422]


class TestGetItemResponseValidation:
    """Test response validation for get item."""

    def test_get_item_response_has_correct_id(self):
        """Response for item/1 should have id=1."""
        r = client.get("/items/1")
        assert r.json()["id"] == 1

    def test_get_item_response_has_name(self):
        """Response should include name field."""
        r = client.get("/items/1")
        assert "name" in r.json()
        assert isinstance(r.json()["name"], str)

    def test_get_item_response_has_price(self):
        """Response should include price field."""
        r = client.get("/items/1")
        assert "price" in r.json()
        assert isinstance(r.json()["price"], (int, float))

    def test_get_item_response_price_is_positive(self):
        """Response price should be positive."""
        r = client.get("/items/1")
        assert r.json()["price"] > 0


class TestIntegrationScenarios:
    """Test multi-step workflows combining multiple endpoints."""

    def test_create_then_get_item(self):
        """Create item then retrieve it."""
        # Create item
        create_r = client.post("/items", json={"name": "book", "price": 12.5})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]

        # Get created item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == created_id

    def test_create_multiple_items(self):
        """Create multiple items successfully."""
        items = [
            {"name": "item1", "price": 1.0},
            {"name": "item2", "price": 2.0},
            {"name": "item3", "price": 3.0},
        ]
        for item_data in items:
            r = client.post("/items", json=item_data)
            assert r.status_code == 200
            assert r.json()["name"] == item_data["name"]

    def test_create_then_get_invalid_item(self):
        """Create item then try to get non-existent item."""
        # Create valid item
        create_r = client.post("/items", json={"name": "item", "price": 5.0})
        assert create_r.status_code == 200

        # Try to get non-existent item
        get_r = client.get("/items/999")
        assert get_r.status_code == 404

    def test_sequential_create_operations(self):
        """Execute multiple create operations in sequence."""
        test_items = [
            ("apple", 0.99),
            ("banana", 0.59),
            ("orange", 0.79),
            ("grape", 2.99),
            ("melon", 4.99),
        ]

        for name, price in test_items:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200, f"Failed to create {name}"
            data = r.json()
            assert data["name"] == name
            assert data["price"] == price

    def test_get_existing_then_non_existing(self):
        """Get existing item, then non-existing item."""
        # Get existing
        r1 = client.get("/items/1")
        assert r1.status_code == 200

        # Get non-existing
        r2 = client.get("/items/999")
        assert r2.status_code == 404

    def test_health_check_always_available(self):
        """Health endpoint should be available during operations."""
        # Check health
        r = client.get("/health")
        assert r.status_code == 200

        # Create item
        client.post("/items", json={"name": "item", "price": 1.0})

        # Check health again
        r = client.get("/health")
        assert r.status_code == 200


class TestErrorRecovery:
    """Test handling of error conditions."""

    def test_create_with_invalid_price_then_valid_price(self):
        """Handle invalid price error, then create with valid price."""
        # Invalid
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400

        # Valid
        r2 = client.post("/items", json={"name": "item", "price": 1.0})
        assert r2.status_code == 200

    def test_get_non_existent_then_existing(self):
        """Handle not found, then get existing item."""
        # Non-existent
        r1 = client.get("/items/999")
        assert r1.status_code == 404

        # Existing
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_invalid_request_then_valid_request(self):
        """Handle validation error, then send valid request."""
        # Missing field
        r1 = client.post("/items", json={"name": "item"})
        assert r1.status_code == 422

        # Valid
        r2 = client.post("/items", json={"name": "item", "price": 1.0})
        assert r2.status_code == 200


class TestErrorMessageConsistency:
    """Test error message format and content."""

    def test_price_error_message_not_empty(self):
        """Price validation error should have meaningful message."""
        r = client.post("/items", json={"name": "item", "price": 0})
        detail = r.json().get("detail", "")
        assert len(detail) > 0

    def test_not_found_error_message_not_empty(self):
        """Not found error should have meaningful message."""
        r = client.get("/items/999")
        detail = r.json().get("detail", "")
        assert len(detail) > 0

    def test_validation_error_has_detail(self):
        """Validation error should have detail field."""
        r = client.post("/items", json={"price": 10.0})
        assert "detail" in r.json()

    def test_business_logic_error_has_detail(self):
        """Business logic error should have detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert "detail" in r.json()


class TestEndToEndWorkflows:
    """Complete end-to-end workflow scenarios."""

    def test_workflow_health_check_create_get(self):
        """Workflow: health check -> create -> get item."""
        # Health check
        health = client.get("/health")
        assert health.status_code == 200

        # Create
        create = client.post("/items", json={"name": "widget", "price": 5.99})
        assert create.status_code == 200
        item_id = create.json()["id"]

        # Get
        get = client.get(f"/items/{item_id}")
        assert get.status_code == 200
        assert get.json()["name"] == "widget"

    def test_workflow_multiple_creates_validate_responses(self):
        """Create multiple items and validate all responses."""
        test_data = [
            ("book", 15.99),
            ("pen", 2.50),
            ("notebook", 8.00),
        ]

        results = []
        for name, price in test_data:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == name
            assert data["price"] == price
            results.append(data)

        # Verify all results have consistent structure
        for result in results:
            assert "id" in result
            assert "name" in result
            assert "price" in result

    def test_workflow_error_handling_and_recovery(self):
        """Test error handling and recovery in workflow."""
        # Try invalid create
        r1 = client.post("/items", json={"name": "item", "price": -5.0})
        assert r1.status_code == 400

        # Try valid create
        r2 = client.post("/items", json={"name": "item", "price": 5.0})
        assert r2.status_code == 200

        # Try get non-existent
        r3 = client.get("/items/999")
        assert r3.status_code == 404

        # Get existing
        r4 = client.get("/items/1")
        assert r4.status_code == 200


class TestConcurrentLikeOperations:
    """Test patterns similar to concurrent operations."""

    def test_multiple_creates_interleaved_with_gets(self):
        """Interleave create and get operations."""
        # Create 1
        c1 = client.post("/items", json={"name": "item1", "price": 1.0})
        assert c1.status_code == 200

        # Get 1
        g1 = client.get("/items/1")
        assert g1.status_code == 200

        # Create 2
        c2 = client.post("/items", json={"name": "item2", "price": 2.0})
        assert c2.status_code == 200

        # Get 2
        g2 = client.get("/items/1")
        assert g2.status_code == 200

    def test_rapid_get_requests_same_item(self):
        """Multiple rapid get requests for same item."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_invalid_then_valid_creates(self):
        """Alternate between invalid and valid create operations."""
        for i in range(3):
            # Invalid
            r1 = client.post("/items", json={"name": "item", "price": -1.0})
            assert r1.status_code == 400

            # Valid
            r2 = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r2.status_code == 200


class TestResponseParsing:
    """Test response parsing and data integrity."""

    def test_create_response_json_valid(self):
        """Create response should be valid JSON."""
        r = client.post("/items", json={"name": "item", "price": 1.0})
        # If we can call .json(), it's valid JSON
        data = r.json()
        assert isinstance(data, dict)

    def test_get_response_json_valid(self):
        """Get response should be valid JSON."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data, dict)

    def test_error_response_json_valid(self):
        """Error response should be valid JSON."""
        r = client.get("/items/999")
        data = r.json()
        assert isinstance(data, dict)

    def test_response_fields_accessible(self):
        """Response fields should be accessible."""
        r = client.post("/items", json={"name": "item", "price": 1.0})
        data = r.json()
        # Should not raise KeyError
        _ = data["id"]
        _ = data["name"]
        _ = data["price"]


class TestEdgeCaseIntegrations:
    """Edge cases in integration scenarios."""

    def test_create_with_maximum_price(self):
        """Create with very large price."""
        r = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99

    def test_create_with_minimum_price(self):
        """Create with minimum valid price."""
        r = client.post("/items", json={"name": "cheap", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_with_very_long_name_then_get(self):
        """Create with very long name and retrieve."""
        long_name = "x" * 5000
        r1 = client.post("/items", json={"name": long_name, "price": 1.0})
        assert r1.status_code == 200

        # Get the created item
        item_id = r1.json()["id"]
        r2 = client.get(f"/items/{item_id}")
        assert r2.status_code == 200

    def test_get_all_boundary_ids(self):
        """Test getting items with various boundary IDs."""
        boundary_ids = [-999999, -1, 0, 1, 2, 999999]
        for item_id in boundary_ids:
            r = client.get(f"/items/{item_id}")
            # All except 1 should be 404
            if item_id == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404
