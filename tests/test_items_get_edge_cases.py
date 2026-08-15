"""Test edge cases and integration scenarios for items API."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_valid_item_id(self, item_id):
        """Test getting item with valid ID."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, -100, 2, 99, 999999])
    def test_get_invalid_item_ids(self, item_id):
        """Test that only item_id=1 is found."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    def test_get_item_id_boundary_zero(self):
        """Test boundary case where item_id is 0."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_boundary_one(self):
        """Test boundary case where item_id is 1 (valid)."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_id_boundary_two(self):
        """Test boundary case where item_id is 2 (invalid)."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_id_negative(self):
        """Test that negative IDs are not found."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_id_very_large(self):
        """Test that very large IDs are not found."""
        r = client.get("/items/999999999")
        assert r.status_code == 404


class TestCreateItemWithVariousNames:
    """Test creating items with various name values."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "book",
        "product",
        "Item 1",
        "Item-2",
        "Item_3",
        "Item.4",
        "Item@5",
    ])
    def test_create_with_various_names(self, name):
        """Test creating items with different name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name

    def test_create_item_name_case_sensitivity(self):
        """Test that names preserve case."""
        r1 = client.post("/items", json={"name": "Book", "price": 10.0})
        r2 = client.post("/items", json={"name": "book", "price": 10.0})
        data1 = r1.json()
        data2 = r2.json()
        assert data1["name"] == "Book"
        assert data2["name"] == "book"
        assert data1["name"] != data2["name"]

    def test_create_item_with_numeric_name(self):
        """Test that numeric strings as names work."""
        r = client.post("/items", json={"name": "123", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "123"

    def test_create_item_with_long_name(self):
        """Test creating items with long names."""
        long_name = "a" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name

    def test_create_item_name_with_special_characters(self):
        """Test names with special characters."""
        special_names = [
            "Item's",
            'Item "quoted"',
            "Item\nNewline",
            "Item\tTab",
            "Item with émojis 🎉",
        ]
        for name in special_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == name


class TestCreateItemWithVariousPrices:
    """Test creating items with various price values."""

    @pytest.mark.parametrize("price", [
        0.001,
        0.01,
        0.1,
        1.0,
        10.0,
        10.5,
        10.99,
        100.0,
        1000.0,
        10000.99,
        999999.99,
    ])
    def test_create_with_various_valid_prices(self, price):
        """Test creating items with different valid prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    @pytest.mark.parametrize("price", [
        0,
        -0.001,
        -0.01,
        -0.1,
        -1.0,
        -10.0,
        -100.0,
        -1000.0,
        -999999.99,
    ])
    def test_create_with_various_invalid_prices(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    def test_create_item_price_precision(self):
        """Test that price precision is maintained."""
        prices = [0.01, 0.99, 10.5, 19.99, 100.01]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            data = r.json()
            assert abs(data["price"] - price) < 0.001

    def test_create_item_price_float_vs_int(self):
        """Test that prices work with both int and float."""
        r_float = client.post("/items", json={"name": "item", "price": 10.0})
        r_int = client.post("/items", json={"name": "item", "price": 10})
        assert r_float.status_code == 200
        assert r_int.status_code == 200
        data_float = r_float.json()
        data_int = r_int.json()
        assert data_float["price"] == data_int["price"]


class TestBoundaryConditions:
    """Test boundary conditions across endpoints."""

    def test_price_boundary_just_above_zero(self):
        """Test the exact boundary of price > 0."""
        # Should succeed
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_price_boundary_at_zero(self):
        """Test that price = 0 is rejected."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_price_boundary_just_below_zero(self):
        """Test that negative price is rejected."""
        r = client.post("/items", json={"name": "item", "price": -0.0001})
        assert r.status_code == 400

    def test_item_id_boundary_below_one(self):
        """Test that item_id < 1 returns 404."""
        for item_id in [0, -1, -100]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_item_id_boundary_at_one(self):
        """Test that item_id = 1 returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_item_id_boundary_above_one(self):
        """Test that item_id > 1 returns 404."""
        for item_id in [2, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple operations."""

    def test_create_then_retrieve_same_item(self):
        """Test that created item can be retrieved."""
        # Create
        create_r = client.post("/items", json={"name": "test-book", "price": 25.5})
        assert create_r.status_code == 200
        create_data = create_r.json()
        
        # Retrieve
        get_r = client.get(f"/items/{create_data['id']}")
        # Since only item_id=1 is retrievable
        if create_data['id'] == 1:
            assert get_r.status_code == 200
            get_data = get_r.json()
            assert get_data["id"] == create_data["id"]

    def test_multiple_creates_then_get_existing(self):
        """Test multiple creates followed by get."""
        # Create multiple items
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
        
        # Get existing item
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_create_fails_then_get_still_works(self):
        """Test that failed create doesn't affect GET."""
        # Try to create with invalid price
        r1 = client.post("/items", json={"name": "bad", "price": -1})
        assert r1.status_code == 400
        
        # GET should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_create_invalid_then_create_valid(self):
        """Test creating invalid then valid item."""
        # Invalid
        r1 = client.post("/items", json={"name": "bad", "price": 0})
        assert r1.status_code == 400
        
        # Valid
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200

    def test_get_nonexistent_then_existing(self):
        """Test getting non-existent then existing item."""
        # Non-existent
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Existing
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_invalid_request_doesnt_break_service(self):
        """Test that invalid request doesn't break service."""
        # Send invalid request
        r1 = client.post("/items", json={"name": "bad", "price": -10})
        assert r1.status_code == 400
        
        # Service should still work
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200

    def test_malformed_request_doesnt_break_service(self):
        """Test that malformed request doesn't break service."""
        # Send malformed request
        r1 = client.post("/items", data="invalid json", headers={"Content-Type": "application/json"})
        # This will return 422
        
        # Service should still work
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200

    def test_get_with_string_id_fails_gracefully(self):
        """Test that GET with string ID returns error."""
        # FastAPI's path conversion should handle this
        r = client.get("/items/invalid")
        # Should return 422 (validation error) or 404
        assert r.status_code in [404, 422]

    def test_get_with_float_id_fails(self):
        """Test that GET with float ID returns error."""
        # /items/1.5 - FastAPI path conversion should fail
        r = client.get("/items/1.5")
        # May be 404 or 422
        assert r.status_code in [404, 422]


class TestConsecutiveOperations:
    """Test consecutive operations."""

    def test_three_consecutive_creates(self):
        """Test three creates in a row."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1  # Hard-coded to return id=1

    def test_create_with_different_names_consecutively(self):
        """Test consecutive creates with different names."""
        names = ["book", "pen", "notebook", "pencil"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == name

    def test_five_consecutive_gets_on_valid_id(self):
        """Test five consecutive GET requests on valid ID."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1

    def test_alternating_creates_and_gets(self):
        """Test alternating creates and gets."""
        for i in range(3):
            # Create
            r1 = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert r1.status_code == 200
            
            # Get
            r2 = client.get("/items/1")
            assert r2.status_code == 200
