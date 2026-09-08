"""
پیش‌نمایش سریع: نتیجهٔ اعمال رژ همهٔ محصولات کاتالوگ روی یک عکس چهره،
به‌علاوهٔ پچ رنگ swatch هر محصول، همه در یک فایل PNG کنار هم.

اجرا (از داخل پوشهٔ اصلی پروژه):
    python preview_catalog.py face_sample.jpg

اگه مسیر عکس رو ندی، دنبال face_sample.jpg در پوشهٔ همین اسکریپت می‌گرده.
خروجی: preview_result.png (در همون پوشه)

🔧 FIX (باگ «عکس پیدا نشد»): قبلاً face_path یک مسیر نسبی خام بود که با
os.path.exists نسبت به working directory فعلی ترمینال چک می‌شد، نه
نسبت به پوشه‌ای که خود preview_catalog.py توشه. یعنی اگه از یه پوشهٔ
دیگه (مثلاً از داخل app/) اسکریپت رو اجرا می‌کردی، حتی اگه عکس دقیقاً
کنار خود این فایل بود، پیدا نمی‌شد. حالا face_path هم مثل CATALOG_PATH
نسبت به مسیر خود اسکریپت resolve می‌شه (مگر این‌که مسیر مطلق داده باشی).

🔧 CHANGE دیگه: استفاده از get_lip_contours (به‌جای get_lip_landmarks
قدیمی) چون build_lip_mask دیگه به دو کانتور مرتب (بیرونی/داخلی) نیاز
داره، نه یک لیست نامرتب از نقاط.
"""

import json
import os
import sys

import cv2
import numpy as np

from app.core.face_landmarks import get_lip_contours, build_lip_mask
from app.core.color_lab import apply_color_to_masked_region
from app.core.color_extract import lab_to_rgb_preview

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(SCRIPT_DIR, "products.json")
OUT_PATH = os.path.join(SCRIPT_DIR, "preview_result.png")

CELL_W = 260
CELL_H = 320
LABEL_H = 40
SWATCH_H = 40


def _load_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _make_cell(img, label, swatch_rgb=None):
    """یک خونهٔ گرید می‌سازه: پچ رنگ (اختیاری) + عکس + برچسب زیرش."""
    resized = cv2.resize(img, (CELL_W, CELL_H - LABEL_H - (SWATCH_H if swatch_rgb else 0)))

    parts = []
    if swatch_rgb is not None:
        swatch = np.zeros((SWATCH_H, CELL_W, 3), dtype=np.uint8)
        swatch[:, :] = (swatch_rgb[2], swatch_rgb[1], swatch_rgb[0])  # RGB -> BGR
        parts.append(swatch)

    parts.append(resized)

    label_bar = np.full((LABEL_H, CELL_W, 3), 255, dtype=np.uint8)
    cv2.putText(
        label_bar, label, (8, 27), cv2.FONT_HERSHEY_SIMPLEX,
        0.55, (0, 0, 0), 1, cv2.LINE_AA,
    )
    parts.append(label_bar)

    return np.vstack(parts)


def main():
    face_arg = sys.argv[1] if len(sys.argv) > 1 else "face_sample.jpg"
    # اگه مسیر مطلق نبود، نسبت به پوشهٔ خودِ این اسکریپت resolve کن،
    # نه نسبت به working directory فعلی ترمینال.
    face_path = face_arg if os.path.isabs(face_arg) else os.path.join(SCRIPT_DIR, face_arg)

    if not os.path.exists(face_path):
        print(f"❌ عکس چهره پیدا نشد: {face_path}")
        print("   یک عکس frontal با نور یکنواخت بذار یا مسیرش رو به اسکریپت بده:")
        print("   python preview_catalog.py path/to/face.jpg")
        sys.exit(1)

    img = cv2.imread(face_path)
    if img is None:
        print(f"❌ فایل عکس معتبر نیست: {face_path}")
        sys.exit(1)

    contours = get_lip_contours(img)
    if contours is None:
        print("❌ چهره‌ای در عکس تشخیص داده نشد (مدیاپایپ لندمارک لب پیدا نکرد).")
        sys.exit(1)

    mask = build_lip_mask(img.shape, contours, feather_px=4)

    products = _load_catalog()
    if not products:
        print(f"❌ کاتالوگ خالیه یا پیدا نشد: {CATALOG_PATH}")
        sys.exit(1)

    cells = [_make_cell(img, "Original")]

    for p in products:
        result = apply_color_to_masked_region(img, mask, p["lab"])
        swatch_rgb = lab_to_rgb_preview(p["lab"]["l"], p["lab"]["a"], p["lab"]["b"])
        label = f"{p['name']} (id={p['id']})"
        cells.append(_make_cell(result, label, swatch_rgb=swatch_rgb))

    grid = np.hstack(cells)
    cv2.imwrite(OUT_PATH, grid)
    print(f"✅ ذخیره شد: {OUT_PATH}")
    print(f"   {len(products)} محصول + عکس اصلی، کنار هم مقایسه شدن.")


if __name__ == "__main__":
    main()
