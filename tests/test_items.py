import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemSuccess:
    def test_create_item_success(self):
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "book"
        assert data["price"] == 12.5

    @pytest.mark.parametrize("price", [0.01, 1, 100, 999.99, 10000.5])
    def test_create_item_various_positive_prices(self, price):
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    @pytest.mark.parametrize("name", ["a", "Book", "Item with spaces", "CAPS", "item123"])
    def test_create_item_various_names(self, name):
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name


class TestCreateItemPriceValidation:
    def test_create_item_rejects_zero_price(self):
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-1, -0.01, -100, -999.99])
    def test_create_item_rejects_negative_prices(self, price):
        r = client.post("/items", json={"name": "bad", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-1, -100])
    def test_create_item_negative_price_response_structure(self, price):
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestCreateItemMissingFields:
    def test_create_item_missing_name(self):
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_empty_json(self):
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    def test_create_item_price_as_string(self):
        r = client.post("/items", json={"name": "book", "price": "10.0"})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_price_as_null(self):
        r = client.post("/items", json={"name": "book", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_null(self):
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemEdgeCases:
    def test_create_item_empty_name(self):
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == ""

    def test_create_item_whitespace_name(self):
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "   "

    def test_create_item_very_long_name(self):
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name

    def test_create_item_very_large_price(self):
        large_price = 999999999.99
        r = client.post("/items", json={"name": "expensive", "price": large_price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == large_price

    def test_create_item_very_small_positive_price(self):
        r = client.post("/items", json={"name": "cheap", "price": 0.0001})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 0.0001

    def test_create_item_extra_fields(self):
        r = client.post("/items", json={"name": "book", "price": 10.0, "extra": "field"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "book"


class TestGetItem:
    def test_get_item_found(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_not_found(self):
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999])
    def test_get_item_various_not_found_ids(self, item_id):
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"
