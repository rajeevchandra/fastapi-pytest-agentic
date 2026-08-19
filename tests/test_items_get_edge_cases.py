"""
Edge cases and path parameter validation tests.
Tests boundary conditions for path parameters, negative cases, and integration scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [
        1,                           # Valid: positive ID
        0,                           # Edge case: zero ID
        -1,                          # Edge case: negative ID
        -999,                        # Edge case: large negative ID
        999999999,                   # Edge case: very large ID
        1000000000,                  # Edge case: max integer range
    ])
    def test_get_item_path_parameter_boundary_values(self, item_id):
        """Test various item_id boundary values."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestCreateItemWithVariousNames:
    """Test create_item with various name edge cases."""

    @pytest.mark.parametrize("name,should_succeed", [
        ("a", True),                            # Single char
        ("a" * 255, True),                      # Very long name (255 chars)
        ("a" * 1000, True),                     # Extremely long name
        (" leading_space", True),               # Leading space
        ("trailing_space ", True),              # Trailing space
        ("  multiple  spaces  ", True),         # Multiple spaces
        ("123", True),                          # Numeric name
        ("!@#$%^&*()", True),                   # Special characters
        ("Line\nbreak", True),                  # Name with newline
        ("Tab\there", True),                    # Name with tab
    ])
    def test_create_item_various_names(self, name, should_succeed):
        """Test creating items with various name values."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        if should_succeed:
            assert r.status_code == 200
            assert r.json()["name"] == name
        else:
            assert r.status_code in [400, 422]


class TestCreateItemWithVariousPrices:
    """Test create_item with various price edge cases."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.001, True),                          # Very small valid price
        (0.0001, True),                         # Even smaller valid price
        (0.00001, True),                        # Micro price
        (1, True),                              # Integer as price
        (100, True),                            # Larger integer
        (999999.99, True),                      # Large price
        (9999999.99, True),                     # Very large price
        (0, False),                             # Zero (invalid)
        (-0.01, False),                         # Negative (invalid)
        (-999.99, False),                       # Large negative (invalid)
    ])
    def test_create_item_various_prices(self, price, should_succeed):
        """Test creating items with various price values."""
        r = client.post("/items", json={"name": "test", "price": price})
        if should_succeed:
            assert r.status_code == 200
            assert r.json()["price"] == price
        else:
            assert r.status_code == 400


class TestGetItemResponseConsistency:
    """Test that get_item always returns consistent data."""

    def test_get_item_always_returns_same_data_for_id_1(self):
        """Test that get_item/1 always returns the same data."""
        responses = [client.get("/items/1") for _ in range(5)]
        data_points = [r.json() for r in responses]
        # All responses should be identical
        for data in data_points:
            assert data == data_points[0]

    def test_get_item_1_returns_hardcoded_values(self):
        """Test that get_item/1 returns expected hardcoded data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestCreateItemAndReturnedData:
    """Test that created items return expected data."""

    def test_create_item_returns_correct_id(self):
        """Test that created item has id=1."""
        names = ["book", "pen", "notebook", "pencil"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_item_returns_input_name(self):
        """Test that created item returns the input name."""
        names = ["special-book", "book123", "Book with Spaces"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_returns_input_price(self):
        """Test that created item returns the input price."""
        prices = [10.5, 100.0, 0.01, 9999.99]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestMultipleItemCreation:
    """Test creating multiple items in sequence."""

    def test_create_multiple_items_all_get_id_1(self):
        """Test that multiple created items all have id=1."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i+1)})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["name"] == f"item{i}"
            assert data["price"] == float(i+1)


class TestNegativeHTTPStatusCases:
    """Test negative cases and error paths."""

    def test_create_item_without_json_body(self):
        """Test creating item without JSON body."""
        r = client.post("/items")
        assert r.status_code == 422

    def test_create_item_with_empty_object(self):
        """Test creating item with empty JSON object."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_get_nonexistent_items(self):
        """Test getting various nonexistent item IDs."""
        nonexistent_ids = [2, 3, 10, 100, 999, 9999]
        for item_id in nonexistent_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404."""
        r = client.get("/invalid")
        assert r.status_code == 404

    def test_invalid_method_on_endpoint(self):
        """Test that invalid HTTP methods return error."""
        r = client.put("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 405  # Method not allowed


class TestEndpointMethodValidation:
    """Test that endpoints only accept correct HTTP methods."""

    def test_health_only_accepts_get(self):
        """Test health endpoint with various methods."""
        # GET should work
        r = client.get("/health")
        assert r.status_code == 200
        
        # Other methods should fail
        r = client.post("/health")
        assert r.status_code == 405

    def test_create_item_only_accepts_post(self):
        """Test create_item endpoint HTTP method validation."""
        # POST should work
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        
        # GET should fail (create_item only accepts POST)
        r = client.get("/items")
        assert r.status_code == 404  # or 405, depending on routing

    def test_get_item_only_accepts_get(self):
        """Test get_item endpoint HTTP method validation."""
        # GET should work
        r = client.get("/items/1")
        assert r.status_code == 200
        
        # POST should fail
        r = client.post("/items/1", json={})
        assert r.status_code == 405


class TestResponseBodyValidation:
    """Test response bodies contain valid JSON and expected structure."""

    def test_create_item_success_body_valid_json(self):
        """Test that create_item success response is valid JSON."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        try:
            data = r.json()
            assert isinstance(data, dict)
        except ValueError:
            pytest.fail("Response is not valid JSON")

    def test_get_item_success_body_valid_json(self):
        """Test that get_item success response is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        try:
            data = r.json()
            assert isinstance(data, dict)
        except ValueError:
            pytest.fail("Response is not valid JSON")

    def test_error_response_has_detail(self):
        """Test that all error responses have a detail field."""
        error_cases = [
            ("POST", "/items", 422, {"name": "item"}),  # Missing price
            ("POST", "/items", 400, {"name": "item", "price": 0}),  # Invalid price
            ("GET", "/items/999", 404, None),  # Not found
        ]
        for method, endpoint, expected_status, json_data in error_cases:
            if method == "POST":
                r = client.post(endpoint, json=json_data)
            else:
                r = client.get(endpoint)
            assert r.status_code == expected_status
            data = r.json()
            assert "detail" in data


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_create_item_then_get_it(self):
        """Test creating an item then retrieving it."""
        # Create
        create_r = client.post("/items", json={"name": "test-book", "price": 15.0})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Get
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        got_data = get_r.json()
        
        # Check consistency
        assert got_data["id"] == created_data["id"]

    def test_create_item_with_different_prices_all_succeed(self):
        """Test creating multiple items with different prices."""
        prices = [1.0, 5.5, 10.99, 100.00]
        for price in prices:
            r = client.post("/items", json={"name": f"item-{price}", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_health_check_always_available(self):
        """Test that health endpoint is always available."""
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"


class TestBoundaryValuePrices:
    """Test price boundary values more thoroughly."""

    @pytest.mark.parametrize("price", [
        0.001,
        0.01,
        0.1,
        1.0,
        10.0,
        100.0,
        1000.0,
        10000.0,
        99999.99,
    ])
    def test_valid_prices_all_accepted(self, price):
        """Test that all valid prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [
        0,
        -0.001,
        -0.1,
        -1.0,
        -10.0,
        -100.0,
        -1000.0,
    ])
    def test_invalid_prices_all_rejected(self, price):
        """Test that all invalid prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "detail" in r.json()
