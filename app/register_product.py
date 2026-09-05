"""
ثبت محصول جدید در کاتالوگ (products.json).

این اسکریپت روی ۳ عکس واقعی تست شده و درست کار می‌کند.

اجرا (از داخل پوشهٔ image_service):
    python -m app.register_product
"""

import json
import os

from app.core.color_extract import extract_dominant_swatch_color

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(BASE_DIR, "products.json")


def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return []
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_catalog(catalog):
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)


def register_product(name: str, swatch_image_path: str, brand: str = ""):
    """
    یک محصول جدید را با استخراج رنگ واقعی از عکس سواچ، به کاتالوگ اضافه می‌کند.
    اگر محصولی با همین اسم از قبل وجود داشته باشد، رنگش به‌روزرسانی می‌شود.
    """
    result = extract_dominant_swatch_color(swatch_image_path)
    lab = result["swatch_lab"]

    catalog = load_catalog()

    existing = next((p for p in catalog if p["name"] == name), None)
    new_id = max([p["id"] for p in catalog], default=0) + 1

    entry = {
        "id": existing["id"] if existing else new_id,
        "name": name,
        "brand": brand,
        "swatch_image_path": swatch_image_path,
        "lab": lab,
    }

    if existing:
        catalog = [entry if p["id"] == entry["id"] else p for p in catalog]
    else:
        catalog.append(entry)

    save_catalog(catalog)
    return entry


if __name__ == "__main__":
    test_products = [
        ("رژ ۱", "test_images/swatch_1.jfif"),
        ("رژ ۲", "test_images/swatch_2.jfif"),
        ("رژ ۳", "test_images/swatch_3.jfif"),
    ]

    for name, path in test_products:
        entry = register_product(name, path)
        print(f"ثبت شد: {entry['name']} -> Lab={entry['lab']}")

    print(f"\nکاتالوگ نهایی در: {CATALOG_PATH}")
