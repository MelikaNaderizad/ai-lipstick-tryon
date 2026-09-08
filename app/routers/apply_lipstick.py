"""
Endpoint: POST /apply-lipstick
ورودی: عکس مشتری (multipart) + product_id (باید در products.json موجود باشد)
خروجی: JSON شامل لینک عکس نتیجه (نه خودِ فایل باینری)

🔧 CHANGE (برای سازگاری با ایجنت n8n): قبلاً این endpoint مستقیم فایل
PNG رو برمی‌گردوند (FileResponse). این برای فراخوانی مستقیم از مرورگر
(static/test_client.html) خوب بود، ولی وقتی این endpoint قراره از طریق
یه AI Agent (که با LLM کار می‌کنه) صدا زده بشه، LLM نمی‌تونه باینری رو
پردازش کنه — فقط متن/JSON می‌فهمه.

برای همین حالا عکس نتیجه رو ذخیره می‌کنیم توی static/results/ (که از
قبل mount شده روی /static) و به‌جاش یه JSON با لینک عکس برمی‌گردونیم.
این‌جوری هم Agent می‌تونه لینک رو توی جوابش بذاره، هم فرانت (ویجت وب)
می‌تونه مستقیم <img src="..."> نمایشش بده.

⚠️ نکته‌ی deployment: این لینک نسبیه (/static/results/xxx.png). وقتی
سرور رو روی دامنه‌ی واقعی بالا بردی، باید base_url رو هم بهش اضافه کنی
(یا از طریق reverse proxy همون دامنه رو serve کنی) تا مرورگر کاربر
نهایی بتونه بهش دسترسی داشته باشه.
"""

import json
import os
import shutil
import tempfile
import uuid

import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.face_landmarks import get_lip_contours, build_lip_mask
from app.core.color_lab import apply_color_to_masked_region
from app.core.color_extract import lab_to_rgb_preview

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG_PATH = os.path.join(BASE_DIR, "products.json")
RESULTS_DIR = os.path.join(BASE_DIR, "static", "results")

os.makedirs(RESULTS_DIR, exist_ok=True)


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

    contours = get_lip_contours(img)
    if contours is None:
        raise HTTPException(status_code=422, detail="چهره‌ای در عکس تشخیص داده نشد")

    mask = build_lip_mask(img.shape, contours, feather_px=4)
    result = apply_color_to_masked_region(img, mask, product["lab"])

    out_filename = f"{uuid.uuid4().hex}.png"
    out_path = os.path.join(RESULTS_DIR, out_filename)
    cv2.imwrite(out_path, result)

    r, g, b = lab_to_rgb_preview(product["lab"]["l"], product["lab"]["a"], product["lab"]["b"])

    return {
        "image_url": f"/static/results/{out_filename}",
        "product_id": product["id"],
        "product_name": product["name"],
        "hex": f"#{r:02x}{g:02x}{b:02x}",
    }
