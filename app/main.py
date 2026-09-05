"""
اپلیکیشن اصلی FastAPI — همه‌ی روترها اینجا به هم وصل می‌شن.

اجرا:
    uvicorn app.main:app --reload

بعد از اجرا، مستندات تعاملی API در آدرس زیر در دسترسه:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from app.routers import product_color, apply_lipstick, skin_tone

app = FastAPI(title="Lipstick Virtual Try-On Service")

app.include_router(product_color.router)
app.include_router(apply_lipstick.router)
app.include_router(skin_tone.router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Lipstick try-on image service is running"}
