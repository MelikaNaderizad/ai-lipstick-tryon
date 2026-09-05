"""
منطق تبدیل و ترکیب رنگ در فضای Lab برای اعمال رژ روی لب.

ایدهٔ اصلی: کانال L (روشنایی/بافت/سایه‌روشن طبیعی لب) دست‌نخورده می‌ماند؛
فقط کانال‌های a و b (اطلاعات رنگی) در محدودهٔ ماسک با رنگ محصول
جایگزین/ترکیب می‌شوند. این باعث می‌شود نتیجه طبیعی به نظر برسد،
نه یک رنگ تخت مصنوعی.
"""

import cv2
import numpy as np


def apply_color_to_masked_region(image_bgr, mask, target_lab, blend_ratio=0.9, l_blend_ratio=0.35):
    img_lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_ch = img_lab[:, :, 0] * (100.0 / 255.0)
    a_ch = img_lab[:, :, 1] - 128.0
    b_ch = img_lab[:, :, 2] - 128.0

    alpha = mask * blend_ratio
    new_a = a_ch * (1 - alpha) + target_lab["a"] * alpha
    new_b = b_ch * (1 - alpha) + target_lab["b"] * alpha

    # به‌جای دست‌نخورده گذاشتن کامل L، فقط بخشی از فاصله تا L محصول رو می‌پیمایم
    # (l_blend_ratio پایین = بافت/براقی طبیعی لب بیشتر حفظ می‌شه)
    l_alpha = mask * blend_ratio * l_blend_ratio
    new_l = l_ch * (1 - l_alpha) + target_lab["l"] * l_alpha

    out_lab = np.stack([
        new_l * (255.0 / 100.0),
        new_a + 128.0,
        new_b + 128.0,
    ], axis=-1)
    out_lab = np.clip(out_lab, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out_lab, cv2.COLOR_LAB2BGR)
