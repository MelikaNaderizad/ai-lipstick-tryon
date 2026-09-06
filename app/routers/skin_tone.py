"""
Endpoint: POST /analyze-skin-tone
ورودی: عکس مشتری
خروجی: آندرتون پوست + لیست رتبه‌بندی‌شدهٔ محصولات مناسب از کاتالوگ
"""

import json
import os
import shutil
import tempfile

import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.skin_tone import analyze_skin_tone
from app.models.schemas import SkinToneResponse

router = APIRouter()

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "products.json",
)


def _load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return []
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/analyze-skin-tone", response_model=SkinToneResponse)
async def analyze_skin_tone_endpoint(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    img = cv2.imread(tmp_path)
    if img is None:
        raise HTTPException(status_code=400, detail="فایل تصویر معتبر نیست")

    products = _load_catalog()
    if not products:
        raise HTTPException(status_code=500, detail="کاتالوگ محصولات خالی است")

    result = analyze_skin_tone(img, products)
    if result is None:
        raise HTTPException(status_code=422, detail="چهره‌ای در عکس تشخیص داده نشد")

    return result