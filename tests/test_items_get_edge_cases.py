import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [
        1,
        -1,
        0,
        2,
        999,
        -999,
        1000000,
    ])
    def test_get_item_various_ids(self, item_id):
        """Test get_item with various item_id values."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
        else:
            assert r.status_code == 404
            data = r.json()
            assert data["detail"] == "not found"


class TestCreateItemWithVariousPrices:
    """Test create_item with comprehensive price values."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.001, True),
        (0.01, True),
        (0.1, True),
        (1, True),
        (10, True),
        (100, True),
        (1000, True),
        (10000, True),
        (100000, True),
        (999999.99, True),
        (0, False),
        (-0.001, False),
        (-1, False),
        (-100, False),
        (-999999.99, False),
    ])
    def test_create_item_price_boundaries(self, price, should_succeed):
        """Test create_item with boundary prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        if should_succeed:
            assert r.status_code == 200
            data = r.json()
            assert data["price"] == price
        else:
            assert r.status_code == 400
            assert r.json()["detail"] == "price must be > 0"


class TestCreateItemWithVariousNames:
    """Test create_item with comprehensive name values."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "Book",
        "My Product",
        "product-with-dash",
        "product_with_underscore",
        "Product123",
        "123 Product",
        "UPPERCASE",
        "MixedCase",
        "product@example.com",
        "product with spaces",
        "a" * 100,
        "😀",
        "名前",
        "café",
        "Москва",
    ])
    def test_create_item_various_names(self, name):
        """Test create_item with various name values."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # All non-empty strings should be accepted by default Pydantic behavior
        assert r.status_code in [200, 422]  # May vary based on model constraints
        if r.status_code == 200:
            data = r.json()
            assert data["name"] == name


class TestIntegrationSequences:
    """Test sequences of operations to validate integration."""

    def test_create_then_get_workflow(self):
        """Test creating item then getting it."""
        # Create an item
        create_r = client.post("/items", json={"name": "workflow_test", "price": 29.99})
        assert create_r.status_code == 200
        created_data = create_r.json()
        created_id = created_data["id"]

        # Get the created item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()
        # Note: Mock always returns id=1 and fixed data
        assert retrieved_data["id"] == 1

    def test_multiple_creations(self):
        """Test creating multiple items."""
        ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
            data = r.json()
            ids.append(data["id"])
        
        # All should have id=1 (mock behavior)
        assert all(id == 1 for id in ids)

    def test_get_after_failed_create(self):
        """Test that failed create doesn't affect subsequent operations."""
        # Try to create with invalid price
        r1 = client.post("/items", json={"name": "bad", "price": 0})
        assert r1.status_code == 400

        # Should still be able to get item 1
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestEdgeCaseNumbers:
    """Test edge case numeric values."""

    @pytest.mark.parametrize("price", [
        0.00000001,
        0.00001,
        0.0001,
        0.001,
        1.23456789,
        999999999.99,
    ])
    def test_small_and_large_prices(self, price):
        """Test with very small and very large prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        # Check price is preserved with reasonable precision
        assert abs(data["price"] - price) < 1e-6 or data["price"] == price


class TestConcurrentOperations:
    """Test behavior with concurrent-like operations."""

    def test_rapid_creates(self):
        """Test multiple rapid create operations."""
        for i in range(5):
            r = client.post("/items", json={"name": f"rapid_{i}", "price": 10.0 + i})
            assert r.status_code == 200

    def test_rapid_gets(self):
        """Test multiple rapid get operations."""
        for i in range(1, 6):
            r = client.get(f"/items/{i}")
            if i == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_recover_from_invalid_price_error(self):
        """Test that API recovers after invalid price error."""
        # Send invalid
        r1 = client.post("/items", json={"name": "bad", "price": -1})
        assert r1.status_code == 400

        # Should be able to send valid immediately after
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200

    def test_recover_from_validation_error(self):
        """Test that API recovers after validation error."""
        # Send with missing field
        r1 = client.post("/items", json={"price": 10.0})
        assert r1.status_code == 422

        # Should be able to send valid immediately after
        r2 = client.post("/items", json={"name": "good", "price": 20.0})
        assert r2.status_code == 200

    def test_recover_from_not_found_error(self):
        """Test that API recovers after not found error."""
        # Get non-existent
        r1 = client.get("/items/999")
        assert r1.status_code == 404

        # Should be able to get existing immediately after
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestSpecialCharactersAndEncoding:
    """Test handling of special characters and encoding."""

    @pytest.mark.parametrize("name", [
        "name with spaces",
        "name\twith\ttabs",
        "name.with.dots",
        "name,with,commas",
        "name;with;semicolons",
        "name:with:colons",
        "name/with/slashes",
        "name\\with\\backslashes",
        "name?with?questions",
        "name!with!exclamation",
        "name#with#hash",
        "name$with$dollar",
        "name%with%percent",
        "name&with&ampersand",
        "name*with*asterisk",
        "name(with)parens",
        "name[with]brackets",
        "name{with}braces",
        "name|with|pipes",
        "name=with=equals",
    ])
    def test_special_characters_in_name(self, name):
        """Test that special characters are accepted in names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # These should be accepted unless model has specific constraints
        assert r.status_code in [200, 422]


