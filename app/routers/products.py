"""
Endpoint: GET /products
خروجی: لیست محصولات کاتالوگ (id, name, رنگ به‌صورت hex برای نمایش/تصمیم‌گیری)

چرا این endpoint لازمه: ایجنت (توی n8n) برای اینکه بتونه از روی پیام
کاربر ("رژ ۲ رو بزن"، "چه رژی بهم میاد؟") تصمیم بگیره کدوم product_id
رو به /apply-lipstick بده، باید بتونه لیست محصولات رو بخونه. این
endpoint دقیقاً همون کاری رو می‌کنه که products.json می‌کنه، ولی از
طریق HTTP و با رنگ آماده‌ی نمایش (hex).
"""

import json
import os

from fastapi import APIRouter

from app.core.color_extract import lab_to_rgb_preview

router = APIRouter()

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "products.json",
)


@router.get("/products")
async def list_products():
    if not os.path.exists(CATALOG_PATH):
        return []

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    result = []
    for p in catalog:
        r, g, b = lab_to_rgb_preview(p["lab"]["l"], p["lab"]["a"], p["lab"]["b"])
        result.append({
            "id": p["id"],
            "name": p["name"],
            "brand": p.get("brand", ""),
            "hex": f"#{r:02x}{g:02x}{b:02x}",
        })
    return result
