"""
Test suite for edge cases and integration scenarios.
Focuses on boundary values, error condition sequences, and endpoint interactions.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryIds:
    """Tests for get_item with boundary item_id values."""

    def test_get_item_with_id_one(self):
        """Test get_item with id=1 (valid item)."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_with_id_zero(self):
        """Test get_item with id=0 (should not exist)."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_with_negative_id(self):
        """Test get_item with negative id."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_with_large_negative_id(self):
        """Test get_item with large negative id."""
        r = client.get("/items/-999999")
        assert r.status_code == 404

    def test_get_item_with_id_two(self):
        """Test get_item with id=2 (should not exist)."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_with_large_id(self):
        """Test get_item with very large id."""
        r = client.get("/items/999999")
        assert r.status_code == 404

    def test_get_item_with_max_int_id(self):
        """Test get_item with max integer id."""
        r = client.get(f"/items/{2**31-1}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000])
    def test_get_item_various_non_existent_ids(self, item_id):
        """Test get_item with various non-existent ids."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemBoundaryBehavior:
    """Tests for get_item boundary behavior."""

    def test_get_item_only_accepts_id_one(self):
        """Test get_item only successfully returns for id=1."""
        valid_r = client.get("/items/1")
        invalid_r = client.get("/items/2")
        assert valid_r.status_code == 200
        assert invalid_r.status_code == 404

    def test_get_item_one_always_succeeds(self):
        """Test get_item/1 always returns successfully."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_get_item_other_ids_always_fail(self):
        """Test get_item fails for any id != 1."""
        for item_id in [0, 2, 3, -1, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestCreateItemIntegrationSequences:
    """Tests for sequences of create_item calls."""

    def test_create_multiple_items_all_return_id_one(self):
        """Test multiple create_item calls all return id=1."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_items_with_increasing_prices(self):
        """Test creating items with increasing prices."""
        prices = [1.0, 2.0, 5.0, 10.0, 100.0]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_create_items_with_varied_names(self):
        """Test creating items with different names."""
        names = ["apple", "book", "car", "door", "egg"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_valid_then_invalid(self):
        """Test creating valid item then invalid item."""
        # Valid
        r1 = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r1.status_code == 200

        # Invalid
        r2 = client.post("/items", json={"name": "invalid", "price": 0})
        assert r2.status_code == 400

    def test_create_invalid_then_valid(self):
        """Test creating invalid item then valid item."""
        # Invalid
        r1 = client.post("/items", json={"name": "invalid", "price": -5})
        assert r1.status_code == 400

        # Valid
        r2 = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r2.status_code == 200

    def test_create_multiple_invalid_attempts(self):
        """Test multiple invalid create attempts."""
        invalid_payloads = [
            {"name": "test", "price": 0},
            {"name": "test", "price": -1},
            {"price": 10.0},
        ]
        for payload in invalid_payloads:
            r = client.post("/items", json=payload)
            assert r.status_code in [400, 422]


class TestEndpointInteractions:
    """Tests for interactions between different endpoints."""

    def test_health_never_interferes_with_items(self):
        """Test health endpoint doesn't affect items endpoints."""
        client.get("/health")
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_items_after_health(self):
        """Test items endpoints work after health check."""
        client.get("/health")
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_get_item_after_create(self):
        """Test get_item works after create_item."""
        # Create
        client.post("/items", json={"name": "test", "price": 10.0})
        # Get
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_multiple_endpoint_sequence(self):
        """Test sequence of multiple endpoints."""
        # Health
        r1 = client.get("/health")
        assert r1.status_code == 200

        # Create
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

        # Get
        r3 = client.get("/items/1")
        assert r3.status_code == 200

        # Health again
        r4 = client.get("/health")
        assert r4.status_code == 200

    def test_create_get_then_invalid_get(self):
        """Test create, get valid, get invalid."""
        # Create
        client.post("/items", json={"name": "test", "price": 10.0})

        # Get valid
        r1 = client.get("/items/1")
        assert r1.status_code == 200

        # Get invalid
        r2 = client.get("/items/2")
        assert r2.status_code == 404


class TestErrorHandlingEdgeCases:
    """Tests for edge cases in error handling."""

    def test_price_exactly_at_boundary(self):
        """Test price exactly at validation boundary (0)."""
        r = client.post("/items", json={"name": "boundary", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_price_just_above_boundary(self):
        """Test price just above validation boundary."""
        r = client.post("/items", json={"name": "boundary", "price": 0.00001})
        assert r.status_code == 200

    def test_price_just_below_boundary(self):
        """Test price just below validation boundary."""
        r = client.post("/items", json={"name": "boundary", "price": -0.00001})
        assert r.status_code == 400

    def test_item_id_exactly_at_boundary(self):
        """Test item_id exactly at valid boundary (1)."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_item_id_just_above_valid_range(self):
        """Test item_id just above valid range."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_item_id_just_below_valid_range(self):
        """Test item_id just below valid range."""
        r = client.get("/items/0")
        assert r.status_code == 404


class TestInputCombinations:
    """Tests for various input combinations."""

    @pytest.mark.parametrize("name,price", [
        ("a", 0.01),
        ("very long name here", 999.99),
        ("123", 1.0),
        ("test-item", 50.0),
        ("item with spaces", 25.5),
    ])
    def test_various_name_price_combinations(self, name, price):
        """Test various combinations of name and price."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price

    @pytest.mark.parametrize("price", [0, -1, -0.01, -100])
    def test_invalid_prices_all_fail(self, price):
        """Test all invalid prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    @pytest.mark.parametrize("item_id", [0, -1, 2, 100, -999])
    def test_invalid_item_ids_all_fail(self, item_id):
        """Test all invalid ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestConsecutiveOperations:
    """Tests for consecutive operations of same type."""

    def test_consecutive_health_checks(self):
        """Test multiple consecutive health checks."""
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"

    def test_consecutive_get_item_one(self):
        """Test multiple consecutive get_item/1 calls."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_consecutive_get_item_invalid(self):
        """Test multiple consecutive get_item with invalid id."""
        for i in range(10):
            r = client.get(f"/items/{i+2}")
            assert r.status_code == 404

    def test_consecutive_create_items(self):
        """Test multiple consecutive create_item calls."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_consecutive_invalid_creates(self):
        """Test multiple consecutive invalid create_item calls."""
        for i in range(5):
            r = client.post("/items", json={"name": f"bad{i}", "price": -i-1})
            assert r.status_code == 400


class TestStatusCodeConsistency:
    """Tests for consistent HTTP status codes."""

    def test_success_status_is_200(self):
        """Test successful requests return 200."""
        r1 = client.get("/health")
        r2 = client.get("/items/1")
        r3 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 200

    def test_not_found_status_is_404(self):
        """Test not found responses return 404."""
        r1 = client.get("/items/2")
        r2 = client.get("/items/0")
        r3 = client.get("/items/-1")
        assert r1.status_code == 404
        assert r2.status_code == 404
        assert r3.status_code == 404

    def test_validation_error_status_is_400(self):
        """Test validation errors return 400."""
        r1 = client.post("/items", json={"name": "test", "price": 0})
        r2 = client.post("/items", json={"name": "test", "price": -5})
        assert r1.status_code == 400
        assert r2.status_code == 400

    def test_malformed_request_status_is_422(self):
        """Test malformed requests return 422."""
        r1 = client.post("/items", json={"price": 10.0})
        r2 = client.post("/items", json={"name": "test"})
        r3 = client.post("/items", json={})
        assert r1.status_code == 422
        assert r2.status_code == 422
        assert r3.status_code == 422


class TestResponseDataAccuracy:
    """Tests for accuracy of response data."""

    def test_create_response_echoes_name(self):
        """Test create_item response echoes provided name."""
        names = ["alice", "bob", "charlie"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.json()["name"] == name

    def test_create_response_echoes_price(self):
        """Test create_item response echoes provided price."""
        prices = [1.5, 10.0, 99.99, 0.01]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.json()["price"] == price

    def test_create_response_always_id_one(self):
        """Test create_item response always has id=1."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert r.json()["id"] == 1

    def test_get_item_one_always_same(self):
        """Test get_item/1 always returns same data."""
        first_r = client.get("/items/1")
        first_data = first_r.json()
        for _ in range(5):
            r = client.get("/items/1")
            assert r.json() == first_data
