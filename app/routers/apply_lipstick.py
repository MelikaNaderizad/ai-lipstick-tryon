"""
Endpoint: POST /apply-lipstick
ورودی: عکس مشتری (multipart) + product_id (باید در products.json موجود باشد)
خروجی: عکس نهایی (PNG) با رژ اعمال‌شده روی لب
"""

import json
import os
import shutil
import tempfile

import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.core.face_landmarks import get_lip_landmarks, build_lip_mask
from app.core.color_lab import apply_color_to_masked_region

router = APIRouter()

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "products.json",
)


def _load_product(product_id: int):
    if not os.path.exists(CATALOG_PATH):
        return None
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    return next((p for p in catalog if p["id"] == product_id), None)


@router.post("/apply-lipstick")
async def apply_lipstick(file: UploadFile = File(...), product_id: int = None):
    if product_id is None:
        raise HTTPException(status_code=400, detail="product_id لازم است")

    product = _load_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"محصولی با id={product_id} پیدا نشد")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    img = cv2.imread(tmp_path)
    if img is None:
        raise HTTPException(status_code=400, detail="فایل تصویر معتبر نیست")

    landmarks = get_lip_landmarks(img)
    if landmarks is None:
        raise HTTPException(status_code=422, detail="چهره‌ای در عکس تشخیص داده نشد")

    mask = build_lip_mask(img.shape, landmarks, feather_px=4)
    result = apply_color_to_masked_region(img, mask, product["lab"], blend_ratio=0.75)

    out_path = tmp_path.replace(".jpg", "_result.png")
    cv2.imwrite(out_path, result)

    return FileResponse(out_path, media_type="image/png")
