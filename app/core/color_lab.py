"""
منطق تبدیل و ترکیب رنگ در فضای Lab برای اعمال رژ روی لب.

ایدهٔ اصلی: کانال L (روشنایی/بافت/سایه‌روشن طبیعی لب) دست‌نخورده می‌ماند؛
فقط کانال‌های a و b (اطلاعات رنگی) در محدودهٔ ماسک با رنگ محصول
جایگزین/ترکیب می‌شوند. این باعث می‌شود نتیجه طبیعی به نظر برسد،
نه یک رنگ تخت مصنوعی.
"""

import cv2
import numpy as np


def apply_color_to_masked_region(image_bgr, mask, target_lab, blend_ratio=0.75):
    """
    image_bgr: تصویر ورودی (BGR, numpy array)
    mask: ماسک فازی ناحیهٔ لب (همان اندازهٔ تصویر، مقادیر float بین ۰ و ۱)
    target_lab: دیکشنری {"l":.., "a":.., "b":..} رنگ محصول (بازهٔ استاندارد Lab)
    blend_ratio: چقدر از رنگ محصول در برابر رنگ اصلی لب غالب باشد (۰ تا ۱)
                 مثلاً ۰.۷۵ یعنی ۷۵٪ رنگ محصول + ۲۵٪ رنگ طبیعی لب

    خروجی: تصویر نهایی BGR با رنگ اعمال‌شده
    """
    img_lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    # تبدیل کانال‌های OpenCV (بازهٔ 0-255) به بازهٔ استاندارد Lab
    l_ch = img_lab[:, :, 0] * (100.0 / 255.0)
    a_ch = img_lab[:, :, 1] - 128.0
    b_ch = img_lab[:, :, 2] - 128.0

    # ترکیب: در هر پیکسل، به نسبت (mask * blend_ratio) به‌سمت رنگ محصول می‌رویم
    alpha = mask * blend_ratio  # مقدار نهایی وزن رنگ محصول در هر پیکسل

    new_a = a_ch * (1 - alpha) + target_lab["a"] * alpha
    new_b = b_ch * (1 - alpha) + target_lab["b"] * alpha
    # کانال L دست‌نخورده می‌ماند تا بافت/نور طبیعی لب حفظ شود
    new_l = l_ch

    # بازگرداندن به بازهٔ OpenCV (0-255) برای بازسازی تصویر
    out_lab = np.stack([
        new_l * (255.0 / 100.0),
        new_a + 128.0,
        new_b + 128.0,
    ], axis=-1)
    out_lab = np.clip(out_lab, 0, 255).astype(np.uint8)

    result_bgr = cv2.cvtColor(out_lab, cv2.COLOR_LAB2BGR)
    return result_bgr
