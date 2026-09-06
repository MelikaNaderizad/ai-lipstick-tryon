"""
منطق تبدیل و ترکیب رنگ در فضای Lab برای اعمال رژ روی لب.

🔧 FIX: مقادیر پیش‌فرض blend_ratio و l_blend_ratio بالا برده شدن
(۰.۷۵→۰.۹۵ و ۰.۳۵→۰.۶). با مقادیر قبلی، حتی بعد از تصحیح استخراج رنگ،
نتیجه هنوز کمی "لایه‌ی نازک روی رنگ طبیعی لب" به نظر می‌رسید، نه پوشش
کامل شبیه رژ واقعی. با این مقادیر جدید، پوشش کامل‌تر و مات‌تر می‌شه ولی
هنوز کاملاً صاف/مصنوعی نیست (چون l_blend_ratio هنوز ۱ نیست و کمی از
بافت/روشنایی طبیعی لب حفظ می‌شه).
"""

import cv2
import numpy as np


def apply_color_to_masked_region(image_bgr, mask, target_lab,
                                  blend_ratio=0.95, l_blend_ratio=0.6):
    """
    blend_ratio: سهم رنگ محصول (کانال‌های a/b) در ترکیب با رنگ طبیعی لب.
    l_blend_ratio: چقدر از فاصله‌ی روشنایی طبیعی لب تا روشنایی رنگ محصول
    طی بشه (۰ = کانال L کاملاً دست‌نخورده، ۱ = کاملاً جایگزین بشه).
    مقدار بالاتر (۰.۶) نسبت به قبل (۰.۳۵) باعث می‌شه پوشش به رژ واقعی
    (مات و کامل) نزدیک‌تر باشه، درعین‌حال کمی بافت طبیعی لب حفظ بشه.
    """
    img_lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_ch = img_lab[:, :, 0] * (100.0 / 255.0)
    a_ch = img_lab[:, :, 1] - 128.0
    b_ch = img_lab[:, :, 2] - 128.0

    alpha = mask * blend_ratio
    new_a = a_ch * (1 - alpha) + target_lab["a"] * alpha
    new_b = b_ch * (1 - alpha) + target_lab["b"] * alpha

    l_alpha = mask * blend_ratio * l_blend_ratio
    new_l = l_ch * (1 - l_alpha) + target_lab["l"] * l_alpha

    out_lab = np.stack([
        new_l * (255.0 / 100.0),
        new_a + 128.0,
        new_b + 128.0,
    ], axis=-1)
    out_lab = np.clip(out_lab, 0, 255).astype(np.uint8)

    result_bgr = cv2.cvtColor(out_lab, cv2.COLOR_LAB2BGR)
    return result_bgr
