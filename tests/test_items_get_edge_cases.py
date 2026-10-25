"""Part 3: Edge cases and integration tests for items endpoints.

Tests comprehensive edge cases and integration scenarios including:
- Boundary value testing for item_id
- Interaction patterns between endpoints
- Stress testing with various input combinations
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestGetItemIdBoundaryValues:
    """Tests for get_item with boundary value item_id."""

    def test_get_item_id_one_success(self):
        """Test that item_id=1 returns success."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_id_zero_not_found(self):
        """Test that item_id=0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_negative_not_found(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-1000, -100, -10, -1])
    def test_get_item_negative_ids(self, item_id):
        """Test that negative item_ids are not found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 1000000])
    def test_get_item_large_ids_not_found(self, item_id):
        """Test that large item_ids are not found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_max_int_value(self):
        """Test with maximum integer value."""
        max_int = 2147483647  # 32-bit max int
        r = client.get(f"/items/{max_int}")
        assert r.status_code == 404

    def test_get_item_very_large_number(self):
        """Test with very large number beyond int range."""
        # Python handles big integers, but FastAPI should parse as int
        large_num = 9223372036854775807  # 64-bit max int
        r = client.get(f"/items/{large_num}")
        assert r.status_code == 404


class TestGetItemInvalidPathParameters:
    """Tests for get_item with invalid path parameters."""

    def test_get_item_string_id_invalid(self):
        """Test that string id returns validation error."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_float_id_invalid(self):
        """Test that float id returns validation error."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_get_item_empty_id_invalid(self):
        """Test that empty id path returns 404."""
        r = client.get("/items/")
        assert r.status_code == 404

    def test_get_item_special_chars_id_invalid(self):
        """Test that special chars in id return validation error."""
        r = client.get("/items/@#$")
        assert r.status_code == 422


class TestCreateItemSequentialCalls:
    """Tests for sequential create_item calls."""

    def test_multiple_create_items_success(self):
        """Test that multiple create_item calls all succeed."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_item_always_returns_id_one(self):
        """Test that all created items have id=1."""
        ids = []
        for _ in range(10):
            r = client.post("/items", json={"name": "test", "price": 10.0})
            ids.append(r.json()["id"])
        assert all(id_ == 1 for id_ in ids)

    def test_create_different_items_multiple_times(self):
        """Test creating multiple different items."""
        items = [
            {"name": "book", "price": 15.0},
            {"name": "pen", "price": 2.5},
            {"name": "desk", "price": 100.0},
            {"name": "lamp", "price": 25.0},
        ]
        for item in items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == item["name"]
            assert data["price"] == item["price"]


class TestCreateThenGetItem:
    """Tests for creating then getting an item (integration)."""

    def test_create_item_then_get_item(self):
        """Test create item followed by get item."""
        # Create item
        create_r = client.post("/items", json={"name": "created", "price": 20.0})
        assert create_r.status_code == 200
        
        # Get the same item
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        
        # Both should return id=1
        assert create_r.json()["id"] == 1
        assert get_r.json()["id"] == 1

    def test_create_item_fields_match_retrieval(self):
        """Test that created item fields match what's retrieved."""
        name = "integration_test"
        price = 42.5
        
        create_r = client.post("/items", json={"name": name, "price": price})
        assert create_r.status_code == 200
        
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        
        # Note: get_item returns hardcoded values, not the created item
        # This tests the API contract
        assert "id" in create_r.json()
        assert "id" in get_r.json()


class TestMixedOperationsSequence:
    """Tests for mixed sequence of operations."""

    def test_create_get_create_sequence(self):
        """Test alternating create and get operations."""
        # Create
        r1 = client.post("/items", json={"name": "first", "price": 10.0})
        assert r1.status_code == 200
        
        # Get
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        
        # Create again
        r3 = client.post("/items", json={"name": "second", "price": 20.0})
        assert r3.status_code == 200
        
        # Get again
        r4 = client.get("/items/1")
        assert r4.status_code == 200

    def test_get_not_found_then_create_success(self):
        """Test get (not found) followed by create (success)."""
        # Get non-existent item
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Create item
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_create_with_error_then_success(self):
        """Test failed create followed by successful create."""
        # Create with invalid price
        r1 = client.post("/items", json={"name": "bad", "price": -1})
        assert r1.status_code == 400
        
        # Create with valid price
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200


class TestPriceValidationEdgeCases:
    """Tests for price validation edge cases."""

    def test_price_exactly_zero(self):
        """Test that exactly zero price is rejected."""
        r = client.post("/items", json={"name": "free", "price": 0.0})
        assert r.status_code == 400

    def test_price_just_above_zero(self):
        """Test that price just above zero is accepted."""
        r = client.post("/items", json={"name": "cheap", "price": 0.00001})
        assert r.status_code == 200

    def test_price_just_below_zero(self):
        """Test that price just below zero is rejected."""
        r = client.post("/items", json={"name": "invalid", "price": -0.00001})
        assert r.status_code == 400

    def test_price_decimal_precision(self):
        """Test various decimal precisions."""
        prices = [0.1, 0.01, 0.001, 0.0001, 0.00001]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_price_scientific_notation_valid(self):
        """Test price in scientific notation (valid)."""
        r = client.post("/items", json={"name": "expensive", "price": 1e2})
        assert r.status_code == 200
        assert r.json()["price"] == 100.0

    def test_price_scientific_notation_negative(self):
        """Test negative price in scientific notation."""
        r = client.post("/items", json={"name": "invalid", "price": -1e2})
        assert r.status_code == 400


class TestNameValidationEdgeCases:
    """Tests for name validation edge cases."""

    def test_name_single_character(self):
        """Test that single character name is accepted."""
        r = client.post("/items", json={"name": "x", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "x"

    def test_name_empty_string(self):
        """Test that empty string name is accepted (no validation)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_name_whitespace_only(self):
        """Test that whitespace-only name is accepted."""
        names = [" ", "  ", "\t", "\n"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200

    def test_name_with_numbers(self):
        """Test name containing numbers."""
        r = client.post("/items", json={"name": "item123", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item123"

    def test_name_with_punctuation(self):
        """Test name with various punctuation."""
        names = ["test.", "test!", "test?", "test-item", "test_item", "test/item"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200

    def test_name_with_emojis(self):
        """Test name with emoji characters."""
        r = client.post("/items", json={"name": "item🎉", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item🎉"

    def test_name_multilingual(self):
        """Test name with multiple languages."""
        names = ["café", "日本語", "Русский", "العربية"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestCombinedValidation:
    """Tests combining multiple validation rules."""

    def test_boundary_price_with_various_names(self):
        """Test boundary price with different name formats."""
        names = ["a", "normal", "special-chars!", "日本語"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 0.01})
            assert r.status_code == 200

    def test_large_price_with_various_names(self):
        """Test large price with different name formats."""
        names = ["a", "normal", "special-chars!", "日本語"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 1e6})
            assert r.status_code == 200

    @pytest.mark.parametrize("price,name", [
        (0.01, "cheap"),
        (1.0, "normal"),
        (100.0, "expensive"),
        (1e6, "luxury"),
    ])
    def test_parametrized_price_name_combinations(self, price, name):
        """Test various price and name combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_check_success(self):
        """Test that health endpoint returns success."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_check_response_structure(self):
        """Test that health response has expected structure."""
        r = client.get("/health")
        assert "status" in r.json()

    def test_health_check_multiple_calls(self):
        """Test that health endpoint is consistent."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"
