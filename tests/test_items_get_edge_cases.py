"""Edge cases and path parameter tests for item operations."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation with boundary values."""
    
    @pytest.mark.parametrize("item_id,should_exist", [
        (1, True),                              # Valid ID
        (2, False),                             # Non-existent ID
        (0, False),                             # Zero ID
        (-1, False),                            # Negative ID
        (999999, False),                        # Very large ID
    ])
    def test_get_item_id_boundaries(self, item_id, should_exist):
        """Test item retrieval with various ID values."""
        response = client.get(f"/items/{item_id}")
        if should_exist:
            assert response.status_code == 200
            assert response.json()["id"] == item_id
        else:
            assert response.status_code == 404


class TestCreateItemWithPriceEdgeCases:
    """Test edge cases in price values."""
    
    def test_very_large_price(self):
        """Test handling of very large price values."""
        response = client.post("/items", json={"name": "expensive", "price": 1e10})
        assert response.status_code == 200
        assert response.json()["price"] == 1e10


    def test_very_small_price(self):
        """Test handling of very small but valid price."""
        response = client.post("/items", json={"name": "cheap", "price": 0.001})
        assert response.status_code == 200
        assert response.json()["price"] == 0.001


    def test_price_with_many_decimals(self):
        """Test price with many decimal places."""
        response = client.post("/items", json={"name": "precise", "price": 10.123456789})
        assert response.status_code == 200


    @pytest.mark.parametrize("price", [0.0, -0.0, -0.1, -1, -100, -999999])
    def test_various_negative_prices(self, price):
        """Test rejection of various negative and zero prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400


class TestCreateItemWithNameEdgeCases:
    """Test edge cases in name values."""
    
    def test_very_long_name(self):
        """Test handling of very long name."""
        long_name = "x" * 1000
        response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == long_name


    def test_name_with_only_spaces(self):
        """Test name consisting only of spaces."""
        response = client.post("/items", json={"name": "   ", "price": 10.0})
        assert response.status_code == 200


    def test_name_with_special_characters(self):
        """Test name with various special characters."""
        special_name = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        response = client.post("/items", json={"name": special_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == special_name


    def test_name_with_newlines_and_tabs(self):
        """Test name with newlines and tab characters."""
        response = client.post("/items", json={"name": "line1\nline2\ttab", "price": 10.0})
        assert response.status_code == 200


    def test_name_with_unicode_emoji(self):
        """Test name with unicode emoji characters."""
        emoji_name = "Product 🚀 ✨ 🎉"
        response = client.post("/items", json={"name": emoji_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == emoji_name


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_create_multiple_items(self):
        """Test creating multiple items sequentially."""
        for i in range(5):
            response = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert response.status_code == 200
            assert response.json()["id"] == 1  # API always returns id=1


    def test_get_existing_item_after_creation(self):
        """Test retrieving item after creation."""
        # First create an item
        create_response = client.post("/items", json={"name": "test_item", "price": 25.0})
        assert create_response.status_code == 200
        
        # Then retrieve the item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        # Note: get_item returns fixed data, not created item data
        assert get_response.json()["id"] == 1


    def test_get_nonexistent_item_404_detail_format(self):
        """Test that 404 error has correct format."""
        response = client.get("/items/0")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "not found"


    def test_multiple_consecutive_price_validations(self):
        """Test multiple price validations in sequence."""
        valid_prices = [0.01, 1.0, 100.0, 999.99]
        for price in valid_prices:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 200
        
        invalid_prices = [0, -1, -100]
        for price in invalid_prices:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 400


class TestBoundaryValuePairings:
    """Test combinations of boundary values for both name and price."""
    
    @pytest.mark.parametrize("name,price,should_pass", [
        ("a", 0.01, True),                      # Min valid name, min valid price
        ("x" * 1000, 999999, True),             # Max name, large price
        ("normal", 0, False),                   # Normal name, zero price
        ("", 10.0, True),                       # Empty name, valid price (allowed)
        ("test item", -1, False),               # Normal name, negative price
    ])
    def test_boundary_value_combinations(self, name, price, should_pass):
        """Test various combinations of boundary values."""
        response = client.post("/items", json={"name": name, "price": price})
        if should_pass:
            assert response.status_code == 200
        else:
            assert response.status_code == 400


class TestErrorMessageConsistency:
    """Test consistency of error messages."""
    
    def test_price_error_message_consistent(self):
        """Test that price error message is consistent."""
        prices = [0, -1, -0.5]
        for price in prices:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 400
            assert response.json()["detail"] == "price must be > 0"


    def test_not_found_error_message_consistent(self):
        """Test that not found error message is consistent."""
        ids = [2, 0, -1, 999]
        for item_id in ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"


class TestResponseWithDifferentPrices:
    """Test response behavior with different price values."""
    
    @pytest.mark.parametrize("price", [0.01, 1.0, 10.5, 100.0, 999.99, 9999.99])
    def test_response_reflects_submitted_price(self, price):
        """Test that response accurately reflects submitted price."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price


    @pytest.mark.parametrize("name", ["a", "ab", "abc", "product", "long product name"])
    def test_response_reflects_submitted_name(self, name):
        """Test that response accurately reflects submitted name."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name
