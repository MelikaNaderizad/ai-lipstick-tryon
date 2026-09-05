"""
Endpoint: POST /analyze-skin-tone
ورودی: عکس مشتری
خروجی: آندرتون پوست + لیست رتبه‌بندی‌شدهٔ محصولات مناسب از کاتالوگ

هنوز پیاده‌سازی نشده — منتظر تکمیل app/core/face_landmarks.py
(نمونه‌برداری گونه/پیشانی) در فاز ۴ است.
"""

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    return JSONResponse(
        status_code=501,
        content={"detail": "این endpoint هنوز پیاده‌سازی نشده (فاز ۴ رودمپ)"},
    )
