"""Edge cases and integration testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter edge cases for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [
        0,
        -1,
        -999,
        2,
        3,
        100,
        999999,
    ])
    def test_various_item_ids_not_found(self, item_id):
        """Only item_id=1 should exist, others return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_item_id_1_found(self):
        """Item with id=1 should exist."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestCreateItemWithVariousPrices:
    """Test create item with diverse price values."""

    @pytest.mark.parametrize("price,name", [
        (0.01, "cheap"),
        (1.0, "standard"),
        (10.0, "premium"),
        (99.99, "luxury"),
        (999.99, "ultra"),
        (1.50, "special"),
        (19.95, "discounted"),
        (100.0, "expensive"),
        (0.001, "minimal"),
    ])
    def test_various_valid_prices(self, price, name):
        """Create item with various valid prices."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["name"] == name


class TestCreateItemWithVariousNames:
    """Test create item with diverse name values."""

    @pytest.mark.parametrize("name", [
        "Item",
        "Product 123",
        "book-cover",
        "café_menu",
        "日本語",
        "emoji_🎉_test",
        "UPPERCASE",
        "lowercase",
        "MixedCase",
    ])
    def test_various_name_values(self, name):
        """Create item with various name formats."""
        r = client.post("/items", json={"name": name, "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name


class TestPriceEdgeCases:
    """Test price field edge cases and boundaries."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.001, True),
        (0.0001, True),
        (0.00001, True),
        (0.0, False),
        (-0.0, False),
        (1e-10, True),
        (1e-100, True),
    ])
    def test_very_small_prices(self, price, should_succeed):
        """Test behavior with very small price values."""
        r = client.post("/items", json={"name": "test", "price": price})
        if should_succeed:
            assert r.status_code == 200
        else:
            assert r.status_code == 400


class TestNameFieldEdgeCases:
    """Test name field edge cases."""

    def test_name_with_numbers_only(self):
        """Name with only numbers should be accepted."""
        r = client.post("/items", json={"name": "12345", "price": 5.0})
        assert r.status_code == 200

    def test_name_with_special_chars(self):
        """Name with special characters should be accepted."""
        r = client.post("/items", json={"name": "!@#$%^&*()", "price": 5.0})
        assert r.status_code == 200

    def test_name_with_newlines(self):
        """Name with newlines should be accepted."""
        r = client.post("/items", json={"name": "line1\nline2", "price": 5.0})
        assert r.status_code == 200

    def test_very_long_name(self):
        """Very long name should be accepted."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 5.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 1000


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple operations."""

    def test_create_then_verify_response(self):
        """Create item and verify all response fields."""
        create_resp = client.post("/items", json={"name": "test-item", "price": 25.50})
        assert create_resp.status_code == 200
        
        data = create_resp.json()
        assert data["id"] == 1
        assert data["name"] == "test-item"
        assert data["price"] == 25.50
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_invalid_then_valid_creation(self):
        """Test creating with invalid then valid data."""
        # Invalid: zero price
        invalid = client.post("/items", json={"name": "test", "price": 0})
        assert invalid.status_code == 400
        
        # Valid: positive price
        valid = client.post("/items", json={"name": "test", "price": 10.0})
        assert valid.status_code == 200
        assert valid.json()["price"] == 10.0

    def test_multiple_validation_failures(self):
        """Test multiple types of validation failures."""
        # Missing both fields
        r1 = client.post("/items", json={})
        assert r1.status_code == 422
        
        # Missing name
        r2 = client.post("/items", json={"price": 10.0})
        assert r2.status_code == 422
        
        # Missing price
        r3 = client.post("/items", json={"name": "test"})
        assert r3.status_code == 422
        
        # Wrong type for price
        r4 = client.post("/items", json={"name": "test", "price": "ten"})
        assert r4.status_code == 422


class TestHealthCheckReliability:
    """Test health check endpoint reliability."""

    def test_multiple_health_checks(self):
        """Health check should work consistently."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}

    def test_health_check_response_format(self):
        """Health response format should be consistent."""
        r = client.get("/health")
        data = r.json()
        assert len(data) == 1
        assert "status" in data
        assert data["status"] == "ok"


class TestBoundaryConditions:
    """Test boundary conditions across endpoints."""

    def test_max_integer_item_id(self):
        """Test with maximum integer as item_id."""
        import sys
        r = client.get(f"/items/{sys.maxsize}")
        assert r.status_code == 404

    def test_float_conversion_in_price(self):
        """Test float to int conversion edge cases."""
        # Integer that fits as float
        r = client.post("/items", json={"name": "test", "price": 100})
        assert r.status_code == 200
        assert r.json()["price"] == 100

    def test_scientific_notation_prices(self):
        """Test scientific notation in prices."""
        r = client.post("/items", json={"name": "test", "price": 1e2})
        assert r.status_code == 200
        assert r.json()["price"] == 100.0
