# Lipstick Virtual Try-On — Image Service

## راه‌اندازی (یک‌بار، اول کار)

1. ساخت و فعال‌سازی محیط مجازی (از داخل پوشهٔ image_service):

   Windows (PowerShell):
       python -m venv venv
       .\venv\Scripts\Activate.ps1

   Mac/Linux:
       python3 -m venv venv
       source venv/bin/activate

2. نصب کتابخانه‌ها:
       pip install -r requirements.txt

## تست فاز ۳ (استخراج رنگ از سواچ) — همین الان قابل اجراست

عکس‌های تست از قبل در test_images/ هستند (swatch_1/2/3.jfif).

اجرای مستقیم روی یک عکس:
       python -m app.core.color_extract test_images/swatch_1.jfif

ثبت هر سه محصول تستی در کاتالوگ (products.json):
       python -m app.register_product

## تست فاز ۲ (اعمال رنگ روی لب) — نیاز به یک عکس چهره دارد

یک عکس چهرهٔ frontal (رو‌به‌رو، نور یکنواخت) را در پوشهٔ اصلی بگذار، مثلاً
face_sample.jpg، سپس:

       python -c "
import cv2, json
from app.core.face_landmarks import get_lip_landmarks, build_lip_mask
from app.core.color_lab import apply_color_to_masked_region

with open('products.json', encoding='utf-8') as f:
    products = json.load(f)

img = cv2.imread('face_sample.jpg')
landmarks = get_lip_landmarks(img)
mask = build_lip_mask(img.shape, landmarks, feather_px=4)
result = apply_color_to_masked_region(img, mask, products[0]['lab'], blend_ratio=0.75)
cv2.imwrite('result.png', result)
"

نکتهٔ مهم نصب مدیاپایپ: حتماً نسخهٔ 0.10.13 نصب شود (در requirements.txt
مشخص است). نسخه‌های 0.10.30 به بعد دیگر شامل API قدیمی نمی‌شوند و کار نمی‌کنند.
اگر pip نسخهٔ دقیق را برای سیستم شما پیدا نکرد، این را امتحان کن:
       pip install "mediapipe>=0.10.13,<0.10.30"

## اجرای سرور FastAPI (همه‌ی endpoint های فاز ۱/۲/۳ کار می‌کنند)

       uvicorn app.main:app --reload

بعد مرورگر را باز کن: http://127.0.0.1:8000/docs
از همان‌جا می‌توانی:
- /extract-product-color را با آپلود عکس سواچ تست کنی
- /apply-lipstick را با آپلود عکس چهره + یک product_id (۱، ۲ یا ۳) تست کنی
  (خروجی یک فایل PNG قابل دانلود از همان صفحهٔ Swagger است)

## وضعیت فعلی پروژه

| بخش | وضعیت |
|---|---|
| فاز ۳ - استخراج رنگ از سواچ فروشنده | ✅ کامل و تست‌شده |
| فاز ۱ - اسکلت FastAPI | ✅ آماده |
| فاز ۲ - اعمال رنگ روی لب (apply_lipstick) | ✅ کامل و تست‌شده روی عکس واقعی |
| فاز ۴ - تحلیل تن پوست (skin_tone) | ⏳ در انتظار |
| فاز ۵ - لایو در مرورگر | ⏳ شروع نشده |
| فاز ۶ - اتصال n8n | ⏳ شروع نشده |

## ساختار پوشه‌ها

    image_service/
    ├── app/
    │   ├── main.py                 # اپ اصلی FastAPI
    │   ├── register_product.py     # ثبت محصول در کاتالوگ (تست‌شده)
    │   ├── core/
    │   │   ├── color_extract.py    # ✅ استخراج رنگ از سواچ (تست‌شده)
    │   │   ├── color_lab.py        # ⏳ اعمال رنگ Lab روی لب (فاز ۲)
    │   │   └── face_landmarks.py   # ⏳ تشخیص لندمارک صورت (فاز ۲/۴)
    │   ├── routers/
    │   │   ├── product_color.py    # ✅ endpoint استخراج رنگ
    │   │   ├── apply_lipstick.py   # ⏳ endpoint اعمال رژ
    │   │   └── skin_tone.py        # ⏳ endpoint تحلیل پوست
    │   └── models/
    │       └── schemas.py          # مدل‌های Pydantic
    ├── test_images/                # عکس‌های تست (۳ سواچ واقعی)
    ├── requirements.txt
    └── README.md
