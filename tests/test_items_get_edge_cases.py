"""
Edge cases and integration tests for items API.

Tests cover:
- Boundary value testing for item_id
- Interaction patterns between endpoints
- Stress testing with various input combinations
- Special scenarios and corner cases
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test GET /items/{item_id} with boundary value item_ids."""
    
    @pytest.mark.parametrize("item_id", [0, -1, -100, -2**31])
    def test_negative_and_zero_item_ids_not_found(self, item_id):
        """Test that zero and negative item_ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"
    
    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 2**31])
    def test_positive_item_ids_not_found(self, item_id):
        """Test that positive ids other than 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
    
    def test_item_id_one_found(self):
        """Test that only item_id 1 returns success."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1
    
    @pytest.mark.parametrize("item_id", [1.5, 1.0, 0.5])
    def test_float_like_item_ids(self, item_id):
        """Test behavior with float-like values in URL."""
        # FastAPI converts these to ints in path, may cause issues
        r = client.get(f"/items/{item_id}")
        # Depends on FastAPI's type coercion
        assert r.status_code in [200, 404, 422]


class TestPriceExtremes:
    """Test price field with extreme values."""
    
    @pytest.mark.parametrize("price", [
        0.0000001,  # very small
        1e-10,       # scientific notation small
        1e20,        # very large
        999999999.99,  # large normal number
    ])
    def test_extreme_positive_prices(self, price):
        """Test very large and very small positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price
    
    @pytest.mark.parametrize("price", [
        -0.0000001,
        -1e-10,
        -1e20,
        -999999999.99,
    ])
    def test_extreme_negative_prices_rejected(self, price):
        """Test that extreme negative prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestNameBoundaryValues:
    """Test name field with boundary value lengths."""
    
    def test_single_character_name(self):
        """Test name with single character."""
        r = client.post("/items", json={"name": "A", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "A"
    
    def test_very_long_name(self):
        """Test name with many characters."""
        long_name = "X" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name
        assert len(r.json()["name"]) == 10000
    
    def test_whitespace_only_name(self):
        """Test name that is only whitespace."""
        r = client.post("/items", json={"name": "   ", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "   "
    
    def test_newline_in_name(self):
        """Test name containing newlines."""
        r = client.post("/items", json={"name": "line1\nline2\nline3", "price": 10})
        assert r.status_code == 200
        assert "line1\nline2\nline3" in r.json()["name"]
    
    def test_tab_in_name(self):
        """Test name containing tabs."""
        r = client.post("/items", json={"name": "col1\tcol2\tcol3", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "col1\tcol2\tcol3"


class TestEndpointInteractions:
    """Test interaction patterns between endpoints."""
    
    def test_create_then_get_workflow(self):
        """Test creating an item and then retrieving it."""
        # Create
        create_r = client.post("/items", json={"name": "book", "price": 15.99})
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Get the created item
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify they match (noting that API only returns id=1)
        assert retrieved["id"] == created["id"] == 1
    
    def test_health_check_independence(self):
        """Test that health check is independent of items operations."""
        # Health should work before any items
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        # Create item
        client.post("/items", json={"name": "test", "price": 10})
        
        # Health should still work
        r2 = client.get("/health")
        assert r2.status_code == 200
        assert r1.json() == r2.json()
    
    def test_multiple_creates_independent(self):
        """Test that multiple create requests are independent."""
        r1 = client.post("/items", json={"name": "first", "price": 10})
        r2 = client.post("/items", json={"name": "second", "price": 20})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both return id=1 (mocked)
        assert r1.json()["id"] == r2.json()["id"] == 1
    
    def test_get_before_create(self):
        """Test getting item before creating any."""
        r = client.get("/items/1")
        # Should return 200 because item 1 exists
        assert r.status_code == 200
    
    def test_mixed_workflow(self):
        """Test mixed operations in sequence."""
        # Health
        assert client.get("/health").status_code == 200
        
        # Create
        assert client.post("/items", json={"name": "a", "price": 5}).status_code == 200
        
        # Get existing
        assert client.get("/items/1").status_code == 200
        
        # Get non-existing
        assert client.get("/items/999").status_code == 404
        
        # Create with error
        assert client.post("/items", json={"name": "b", "price": -1}).status_code == 400
        
        # Health still works
        assert client.get("/health").status_code == 200


class TestCombinedValidation:
    """Test combinations of valid and invalid inputs."""
    
    @pytest.mark.parametrize("combo", [
        ("valid_name", 0),
        ("valid_name", -1),
        ("", 10),  # empty name allowed?
        ("name", 10.5),
    ])
    def test_various_input_combinations(self, combo):
        """Test various combinations of inputs."""
        name, price = combo
        r = client.post("/items", json={"name": name, "price": price})
        
        if price > 0:
            assert r.status_code == 200
        else:
            assert r.status_code == 400
    
    @pytest.mark.parametrize("price", [0.01, 1, 100, 1000])
    @pytest.mark.parametrize("name_prefix", ["Item", "Product", ""])
    def test_cartesian_name_price_combinations(self, name_prefix, price):
        """Test cartesian product of names and prices."""
        r = client.post("/items", json={"name": name_prefix, "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestErrorRecovery:
    """Test API behavior after errors."""
    
    def test_api_works_after_validation_error(self):
        """Test that API works normally after receiving validation error."""
        # Send bad request
        bad_r = client.post("/items", json={"name": "item", "price": -5})
        assert bad_r.status_code == 400
        
        # Send good request after
        good_r = client.post("/items", json={"name": "item", "price": 10})
        assert good_r.status_code == 200
    
    def test_api_works_after_not_found(self):
        """Test that API works normally after 404."""
        # Get non-existent
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Get existing should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200
    
    def test_repeated_errors_consistent(self):
        """Test that repeated errors are consistent."""
        results = []
        for _ in range(3):
            r = client.post("/items", json={"name": "item", "price": -1})
            results.append((r.status_code, r.json()["detail"]))
        
        # All should be identical
        assert all(r[0] == 400 for r in results)
        assert all(r[1] == "price must be > 0" for r in results)


class TestDataTypePreservation:
    """Test that data types are preserved through the API."""
    
    def test_string_name_preserved(self):
        """Test that name stays as string."""
        names = ["abc", "123", "[]", "{}"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10})
            assert r.status_code == 200
            assert isinstance(r.json()["name"], str)
            assert r.json()["name"] == name
    
    def test_numeric_price_preserved(self):
        """Test that price type is preserved."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200
        price = r.json()["price"]
        # Should be numeric
        assert isinstance(price, (int, float))
        assert price == 10
    
    def test_integer_id_in_response(self):
        """Test that id is always integer."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)


class TestSpecialStringCharacters:
    """Test handling of special characters in strings."""
    
    @pytest.mark.parametrize("special_name", [
        "Item's",  # apostrophe
        'Item"quoted"',  # quotes
        "Item\\backslash",  # backslash
        "Item/slash",  # forward slash
        "Item|pipe",  # pipe
        "Item*asterisk",  # asterisk
        "Item?question",  # question mark
        "Item:colon",  # colon
        "Item;semicolon",  # semicolon
    ])
    def test_special_characters_in_name(self, special_name):
        """Test various special characters in product names."""
        r = client.post("/items", json={"name": special_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == special_name
    
    def test_control_characters_in_name(self):
        """Test control characters in name."""
        # Null byte, bell, etc
        names_with_control = [
            "Item\x00Null",  # null byte
            "Item\x07Bell",  # bell
            "Item\x08Backspace",  # backspace
        ]
        for name in names_with_control:
            r = client.post("/items", json={"name": name, "price": 10})
            # Should either accept or reject, but not crash
            assert r.status_code in [200, 400, 422]


class TestAPIRobustness:
    """Test API robustness and resilience."""
    
    def test_sequential_requests(self):
        """Test that API handles sequential requests correctly."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10 + i})
            assert r.status_code == 200
    
    def test_mixed_valid_invalid_sequence(self):
        """Test sequence of valid and invalid requests."""
        sequence = [
            ({"name": "good", "price": 10}, 200),
            ({"name": "bad", "price": -1}, 400),
            ({"name": "good2", "price": 20}, 200),
            ({"name": "bad2", "price": 0}, 400),
            ({"name": "good3", "price": 5}, 200),
        ]
        
        for data, expected_status in sequence:
            r = client.post("/items", json=data)
            assert r.status_code == expected_status
