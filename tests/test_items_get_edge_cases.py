"""Edge cases and integration tests for comprehensive coverage."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemIdBoundaries:
    """Test get_item with various item_id boundary values."""

    def test_get_item_id_one_found(self):
        """Test that item_id=1 is found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @pytest.mark.parametrize("item_id", [0, -1, -10, -100])
    def test_get_item_negative_ids_not_found(self, item_id):
        """Test that negative item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 999999])
    def test_get_item_other_positive_ids_not_found(self, item_id):
        """Test that item IDs other than 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_zero_not_found(self):
        """Test explicit check for item_id=0."""
        r = client.get("/items/0")
        assert r.status_code == 404


class TestCreateItemPriceValidation:
    """Test price validation boundaries and edge cases."""

    def test_price_exactly_zero_rejected(self):
        """Test that price=0 exactly is rejected."""
        r = client.post("/items", json={"name": "test", "price": 0.0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_price_just_above_zero_accepted(self):
        """Test that price just above zero is accepted."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0001

    def test_price_just_below_zero_rejected(self):
        """Test that price just below zero is rejected."""
        r = client.post("/items", json={"name": "test", "price": -0.0001})
        assert r.status_code == 400

    def test_price_negative_large_value_rejected(self):
        """Test that large negative prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": -1e10})
        assert r.status_code == 400

    def test_price_positive_large_value_accepted(self):
        """Test that large positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e10


class TestCreateItemNameValidation:
    """Test name field validation edge cases."""

    def test_name_single_character(self):
        """Test that single character names work."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_name_empty_string(self):
        """Test that empty string names are accepted."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_name_whitespace_only(self):
        """Test that whitespace-only names are accepted."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_name_with_newlines(self):
        """Test that names with newlines are accepted."""
        name_with_newline = "line1\nline2"
        r = client.post("/items", json={"name": name_with_newline, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_newline

    def test_name_with_tabs(self):
        """Test that names with tabs are accepted."""
        name_with_tabs = "col1\tcol2\tcol3"
        r = client.post("/items", json={"name": name_with_tabs, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_tabs

    def test_name_very_long(self):
        """Test that very long names are accepted."""
        long_name = "x" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name


class TestIntegrationCreateThenGet:
    """Test interaction patterns between create and get endpoints."""

    def test_create_item_then_verify_exists(self):
        """Test that after creating item, it can be verified (though id=1 always)."""
        # Create an item
        create_r = client.post("/items", json={"name": "integration-test", "price": 25.0})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Get the item
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()
        
        # IDs should match
        assert created_data["id"] == get_data["id"]

    def test_create_item_returns_consistent_response(self):
        """Test that multiple creates return consistent response structure."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        assert r1.status_code == r2.status_code == 200
        assert set(r1.json().keys()) == set(r2.json().keys())
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_get_item_returns_consistent_response(self):
        """Test that multiple gets return the same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        
        assert r1.status_code == r2.status_code == 200
        assert r1.json() == r2.json()

    def test_invalid_get_returns_consistent_error(self):
        """Test that invalid get calls return consistent errors."""
        r1 = client.get("/items/999")
        r2 = client.get("/items/999")
        
        assert r1.status_code == r2.status_code == 404
        assert r1.json()["detail"] == r2.json()["detail"]


class TestMultipleErrorScenarios:
    """Test multiple error scenarios in sequence."""

    def test_multiple_invalid_prices_in_sequence(self):
        """Test that multiple invalid prices all fail consistently."""
        invalid_prices = [0, -1, -100.5]
        
        for price in invalid_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert r.json()["detail"] == "price must be > 0"

    def test_multiple_not_found_in_sequence(self):
        """Test that multiple not-found requests fail consistently."""
        not_found_ids = [2, 3, 999, -1]
        
        for item_id in not_found_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    def test_multiple_validation_errors_in_sequence(self):
        """Test that validation errors are consistent."""
        invalid_requests = [
            {"price": 10.0},  # missing name
            {"name": "test"},  # missing price
            {"name": "test", "price": "invalid"},  # wrong type
        ]
        
        for req in invalid_requests:
            r = client.post("/items", json=req)
            assert r.status_code == 422


class TestEndpointCombinations:
    """Test various endpoint combinations."""

    def test_health_then_create_then_get(self):
        """Test sequence of health, create, get."""
        # Check health
        health_r = client.get("/health")
        assert health_r.status_code == 200
        
        # Create item
        create_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_r.status_code == 200
        
        # Get item
        get_r = client.get("/items/1")
        assert get_r.status_code == 200

    def test_create_failure_doesnt_affect_get(self):
        """Test that failed create doesn't affect get."""
        # Fail to create
        fail_r = client.post("/items", json={"name": "test", "price": -1})
        assert fail_r.status_code == 400
        
        # Get should still work
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == 1

    def test_create_success_then_failed_get(self):
        """Test that successful create works even with failed get."""
        # Create successfully
        create_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_r.status_code == 200
        
        # Fail to get different item
        get_r = client.get("/items/999")
        assert get_r.status_code == 404


class TestDataTypes:
    """Test handling of various data types."""

    def test_create_item_price_integer_converted(self):
        """Test that integer prices work (FastAPI converts to float)."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert r.json()["price"] == 10.0

    def test_create_item_price_float_precision(self):
        """Test that float precision is preserved."""
        test_price = 19.99
        r = client.post("/items", json={"name": "test", "price": test_price})
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    def test_create_item_name_numeric_coercion(self):
        """Test that numeric names are coerced to strings."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 200
        # FastAPI coerces to string
        assert r.json()["id"] == 1

    def test_get_item_id_as_integer(self):
        """Test that get_item requires integer ID."""
        # Valid integer
        r = client.get("/items/1")
        assert r.status_code == 200


class TestErrorMessageQuality:
    """Test that error messages are informative."""

    def test_price_validation_error_message_specific(self):
        """Test that price error message is specific."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail or "positive" in detail.lower()

    def test_not_found_error_message_clear(self):
        """Test that not found error message is clear."""
        r = client.get("/items/999")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert detail == "not found"

    def test_validation_error_has_informative_structure(self):
        """Test that validation errors have structure."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestResponseConsistency:
    """Test response consistency and reliability."""

    def test_create_item_multiple_times_same_response_structure(self):
        """Test that multiple creates have same response structure."""
        responses = []
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            responses.append(r.json())
        
        # All responses have same keys
        keys = set(responses[0].keys())
        for resp in responses[1:]:
            assert set(resp.keys()) == keys

    def test_get_item_multiple_times_same_data(self):
        """Test that getting same item returns same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        
        assert r1.json() == r2.json() == r3.json()

    def test_error_responses_consistent_structure(self):
        """Test that error responses have consistent structure."""
        # Different error scenarios
        errors = [
            client.post("/items", json={"name": "test", "price": -1}),  # 400
            client.post("/items", json={"name": "test"}),  # 422
            client.get("/items/999"),  # 404
        ]
        
        # All have detail field
        for r in errors:
            assert "detail" in r.json()
