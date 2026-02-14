from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ItemIn(BaseModel):
    name: str
    price: float


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/items")
def create_item(item: ItemIn):
    if item.price <= 0:
        raise HTTPException(status_code=400, detail="price must be > 0")
    return {"id": 1, "name": item.name, "price": item.price}


@router.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id != 1:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": 1, "name": "sample", "price": 10.0}
