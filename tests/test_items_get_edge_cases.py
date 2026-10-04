"""Path parameter edge cases and integration testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Test path parameter edge cases with boundary values."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_item_id(self, item_id):
        """Valid item ID should return 200."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, -100])
    def test_get_item_zero_and_negative_ids(self, item_id):
        """Zero and negative IDs should return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 999999])
    def test_get_item_large_ids(self, item_id):
        """Large item IDs should return 404 (not found)."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    def test_get_item_boundary_zero(self):
        """Item ID of 0 (boundary) should return 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_boundary_one(self):
        """Item ID of 1 (valid boundary) should return 200."""
        response = client.get("/items/1")
        assert response.status_code == 200


class TestGetItemPathParameterTypes:
    """Test path parameter type handling."""

    def test_get_item_with_valid_integer(self):
        """Valid integer path parameter should work."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_with_leading_zeros(self):
        """Item ID with leading zeros should be parsed."""
        response = client.get("/items/001")
        # Should be parsed as 1
        assert response.status_code == 200

    def test_get_item_with_text_returns_422(self):
        """Text path parameter should return 422."""
        response = client.get("/items/abc")
        assert response.status_code == 422

    def test_get_item_with_float_in_path(self):
        """Float in path should return 422."""
        response = client.get("/items/1.5")
        assert response.status_code == 422

    def test_get_item_with_special_characters(self):
        """Special characters in path should return 422."""
        response = client.get("/items/@#$")
        assert response.status_code == 422


class TestCreateAndGetIntegration:
    """Test integration of create and get operations."""

    def test_create_item_then_get_succeeds(self):
        """Should be able to create and then get item 1."""
        # Create an item
        create_response = client.post("/items", json={"name": "widget", "price": 29.99})
        assert create_response.status_code == 200
        created_data = create_response.json()
        assert created_data["id"] == 1

        # Get the created item
        get_response = client.get(f"/items/{created_data['id']}")
        assert get_response.status_code == 200
        retrieved_data = get_response.json()
        assert retrieved_data["id"] == 1

    def test_create_item_get_another_id_fails(self):
        """Creating item 1 then getting item 2 should fail."""
        # Create item
        create_response = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_response.status_code == 200

        # Try to get different item
        get_response = client.get("/items/2")
        assert get_response.status_code == 404

    def test_multiple_create_requests_all_return_id_one(self):
        """Multiple creates should all return the same ID (mocked backend)."""
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_create_various_items_then_get(self):
        """Create various items and verify get still works for ID 1."""
        test_cases = [
            {"name": "book", "price": 12.99},
            {"name": "pen", "price": 1.50},
            {"name": "notebook", "price": 5.00},
        ]
        for case in test_cases:
            create_response = client.post("/items", json=case)
            assert create_response.status_code == 200

        # Get should still work
        get_response = client.get("/items/1")
        assert get_response.status_code == 200


class TestSequentialOperations:
    """Test sequential and repeated operations."""

    def test_get_nonexistent_then_create_then_get(self):
        """Sequence: get 404, create, get 200."""
        # Try to get non-existent
        r1 = client.get("/items/2")
        assert r1.status_code == 404

        # Create item
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

        # Get the created item
        r3 = client.get("/items/1")
        assert r3.status_code == 200

    def test_repeated_get_same_item(self):
        """Getting the same item multiple times should work."""
        for _ in range(5):
            response = client.get("/items/1")
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_repeated_create_requests(self):
        """Multiple creates should all succeed."""
        responses = []
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            responses.append(response)
            assert response.status_code == 200

        # All should have returned id=1
        for response in responses:
            assert response.json()["id"] == 1


class TestItemPriceEdgeCasesIntegration:
    """Test price edge cases in realistic scenarios."""

    def test_create_with_minimum_valid_price(self):
        """Create with smallest valid positive price."""
        response = client.post("/items", json={"name": "tiny", "price": 0.01})
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_create_with_maximum_price(self):
        """Create with very large price."""
        response = client.post("/items", json={"name": "expensive", "price": 1e10})
        assert response.status_code == 200
        assert response.json()["price"] == 1e10

    def test_create_multiple_prices_all_positive(self):
        """Create multiple items with various positive prices."""
        prices = [0.01, 1.0, 10.99, 100.00, 999.99]
        for price in prices:
            response = client.post("/items", json={"name": "item", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_price_boundary_just_below_zero_rejected(self):
        """Prices just below or at 0 should be rejected."""
        for price in [-0.01, 0]:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 400

    def test_price_boundary_just_above_zero_accepted(self):
        """Prices just above 0 should be accepted."""
        response = client.post("/items", json={"name": "test", "price": 0.01})
        assert response.status_code == 200


class TestItemNameEdgeCasesIntegration:
    """Test name edge cases in realistic scenarios."""

    def test_create_with_minimal_name(self):
        """Create with single character name."""
        response = client.post("/items", json={"name": "a", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "a"

    def test_create_with_empty_name(self):
        """Create with empty name (should work)."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == ""

    def test_create_with_very_long_name(self):
        """Create with extremely long name."""
        long_name = "x" * 5000
        response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_with_various_character_types(self):
        """Create with different character types in name."""
        names = [
            "Simple",
            "with spaces",
            "with-dashes",
            "with_underscores",
            "with.dots",
            "with!@#$%",
            "123numbers",
            "UPPERCASE",
            "mixedCase",
        ]
        for name in names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            assert response.status_code == 200
            assert response.json()["name"] == name


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_create_with_invalid_price_then_valid_price(self):
        """After rejecting invalid price, valid price should work."""
        # Invalid
        r1 = client.post("/items", json={"name": "test", "price": -1})
        assert r1.status_code == 400

        # Valid
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_create_with_missing_field_then_valid(self):
        """After validation error, valid request should work."""
        # Invalid - missing price
        r1 = client.post("/items", json={"name": "test"})
        assert r1.status_code == 422

        # Valid
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_get_invalid_id_then_valid_id(self):
        """After 404, valid ID should work."""
        # 404
        r1 = client.get("/items/999")
        assert r1.status_code == 404

        # Valid
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestConsistentBehavior:
    """Test consistent behavior across requests."""

    def test_get_item_1_always_returns_same_data(self):
        """Getting item 1 multiple times returns same data."""
        responses = [client.get("/items/1") for _ in range(3)]
        assert len(responses) == 3
        data_list = [r.json() for r in responses]

        # All should be identical
        assert data_list[0] == data_list[1] == data_list[2]
        assert data_list[0]["id"] == 1
        assert data_list[0]["name"] == "sample"
        assert data_list[0]["price"] == 10.0

    def test_create_returns_consistent_structure(self):
        """Multiple creates return same structure."""
        responses = [
            client.post("/items", json={"name": "item1", "price": 10.0}),
            client.post("/items", json={"name": "item2", "price": 20.0}),
        ]

        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert set(data.keys()) == {"id", "name", "price"}
            assert data["id"] == 1

    def test_error_responses_consistent(self):
        """Error responses have consistent structure."""
        # 404 errors
        r1 = client.get("/items/2")
        r2 = client.get("/items/100")

        assert r1.status_code == r2.status_code == 404
        assert r1.json() == r2.json()

        # 400 errors
        r3 = client.post("/items", json={"name": "test", "price": -1})
        r4 = client.post("/items", json={"name": "test", "price": -100})

        assert r3.status_code == r4.status_code == 400
        assert r3.json()["detail"] == r4.json()["detail"]
