"""
Edge case and integration testing for FastAPI item management endpoints.
Tests boundary values, path parameter validation, and multi-endpoint workflows.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id,should_be_found", [
        (1, True),
    ])
    def test_get_item_valid_id(self, item_id, should_be_found):
        """Test getting item with valid id."""
        r = client.get(f"/items/{item_id}")
        if should_be_found:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 0, -1, -100, 999, 10000])
    def test_get_item_invalid_ids(self, item_id):
        """Test that non-existent item ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (3, 404),
        (100, 404),
    ])
    def test_get_item_boundary_ids(self, item_id, expected_status):
        """Test item retrieval with boundary id values."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestPriceEdgeCases:
    """Test edge cases for price validation."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.001, True),
        (0.01, True),
        (0.1, True),
        (1, True),
        (10.5, True),
        (100.99, True),
        (1000, True),
        (10000, True),
        (0.0001, True),
        (0.00001, True),
    ])
    def test_create_item_small_prices(self, price, should_succeed):
        """Test creation with very small positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        if should_succeed:
            assert r.status_code == 200
            assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0, -0.00001, -0.001, -0.01, -1, -10, -100.99])
    def test_create_item_zero_or_negative_prices(self, price):
        """Test that zero and negative prices fail."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestNameEdgeCases:
    """Test edge cases for name field."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "a" * 10,
        "a" * 100,
        "a" * 500,
    ])
    def test_create_item_name_length_variations(self, name):
        """Test creation with various name lengths."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        " space_start",
        "space_end ",
        " both_spaces ",
        "  multiple  spaces  ",
        "	tab_char",
        "new\nline",
    ])
    def test_create_item_name_whitespace_handling(self, name):
        """Test name handling with whitespace characters."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "!@#$%^&*()",
        "{}[]|\\",
        "~`",
        "name;drop--table",
        "<script>alert('xss')</script>",
        "'; DROP TABLE items; --",
    ])
    def test_create_item_name_special_chars(self, name):
        """Test name with potentially dangerous characters."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "café",
        "naïve",
        "こんにちは",
        "مرحبا",
        "🎉😀🎊",
        "Ñoño",
    ])
    def test_create_item_name_unicode_chars(self, name):
        """Test name with unicode characters."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestTypeCoercionEdgeCases:
    """Test edge cases in type coercion and conversion."""

    @pytest.mark.parametrize("price_str,expected", [
        ("10", 10.0),
        ("10.0", 10.0),
        ("10.5", 10.5),
        ("0.1", 0.1),
        ("1e2", 100.0),
        ("1.5e1", 15.0),
    ])
    def test_create_item_price_string_conversion(self, price_str, expected):
        """Test valid string to float conversion for price."""
        r = client.post("/items", json={"name": "item", "price": price_str})
        assert r.status_code == 200
        assert r.json()["price"] == expected

    def test_create_item_name_integer_conversion(self):
        """Test that integer names are converted to strings."""
        r = client.post("/items", json={"name": 42, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "42"
        assert isinstance(r.json()["name"], str)

    def test_create_item_name_float_conversion(self):
        """Test that float names are converted to strings."""
        r = client.post("/items", json={"name": 3.14, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "3.14"

    def test_create_item_name_boolean_conversion(self):
        """Test that boolean names are converted."""
        r = client.post("/items", json={"name": True, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "True"


class TestMultipleOperationSequences:
    """Test sequences of operations to verify consistency."""

    def test_create_and_retrieve_same_item(self):
        """Test creating an item and retrieving it."""
        # Create
        r_create = client.post("/items", json={"name": "test_item", "price": 25.5})
        assert r_create.status_code == 200
        created = r_create.json()
        
        # Retrieve
        r_get = client.get(f"/items/{created['id']}")
        assert r_get.status_code == 200
        retrieved = r_get.json()
        
        # Item id should match
        assert created["id"] == retrieved["id"]
        assert retrieved["id"] == 1

    def test_multiple_create_operations_independent(self):
        """Test that multiple create operations work independently."""
        names = ["apple", "book", "pen"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_failed_create_followed_by_success(self):
        """Test that failed create doesn't affect next successful create."""
        # Fail
        r_fail = client.post("/items", json={"name": "item", "price": 0})
        assert r_fail.status_code == 400
        
        # Succeed
        r_success = client.post("/items", json={"name": "item", "price": 10.0})
        assert r_success.status_code == 200

    def test_get_nonexistent_then_existent(self):
        """Test getting non-existent item followed by existing item."""
        # Get non-existent
        r_not_found = client.get("/items/999")
        assert r_not_found.status_code == 404
        
        # Get existing
        r_found = client.get("/items/1")
        assert r_found.status_code == 200


class TestErrorConditionCombinations:
    """Test combinations of error conditions."""

    def test_missing_name_and_invalid_price(self):
        """Test request with both missing name and invalid price."""
        r = client.post("/items", json={"price": 0})
        # Should fail on missing name (422) not price validation
        assert r.status_code == 422

    def test_invalid_name_type_and_price(self):
        """Test request with invalid name type and valid price."""
        r = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert r.status_code == 422

    def test_valid_name_and_missing_price(self):
        """Test request with valid name but missing price."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422


class TestConcurrentOperationSimulation:
    """Simulate concurrent-like operations to test isolation."""

    def test_alternating_create_and_get(self):
        """Test alternating create and get operations."""
        # Get existing
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        # Create new
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        assert r2.status_code == 200
        
        # Get existing again (should be same)
        r3 = client.get("/items/1")
        assert r3.status_code == 200
        assert r1.json()["id"] == r3.json()["id"]

    def test_stress_multiple_creates(self):
        """Test many create operations in sequence."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i + 1)})
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == f"item_{i}"
            assert data["price"] == float(i + 1)

    def test_stress_multiple_gets_same_item(self):
        """Test many get operations for the same item."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1


class TestHealthEndpointIntegration:
    """Test health endpoint in context of other operations."""

    def test_health_before_and_after_create(self):
        """Test health endpoint before and after creating item."""
        # Health before
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        # Create
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200
        
        # Health after
        r3 = client.get("/health")
        assert r3.status_code == 200
        assert r1.json() == r3.json()

    def test_health_before_and_after_failed_create(self):
        """Test health endpoint before and after failed create."""
        # Health before
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        # Failed create
        r2 = client.post("/items", json={"name": "item", "price": 0})
        assert r2.status_code == 400
        
        # Health after (should be unaffected)
        r3 = client.get("/health")
        assert r3.status_code == 200
        assert r1.json() == r3.json()

    def test_health_endpoint_isolation(self):
        """Test that health endpoint is isolated from other operations."""
        for _ in range(5):
            # Create
            client.post("/items", json={"name": "item", "price": 10.0})
            
            # Health (should always be ok)
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}


class TestBoundaryAndExtremValues:
    """Test with extreme and boundary values."""

    def test_very_large_price(self):
        """Test with very large price value."""
        r = client.post("/items", json={"name": "item", "price": 999999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999999.99

    def test_very_small_positive_price(self):
        """Test with very small but positive price."""
        r = client.post("/items", json={"name": "item", "price": 0.000001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.000001

    def test_very_long_name(self):
        """Test with very long name."""
        long_name = "x" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    @pytest.mark.parametrize("item_id", [0, -1, -999999, 1, 2, 999999])
    def test_get_item_extreme_ids(self, item_id):
        """Test get_item with extreme item id values."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404
