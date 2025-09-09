from fastapi import APIRouter, HTTPException
import json

router = APIRouter()

@router.get("/products")
def get_products():
    with open("app/data/products.json") as f:
        products = json.load(f)
    
    filtered_products = [
        {
            "id": product["id"],
            "title": product["title"],
            "category": product["category"],
            "image": product["image"]
        }
        for product in products
    ]
    
    return filtered_products


@router.get("/products/{product_id}")
def get_product(product_id: int):
    with open("app/data/products.json") as f:
        products = json.load(f)

    for product in products:
        if product.get("id") == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")