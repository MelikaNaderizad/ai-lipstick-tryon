"""
پیش‌نمایش سریع: نتیجهٔ اعمال رژ همهٔ محصولات کاتالوگ روی یک عکس چهره،
به‌علاوهٔ پچ رنگ swatch هر محصول، همه در یک فایل PNG کنار هم.

چرا این اسکریپت؟
    endpoint اصلی (/apply-lipstick) برای هر محصول یک PNG جدا برمی‌گردونه،
    پس مقایسهٔ چند محصول با هم روی Swagger سخته. این اسکریپت یک‌جا
    نتیجهٔ همه رو کنار هم می‌چینه تا سریع ببینی مدل چطور کار می‌کنه.

اجرا (از داخل پوشهٔ اصلی پروژه، یعنی همون جایی که app/ و products.json هستن):
    python preview_catalog.py face_sample.jpg

اگه مسیر عکس رو ندی، دنبال face_sample.jpg در پوشهٔ فعلی می‌گرده.
خروجی: preview_result.png (در همون پوشه)
"""

import json
import os
import sys

import cv2
import numpy as np

from app.core.face_landmarks import get_lip_landmarks, build_lip_mask
from app.core.color_lab import apply_color_to_masked_region
from app.core.color_extract import lab_to_rgb_preview

CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.json")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_result.png")

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
        # لب Rgb -> BGR برای opencv
        swatch[:, :] = (swatch_rgb[2], swatch_rgb[1], swatch_rgb[0])
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
    face_path = sys.argv[1] if len(sys.argv) > 1 else "face_sample.jpg"

    if not os.path.exists(face_path):
        print(f"❌ عکس چهره پیدا نشد: {face_path}")
        print("   یک عکس frontal با نور یکنواخت بذار یا مسیرش رو به اسکریپت بده:")
        print("   python preview_catalog.py path/to/face.jpg")
        sys.exit(1)

    img = cv2.imread(face_path)
    if img is None:
        print(f"❌ فایل عکس معتبر نیست: {face_path}")
        sys.exit(1)

    landmarks = get_lip_landmarks(img)
    if landmarks is None:
        print("❌ چهره‌ای در عکس تشخیص داده نشد (مدیاپایپ لندمارک لب پیدا نکرد).")
        sys.exit(1)

    mask = build_lip_mask(img.shape, landmarks, feather_px=4)

    products = _load_catalog()
    if not products:
        print(f"❌ کاتالوگ خالیه یا پیدا نشد: {CATALOG_PATH}")
        sys.exit(1)

    cells = [_make_cell(img, "Original")]

    for p in products:
        result = apply_color_to_masked_region(img, mask, p["lab"], blend_ratio=0.75)
        swatch_rgb = lab_to_rgb_preview(p["lab"]["l"], p["lab"]["a"], p["lab"]["b"])
        label = f"{p['name']} (id={p['id']})"
        cells.append(_make_cell(result, label, swatch_rgb=swatch_rgb))

    grid = np.hstack(cells)
    cv2.imwrite(OUT_PATH, grid)
    print(f"✅ ذخیره شد: {OUT_PATH}")
    print(f"   {len(products)} محصول + عکس اصلی، کنار هم مقایسه شدن.")


if __name__ == "__main__":
    main()
