import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test valid price scenarios for create_item endpoint."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.5, 100.0, 999.99])
    def test_create_item_with_valid_prices(self, price):
        """Test create_item accepts various valid positive prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price
        assert "id" in data
        assert "name" in data


class TestCreateItemInvalidPrice:
    """Test invalid price scenarios for create_item endpoint."""

    @pytest.mark.parametrize("price", [0, -1, -0.01, -100, -999999])
    def test_create_item_with_non_positive_prices(self, price):
        """Test create_item rejects zero and negative prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [1e6, 1e10, 1e15, 999999999.99])
    def test_create_item_with_very_large_prices(self, price):
        """Test create_item accepts very large valid prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price


class TestCreateItemValidName:
    """Test valid name scenarios for create_item endpoint."""

    @pytest.mark.parametrize("name", [
        "book",
        "A",
        "123",
        "test item",
        "item_123",
        "item-456",
        "Product 1.0",
    ])
    def test_create_item_with_valid_names(self, name):
        """Test create_item accepts various valid names."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        assert data["price"] == 10.0


class TestCreateItemUnicode:
    """Test unicode and special character handling in item names."""

    @pytest.mark.parametrize("name", [
        "café",
        "日本語",
        "Москва",
        "العربية",
        "emoji🎉",
        "naïve",
        "Ñoño",
    ])
    def test_create_item_with_unicode_names(self, name):
        """Test create_item handles unicode characters in names."""
        response = client.post("/items", json={"name": name, "price": 5.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name


class TestCreateItemEmptyName:
    """Test empty and whitespace name handling."""

    def test_create_item_with_empty_name(self):
        """Test create_item accepts empty string name."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == ""

    @pytest.mark.parametrize("name", [" ", "  ", "\t", "\n"])
    def test_create_item_with_whitespace_names(self, name):
        """Test create_item handles whitespace-only names."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name


class TestCreateItemLongName:
    """Test long name handling."""

    @pytest.mark.parametrize("length", [50, 100, 500, 1000])
    def test_create_item_with_long_names(self, length):
        """Test create_item handles very long names."""
        long_name = "x" * length
        response = client.post("/items", json={"name": long_name, "price": 5.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == long_name
        assert len(data["name"]) == length


class TestCreateItemSpecialCharacters:
    """Test special character handling in item names."""

    @pytest.mark.parametrize("name", [
        "name!",
        "name@test",
        "name#123",
        "name$value",
        "name%percent",
        "name&and",
        "name*star",
        "name(paren)",
        "name[bracket]",
        "name{brace}",
        "name|pipe",
        "name\\backslash",
        "name/slash",
        "name:colon",
        "name;semicolon",
        "name'quote",
        'name"doublequote',
    ])
    def test_create_item_with_special_characters(self, name):
        """Test create_item handles various special characters in names."""
        response = client.post("/items", json={"name": name, "price": 5.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name


class TestCreateItemResponseStructure:
    """Test response structure and data types for create_item."""

    def test_create_item_response_has_required_fields(self):
        """Test response contains all required fields with correct types."""
        response = client.post("/items", json={"name": "test", "price": 15.5})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_id_is_one(self):
        """Test create_item always returns id=1."""
        response = client.post("/items", json={"name": "item1", "price": 5.0})
        assert response.json()["id"] == 1
        response = client.post("/items", json={"name": "item2", "price": 10.0})
        assert response.json()["id"] == 1
