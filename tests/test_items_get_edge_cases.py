import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    def test_get_item_with_id_1(self):
        """Test that item ID 1 returns found."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_with_id_0(self):
        """Test that item ID 0 returns not found."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_with_id_minus_1(self):
        """Test that negative ID returns not found."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 1000])
    def test_get_item_with_ids_not_1(self, item_id):
        """Test that various IDs other than 1 return not found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_very_large_id(self):
        """Test with very large ID."""
        r = client.get(f"/items/{10**10}")
        assert r.status_code == 404

    def test_get_item_boundary_id_zero(self):
        """Test boundary at ID 0."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_boundary_id_two(self):
        """Test boundary at ID 2."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_correct_response_for_id_1(self):
        """Test that ID 1 returns correct item data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_same_item_returned_consistently(self):
        """Test that item ID 1 returns the same data on multiple calls."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()


class TestCreateItemWithVariousPrices:
    """Test create_item with various price edge cases."""

    @pytest.mark.parametrize("price", [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0])
    def test_create_item_with_increasing_prices(self, price):
        """Test creation with prices on different scales."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [-1000, -100, -10, -1, -0.1, -0.01, -0.001])
    def test_create_item_rejects_all_negative_prices(self, price):
        """Test that all negative prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    def test_create_item_price_precision_small(self):
        """Test very small price precision."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0001

    def test_create_item_price_precision_large(self):
        """Test large price with decimal precision."""
        r = client.post("/items", json={"name": "item", "price": 123456.789})
        assert r.status_code == 200
        assert r.json()["price"] == 123456.789

    def test_create_item_price_scientific_notation(self):
        """Test price in scientific notation."""
        r = client.post("/items", json={"name": "item", "price": 1e2})
        assert r.status_code == 200
        assert r.json()["price"] == 100.0

    def test_create_item_price_scientific_negative_exponent(self):
        """Test price with negative exponent."""
        r = client.post("/items", json={"name": "item", "price": 1e-2})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01


class TestCreateItemWithVariousNames:
    """Test create_item with various name edge cases."""

    @pytest.mark.parametrize("name", ["a", "ab", "abc", "test", "long name here"])
    def test_create_item_with_varying_name_lengths(self, name):
        """Test creation with names of different lengths."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_100_char_name(self):
        """Test creation with 100 character name."""
        name = "x" * 100
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_1000_char_name(self):
        """Test creation with 1000 character name."""
        name = "y" * 1000
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 1000

    @pytest.mark.parametrize("name", ["name!", "name@", "name#", "name$", "name%"])
    def test_create_item_with_special_char_names(self, name):
        """Test creation with special characters in names."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", ["name\n", "name\t", "name\r"])
    def test_create_item_with_whitespace_names(self, name):
        """Test creation with whitespace characters in names."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200

    def test_create_item_preserves_exact_name(self):
        """Test that exact name is preserved including case."""
        name = "Test Name With Mixed CASE"
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_preserves_multiple_spaces(self):
        """Test that multiple spaces in name are preserved."""
        name = "item  with   multiple    spaces"
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemResponseConsistency:
    """Test consistency of create_item responses."""

    def test_create_item_id_always_one(self):
        """Test that all successful creates return ID 1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_item_response_has_three_fields_only(self):
        """Test that response has exactly id, name, price (no extra fields)."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_name_field_always_matches_input(self):
        """Test that name field always matches input."""
        test_names = ["book", "pen", "notebook", "special!@#$"]
        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 10})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_price_field_always_matches_input(self):
        """Test that price field always matches input."""
        test_prices = [1.0, 5.5, 10.99, 100.001]
        for price in test_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestGetItemResponseConsistency:
    """Test consistency of get_item responses."""

    def test_get_item_always_returns_same_id(self):
        """Test that get_item/1 always returns id 1."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_get_item_always_returns_same_name(self):
        """Test that get_item/1 always returns the same name."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json()["name"] == r2.json()["name"] == "sample"

    def test_get_item_always_returns_same_price(self):
        """Test that get_item/1 always returns the same price."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json()["price"] == r2.json()["price"] == 10.0

    def test_get_item_response_has_three_fields_only(self):
        """Test that response has exactly id, name, price (no extra fields)."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_not_found_has_only_detail_field(self):
        """Test that 404 response has only detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert set(data.keys()) == {"detail"}


class TestHealthEndpoint:
    """Test health endpoint behavior."""

    def test_health_endpoint_returns_ok_status(self):
        """Test that health endpoint returns 'ok' status."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_endpoint_consistent(self):
        """Test that health endpoint is consistent across calls."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"

    def test_health_endpoint_has_only_status_field(self):
        """Test that health response has only status field."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"status"}


class TestIntegrationScenarios:
    """Test integration scenarios across multiple operations."""

    def test_create_and_get_different_names_dont_affect_item_1(self):
        """Test that creating items doesn't change item 1."""
        r1_before = client.get("/items/1")
        client.post("/items", json={"name": "new", "price": 20})
        r1_after = client.get("/items/1")
        assert r1_before.json() == r1_after.json()

    def test_create_multiple_items_all_return_id_1(self):
        """Test that multiple creations all return the same ID 1."""
        ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        assert all(id == 1 for id in ids)

    def test_health_works_after_create_operations(self):
        """Test that health endpoint works after create operations."""
        client.post("/items", json={"name": "test", "price": 10})
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_get_non_existent_doesnt_affect_health(self):
        """Test that trying to get non-existent items doesn't affect health."""
        client.get("/items/999")
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_sequential_operations_maintain_consistency(self):
        """Test that multiple sequential operations maintain consistency."""
        # Create several items
        for i in range(3):
            client.post("/items", json={"name": f"item{i}", "price": 10 + i})
        
        # Check that item 1 is still the same
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["name"] == "sample"
        assert r.json()["price"] == 10.0
        
        # Check that non-1 IDs still don't exist
        for item_id in [2, 3, 10]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_error_conditions_dont_break_api(self):
        """Test that error conditions don't break API."""
        # Try various error conditions
        client.post("/items", json={"name": "test", "price": 0})  # 400
        client.get("/items/999")  # 404
        client.post("/items", json={"name": "test"})  # 422
        
        # API should still work
        r = client.get("/items/1")
        assert r.status_code == 200
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        r = client.get("/health")
        assert r.status_code == 200


class TestEdgeCaseTypeConversion:
    """Test edge cases in type conversion and validation."""

    def test_create_item_string_float_with_leading_zeros(self):
        """Test string float with leading zeros."""
        r = client.post("/items", json={"name": "test", "price": "00010.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_string_float_with_plus_sign(self):
        """Test string float with plus sign."""
        r = client.post("/items", json={"name": "test", "price": "+10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_integer_name_type_coercion(self):
        """Test that integer names are properly coerced."""
        r = client.post("/items", json={"name": 42, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "42"

    def test_create_item_float_name_type_coercion(self):
        """Test that float names are properly coerced."""
        r = client.post("/items", json={"name": 3.14, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "3.14"
