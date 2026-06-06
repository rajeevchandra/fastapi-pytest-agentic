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

    @pytest.mark.parametrize("price", [0.01, 1, 100, 9999.99])
    def test_create_item_with_various_valid_prices(self, price):
        r = client.post("/items", json={"name": "product", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_very_long_name(self):
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_special_characters_in_name(self):
        special_name = "Product™ with™ émojis 🎉"
        r = client.post("/items", json={"name": special_name, "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name


class TestCreateItemPriceValidation:
    def test_create_item_rejects_zero_price(self):
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-1, -0.01, -100, -9999.99])
    def test_create_item_rejects_negative_prices(self, price):
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_accepts_very_large_price(self):
        large_price = 999999999.99
        r = client.post("/items", json={"name": "expensive", "price": large_price})
        assert r.status_code == 200
        assert r.json()["price"] == large_price


class TestCreateItemInputValidation:
    def test_create_item_missing_name_field(self):
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_price_field(self):
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_all_fields(self):
        r = client.post("/items", json={})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_invalid_json(self):
        r = client.post("/items", content="{invalid json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_create_item_with_null_name(self):
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_null_price(self):
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_numeric_string_price_accepted(self):
        # Pydantic coerces numeric strings to float
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_with_non_numeric_string_price(self):
        r = client.post("/items", json={"name": "item", "price": "abc"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_numeric_name(self):
        r = client.post("/items", json={"name": 12345, "price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_empty_name(self):
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_with_whitespace_name(self):
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_with_extra_fields(self):
        r = client.post("/items", json={"name": "item", "price": 10.0, "extra_field": "ignored"})
        assert r.status_code == 200
        assert "extra_field" not in r.json()


class TestGetItemSuccess:
    def test_get_item_found(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_structure(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3


class TestGetItemNotFound:
    def test_get_item_not_found(self):
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, 3, 999, 99999])
    def test_get_item_not_found_various_ids(self, item_id):
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_id_boundary_negative_one(self):
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_id_boundary_zero(self):
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_boundary_large(self):
        r = client.get("/items/2147483647")
        assert r.status_code == 404
