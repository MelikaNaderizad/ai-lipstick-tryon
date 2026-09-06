"""
منطق تبدیل و ترکیب رنگ در فضای Lab برای اعمال رژ روی لب.
...(همون توضیحات قبلی)...
"""

import cv2
import numpy as np


def apply_color_to_masked_region(image_bgr, mask, target_lab,
                                  blend_ratio=0.9, l_blend_ratio=0.35):
    """
    l_blend_ratio: چقدر از فاصله‌ی روشنایی طبیعی لب تا روشنایی رنگ محصول
    طی بشه (۰ = کانال L کاملاً دست‌نخورده، ۱ = کاملاً جایگزین بشه).
    مقدار پایین (۰.۳۵) باعث می‌شه هم بافت/براقی طبیعی لب حفظ بشه،
    هم لب بیش‌ازحد روشن/کم‌رنگ به نظر نرسه.
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