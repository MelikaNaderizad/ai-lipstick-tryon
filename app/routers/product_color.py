"""
Endpoint: POST /extract-product-color
ورودی: عکس سواچ فروشنده (multipart/form-data)
خروجی: رنگ Lab استخراج‌شده از سواچ

این endpoint از تابع تست‌شدهٔ app/core/color_extract.py استفاده می‌کند.
"""

import shutil
import tempfile

from fastapi import APIRouter, UploadFile, File

from app.core.color_extract import extract_dominant_swatch_color

router = APIRouter()


@router.post("/extract-product-color")
async def extract_product_color(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    result = extract_dominant_swatch_color(tmp_path)
    return {
        "swatch_lab": result["swatch_lab"],
        "swatch_fraction": result["swatch_fraction"],
    }