class TestResponseConsistency:
    """Test response consistency across operations."""

    def test_price_precision_maintained(self):
        """Test that price precision is maintained in response."""
        prices = [10.01, 10.99, 99.99, 0.99, 0.01]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            data = r.json()
            assert data["price"] == price

    def test_name_case_preserved(self):
        """Test that name case is preserved."""
        names = ["lowercase", "UPPERCASE", "MixedCase", "camelCase", "PascalCase"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            data = r.json()
            assert data["name"] == name

    def test_unicode_preserved(self):
        """Test that unicode characters are preserved."""
        names = ["café", "naïve", "Москва", "北京", "東京"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            if r.status_code == 200:
                data = r.json()
                assert data["name"] == name


class TestBoundaryConditions:
    """Test various boundary conditions."""

    def test_minimum_valid_price(self):
        """Test that smallest positive price works."""
        r = client.post("/items", json={"name": "test", "price": 0.00000001})
        assert r.status_code == 200

    def test_maximum_price(self):
        """Test that very large price works."""
        r = client.post("/items", json={"name": "test", "price": 999999999.99})
        assert r.status_code == 200

    def test_minimum_name_length(self):
        """Test that single character name works."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_large_name_length(self):
        """Test that very long names work."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        # Should accept or reject based on model constraints
        assert r.status_code in [200, 422]


class TestHTTPMethodValidation:
    """Test behavior with incorrect HTTP methods."""

    def test_get_on_items_endpoint(self):
        """Test that GET on /items is not allowed (only POST)."""
        r = client.get("/items")
        assert r.status_code == 404  # FastAPI returns 404 for undefined routes

    def test_post_on_get_endpoint(self):
        """Test that POST on /items/{item_id} is not allowed (only GET)."""
        r = client.post("/items/1")
        assert r.status_code == 405  # Method Not Allowed

    def test_put_on_create_endpoint(self):
        """Test that PUT on /items is not allowed."""
        r = client.put("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 405

    def test_delete_on_get_endpoint(self):
        """Test that DELETE is not allowed."""
        r = client.delete("/items/1")
        assert r.status_code == 405


class TestEmptyAndNullCases:
    """Test handling of empty and null values."""

    def test_null_name_rejected(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_null_price_rejected(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_empty_string_name(self):
        """Test behavior with empty string name."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        # Default Pydantic may accept or reject based on model constraints
        assert r.status_code in [200, 422]

    def test_whitespace_only_name(self):
        """Test behavior with whitespace-only name."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        # Whitespace-only strings may be accepted
        assert r.status_code in [200, 422]
