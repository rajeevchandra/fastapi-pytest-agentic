from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Test path parameter edge cases for get_item endpoint."""

    def test_get_item_with_very_large_id(self):
        """Verify very large item IDs are handled."""
        r = client.get("/items/999999999999")
        assert r.status_code == 404

    def test_get_item_with_max_int(self):
        """Verify maximum integer value is handled."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_get_item_negative_values(self):
        """Verify negative item IDs return 404."""
        for item_id in [-1, -10, -100, -999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    def test_get_item_zero_id(self):
        """Verify item ID 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1, 2, 3, 10, 100, 1000])
    def test_only_id_1_succeeds(self, item_id):
        """Verify only ID 1 returns success."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestItemCreationAndRetrieval:
    """Test integrated item creation and retrieval workflows."""

    def test_create_then_retrieve_item(self):
        """Verify created item can be retrieved (integration test)."""
        # Create item
        create_r = client.post("/items", json={"name": "test_book", "price": 15.99})
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Retrieve it back (note: implementation always returns same item)
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify ID matches
        assert retrieved["id"] == created["id"]

    def test_multiple_creations_use_same_id(self):
        """Verify multiple creations return same ID (current implementation)."""
        ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        
        # All should be ID 1 (hardcoded)
        assert all(id == 1 for id in ids)

    def test_create_various_items(self):
        """Test creating items with various data."""
        test_items = [
            {"name": "Apple", "price": 0.99},
            {"name": "Book", "price": 19.99},
            {"name": "Computer", "price": 999.99},
            {"name": "Single Item", "price": 0.01},
        ]
        
        for item in test_items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == item["name"]
            assert data["price"] == item["price"]


class TestCreateItemDecimalPrices:
    """Test decimal and floating point price handling."""

    @pytest.mark.parametrize("price", [
        0.01, 0.1, 0.5, 0.99,
        1.00, 1.01, 1.99,
        10.0, 10.5, 10.99,
        99.99, 100.00, 999.99,
    ])
    def test_various_decimal_prices(self, price):
        """Verify various decimal prices are accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_price_precision_maintained(self):
        """Verify price decimal precision is maintained."""
        price = 19.95
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        returned_price = r.json()["price"]
        # Check precision is maintained
        assert abs(returned_price - price) < 0.0001

    def test_price_rounding_edge_cases(self):
        """Verify edge cases for decimal rounding."""
        test_prices = [0.001, 0.009, 0.015, 0.099, 0.999]
        for price in test_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_very_small_positive_price(self):
        """Verify very small but positive prices are accepted."""
        prices = [0.00001, 0.000001, 0.0000001]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200

    def test_integer_prices(self):
        """Verify integer prices work correctly."""
        for price in [1, 10, 100, 1000]:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestItemNameEdgeCases:
    """Test name field edge cases and special characters."""

    @pytest.mark.parametrize("name", [
        "a", "ab", "abc",  # short names
        "item-with-dashes", "item_with_underscores",  # special chars
        "item (with) parentheses", "item/with/slashes",  # more special chars
        "123", "item123", "123item",  # numbers
    ])
    def test_various_name_formats(self, name):
        """Verify various name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_name_with_multiple_spaces(self):
        """Verify names with multiple spaces are preserved."""
        name = "item    with    spaces"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_name_with_tabs_and_newlines(self):
        """Verify names with tabs and newlines are accepted."""
        name = "item\twith\ttabs\nand\nnewlines"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_very_long_name(self):
        """Verify very long names are accepted."""
        name = "x" * 1000
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("unicode_name", [
        "café",
        "naïve",
        "résumé",
        "日本語",
        "中文",
        "한국어",
        "العربية",
        "emoji_😀_test",
    ])
    def test_unicode_names(self, unicode_name):
        """Verify unicode names are handled correctly."""
        r = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == unicode_name


class TestCreateItemRequestPayloadVariations:
    """Test various request payload formats and edge cases."""

    def test_create_with_float_id_in_path(self):
        """Verify that float in path parameter is handled."""
        # This tests how the API handles type coercion
        r = client.get("/items/1.5")
        # FastAPI may reject this or convert it
        assert r.status_code in [200, 404, 422]

    def test_create_with_string_in_price_field(self):
        """Verify string prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": "10.0"})
        assert r.status_code == 422

    def test_create_with_boolean_in_price(self):
        """Verify boolean values in price field are handled."""
        r = client.post("/items", json={"name": "test", "price": True})
        # In Python, True == 1, so this might be accepted
        assert r.status_code in [200, 422]

    def test_create_with_list_in_name(self):
        """Verify list in name field is rejected."""
        r = client.post("/items", json={"name": ["item1", "item2"], "price": 10.0})
        assert r.status_code == 422

    def test_create_with_dict_in_name(self):
        """Verify dict in name field is rejected."""
        r = client.post("/items", json={"name": {"nested": "value"}, "price": 10.0})
        assert r.status_code == 422

    def test_empty_json_body(self):
        """Verify empty JSON body is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_json_with_extra_nested_fields(self):
        """Verify extra nested fields are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "metadata": {"key": "value"}
        })
        assert r.status_code == 200

    def test_json_array_instead_of_object(self):
        """Verify JSON array is rejected."""
        r = client.post("/items", content='["item", 10.0]')
        assert r.status_code == 422


class TestPriceValidationBoundaries:
    """Test precise boundary conditions for price validation."""

    def test_price_exactly_zero_rejected(self):
        """Verify price = 0.0 is rejected."""
        r = client.post("/items", json={"name": "test", "price": 0.0})
        assert r.status_code == 400

    def test_price_just_above_zero_accepted(self):
        """Verify price just above 0 is accepted."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200

    def test_price_negative_zero_rejected(self):
        """Verify negative zero is rejected."""
        r = client.post("/items", json={"name": "test", "price": -0.0})
        assert r.status_code == 400

    @pytest.mark.parametrize("price", [-0.0001, -0.001, -0.01, -0.1, -1.0])
    def test_small_negative_prices_rejected(self, price):
        """Verify small negative prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    def test_price_comparison_uses_greater_than(self):
        """Verify comparison is > not >=."""
        # Price must be > 0, so 0 is rejected but any positive is accepted
        r_zero = client.post("/items", json={"name": "test", "price": 0})
        assert r_zero.status_code == 400
        
        r_positive = client.post("/items", json={"name": "test", "price": 0.0000001})
        assert r_positive.status_code == 200


class TestEndpointIntegration:
    """Test interactions between different endpoints."""

    def test_create_and_health_dont_interfere(self):
        """Verify create and health endpoints don't interfere."""
        h1 = client.get("/health")
        c1 = client.post("/items", json={"name": "test", "price": 10.0})
        h2 = client.get("/health")
        
        assert h1.status_code == 200
        assert c1.status_code == 200
        assert h2.status_code == 200
        assert h1.json() == h2.json()

    def test_get_and_create_dont_interfere(self):
        """Verify get and create endpoints don't interfere."""
        g1 = client.get("/items/1")
        c1 = client.post("/items", json={"name": "test", "price": 10.0})
        g2 = client.get("/items/1")
        
        assert g1.status_code == 200
        assert c1.status_code == 200
        assert g2.status_code == 200
        assert g1.json() == g2.json()

    def test_multiple_invalid_creates_then_valid(self):
        """Verify invalid creates don't affect subsequent valid creates."""
        # Multiple failed creates
        for _ in range(3):
            r = client.post("/items", json={"name": "test", "price": 0})
            assert r.status_code == 400
        
        # Should still be able to create valid item
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_multiple_sequential_operations(self):
        """Verify multiple sequential operations work correctly."""
        operations = [
            ("GET", "/health", None, 200),
            ("GET", "/items/1", None, 200),
            ("POST", "/items", {"name": "item1", "price": 10.0}, 200),
            ("GET", "/items/1", None, 200),
            ("POST", "/items", {"name": "item2", "price": 0}, 400),
            ("GET", "/items/1", None, 200),
        ]
        
        for method, path, data, expected_status in operations:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.post(path, json=data)
            assert r.status_code == expected_status


class TestErrorRecovery:
    """Test error recovery and resilience."""

    def test_recover_from_validation_error(self):
        """Verify API recovers from validation errors."""
        # Send invalid request
        r1 = client.post("/items", json={"name": "test"})
        assert r1.status_code == 422
        
        # Send valid request
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200
        
        # Verify response is correct
        assert r2.json()["name"] == "test"

    def test_recover_from_business_error(self):
        """Verify API recovers from business logic errors."""
        # Send request violating business logic
        r1 = client.post("/items", json={"name": "test", "price": -1})
        assert r1.status_code == 400
        
        # Send valid request
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_recover_from_not_found_error(self):
        """Verify API recovers from not found errors."""
        # Request non-existent item
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Request existing item
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestRequestMethodValidation:
    """Test that only correct HTTP methods work."""

    def test_create_requires_post(self):
        """Verify POST is required for create endpoint."""
        # GET should not work for create
        r = client.get("/items")
        assert r.status_code in [404, 405]  # Not Found or Method Not Allowed

    def test_get_requires_get(self):
        """Verify GET is required for get endpoint."""
        # POST should not work for get
        r = client.post("/items/1", json={})
        assert r.status_code in [404, 405]  # Not Found or Method Not Allowed

    def test_health_requires_get(self):
        """Verify GET is required for health endpoint."""
        # POST should not work
        r = client.post("/health", json={})
        assert r.status_code in [404, 405]


class TestResponseDataConsistency:
    """Test that response data remains consistent and accurate."""

    def test_create_response_name_matches_input(self):
        """Verify created item name matches input exactly."""
        input_names = ["test", "Test Item", "UPPERCASE", "123numbers"]
        for name in input_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_response_price_matches_input(self):
        """Verify created item price matches input exactly."""
        input_prices = [0.01, 1.5, 10.0, 99.99, 1000.0]
        for price in input_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_get_response_always_same(self):
        """Verify get response for item 1 is always identical."""
        responses = [client.get("/items/1").json() for _ in range(5)]
        first = responses[0]
        assert all(r == first for r in responses)

    def test_multiple_creates_preserve_all_data(self):
        """Verify multiple creates all preserve input data."""
        test_data = [
            {"name": "apple", "price": 1.5},
            {"name": "book", "price": 25.99},
            {"name": "computer", "price": 999.99},
        ]
        
        for data in test_data:
            r = client.post("/items", json=data)
            assert r.status_code == 200
            resp = r.json()
            assert resp["name"] == data["name"]
            assert resp["price"] == data["price"]
