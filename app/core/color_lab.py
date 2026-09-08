"""
منطق تبدیل و ترکیب رنگ در فضای Lab برای اعمال رژ روی لب.

🔧 CHANGE (کیفیت رنگ‌آمیزی): l_blend_ratio پیش‌فرض از 0.6 به 0.25 برگشت.

دلیل: با 0.6، بخش زیادی از کانال L (روشنایی طبیعی لب — یعنی های‌لایت‌ها
و بافت) با روشنایی ثابتِ رنگ محصول جایگزین می‌شد و نتیجه "تخت" و مصنوعی
به نظر می‌رسید. این یکی از منابع اصلی افت کیفیتی بود که حس می‌شد.

با 0.25: کانال‌های a/b (که هیو و کروما رو تعیین می‌کنن، یعنی خودِ "رنگ
رژ") همچنان قوی جایگزین می‌شن (blend_ratio بالا می‌مونه)، ولی روشنایی
طبیعی لب (های‌لایت/سایه/بافت) عمدتاً حفظ می‌شه. این دقیقاً همون ایده‌ای
که در نسخهٔ جاوااسکریپت (static/live_tryon.html) با blend mode
"color" پیاده شده: فقط رنگ منتقل می‌شه، روشنایی دست‌نخورده می‌مونه.

اگه پوشش مات‌تر/بیشتر (شبیه رژ مات واقعی) خواستی، l_blend_ratio رو
دستی بین ۰.۳۵ تا ۰.۵ امتحان کن؛ فقط پیشنهاد می‌کنم دیگه به ۰.۶ برنگردی،
چون اونجا بود که تخت به نظر می‌رسید.
"""

import cv2
import numpy as np


def apply_color_to_masked_region(image_bgr, mask, target_lab,
                                  blend_ratio=0.95, l_blend_ratio=0.25):
    """
    blend_ratio: سهم رنگ محصول (کانال‌های a/b) در ترکیب با رنگ طبیعی لب.
    l_blend_ratio: چقدر از فاصله‌ی روشنایی طبیعی لب تا روشنایی رنگ محصول
    طی بشه (۰ = کانال L کاملاً دست‌نخورده، ۱ = کاملاً جایگزین بشه).
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
