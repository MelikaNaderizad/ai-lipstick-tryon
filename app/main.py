"""
اپلیکیشن اصلی FastAPI — همه‌ی روترها اینجا به هم وصل می‌شن.

🔧 CHANGE: روتر جدید products (GET /products) اضافه شد — برای اینکه
ایجنت n8n بتونه لیست کاتالوگ رو بخونه.

اجرا (از ریشهٔ پروژه):
    uvicorn app.main:app --reload

بعد از اجرا:
    http://127.0.0.1:8000/docs                -> مستندات تعاملی API
    http://127.0.0.1:8000/static/index.html   -> صفحهٔ تست (عکس + لایو)
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import product_color, apply_lipstick, skin_tone, products

app = FastAPI(title="Lipstick Virtual Try-On Service")

app.include_router(product_color.router)
app.include_router(apply_lipstick.router)
app.include_router(skin_tone.router)
app.include_router(products.router)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Lipstick try-on image service is running"}
