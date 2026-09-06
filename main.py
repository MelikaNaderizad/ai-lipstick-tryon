"""
اپلیکیشن اصلی FastAPI — همه‌ی روترها اینجا به هم وصل می‌شن.

🔧 FIX: اضافه شدن StaticFiles روی مسیر /static تا صفحات تست
(test_client.html و live_tryon.html) از همون سروری که API روشه سرو بشن.
این باعث می‌شه:
  - نیازی به باز کردن فایل با file:// نباشه (که بعضی مرورگرها روش
    محدودیت دارن، مخصوصاً برای getUserMedia/وبکم).
  - fetch های test_client.html بتونن از آدرس نسبی (/apply-lipstick) استفاده
    کنن، پس دیگه دغدغه‌ی CORS بین origin های مختلف نداریم.

اجرا:
    uvicorn app.main:app --reload

بعد از اجرا:
    http://127.0.0.1:8000/docs                -> مستندات تعاملی API
    http://127.0.0.1:8000/static/index.html   -> صفحهٔ تست (عکس + لایو)
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import product_color, apply_lipstick, skin_tone

app = FastAPI(title="Lipstick Virtual Try-On Service")

app.include_router(product_color.router)
app.include_router(apply_lipstick.router)
app.include_router(skin_tone.router)

# پوشه‌ی static/ باید کنار پوشه‌ی app/ (در ریشه‌ی پروژه) باشه
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Lipstick try-on image service is running"}
