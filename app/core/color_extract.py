"""
استخراج رنگ غالب رژ لب از عکس سواچ (لکه‌ی رنگ روی دست/مچ/ساعد).

چون سواچ همیشه دقیقاً وسط عکس نیست (فروشنده ممکنه از زوایای مختلف عکس بگیره)،
به‌جای کراپ کردن ناحیه مرکزی، کل عکس رو با k-means خوشه‌بندی می‌کنیم و
خوشه‌ای که «رنگی‌ترین» (بیشترین chroma) و در بازهٔ رنگی رژ لب هست رو به‌عنوان
رنگ سواچ انتخاب می‌کنیم. این کد روی ۳ عکس واقعی تست و تأیید شده است.
"""

import cv2
import math
import numpy as np
from sklearn.cluster import KMeans

# رژهای لب (قرمز، صورتی، کورال، بری، ماوی، نود) همیشه در یک بازهٔ زاویهٔ رنگی
# مشخص در فضای a-b قرار می‌گیرند. رنگ‌های خیلی دور از این بازه (زرد، سبز،
# آبی، بنفش تیره) معمولاً پوشاک/پس‌زمینه هستند نه رژ لب.
LIPSTICK_HUE_MIN_DEG = -50   # سمت بری/مویی تیره
LIPSTICK_HUE_MAX_DEG = 60    # سمت کورال/نارنجی


def extract_dominant_swatch_color(image_path: str, k: int = 5, min_cluster_fraction: float = 0.03):
    """
    ورودی: مسیر عکس سواچ
    خروجی: دیکشنری شامل رنگ Lab غالب سواچ + اطلاعات دیباگ همه‌ی خوشه‌ها

    min_cluster_fraction: خوشه‌هایی که سهمشون از کل پیکسل‌ها کمتر از این باشه
    (مثلاً نویز لبه یا انعکاس نور) نادیده گرفته می‌شن.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"نتوانستم عکس را بخوانم: {image_path}")

    # کوچک کردن عکس برای سرعت بیشتر k-means (کیفیت رنگ تغییری نمی‌کند)
    h, w = img_bgr.shape[:2]
    scale = 300 / max(h, w)
    if scale < 1:
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))

    # تبدیل به فضای رنگی Lab (همان فضایی که در کل پروژه استفاده می‌کنیم)
    img_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    # OpenCV مقادیر Lab را در بازه‌ی 0-255 ذخیره می‌کند؛ به بازه‌ی استاندارد
    # L: 0-100, a: -128..127, b: -128..127 تبدیل می‌کنیم تا محاسبات درست باشند.
    l_ch = img_lab[:, :, 0] * (100.0 / 255.0)
    a_ch = img_lab[:, :, 1] - 128.0
    b_ch = img_lab[:, :, 2] - 128.0

    pixels = np.stack([l_ch, a_ch, b_ch], axis=-1).reshape(-1, 3)

    kmeans = KMeans(n_clusters=k, n_init=4, random_state=42)
    labels = kmeans.fit_predict(pixels)
    centers = kmeans.cluster_centers_

    total_pixels = len(labels)
    clusters_info = []
    for i in range(k):
        count = np.sum(labels == i)
        fraction = count / total_pixels
        l, a, b = centers[i]
        chroma = np.sqrt(a ** 2 + b ** 2)
        hue_deg = math.degrees(math.atan2(b, a))
        clusters_info.append({
            "cluster_id": int(i),
            "fraction": float(fraction),
            "lab": {"l": float(l), "a": float(a), "b": float(b)},
            "chroma": float(chroma),
            "hue_deg": float(hue_deg),
        })

    # فیلتر ۱: خوشه‌های خیلی کوچک (نویز لبه/انعکاس نور) را نادیده بگیر
    valid_clusters = [c for c in clusters_info if c["fraction"] >= min_cluster_fraction]
    if not valid_clusters:
        valid_clusters = clusters_info

    # فیلتر ۲: فقط خوشه‌هایی که در بازهٔ رنگی معمول رژ لب هستند را نگه دار
    # (این فیلتر جلوی انتخاب اشتباه رنگ لباس/پس‌زمینه به‌جای رژ را می‌گیرد)
    hue_filtered = [
        c for c in valid_clusters
        if LIPSTICK_HUE_MIN_DEG <= c["hue_deg"] <= LIPSTICK_HUE_MAX_DEG
    ]
    if not hue_filtered:
        hue_filtered = valid_clusters

    swatch_cluster = max(hue_filtered, key=lambda c: c["chroma"])

    return {
        "swatch_lab": swatch_cluster["lab"],
        "swatch_fraction": swatch_cluster["fraction"],
        "all_clusters": sorted(clusters_info, key=lambda c: -c["chroma"]),
    }


def lab_to_rgb_preview(l, a, b):
    """فقط برای دیباگ: یک رنگ Lab را به RGB قابل‌نمایش تبدیل می‌کند."""
    lab_pixel = np.array([[[l * 255.0 / 100.0, a + 128.0, b + 128.0]]], dtype=np.uint8)
    rgb_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2RGB)
    return tuple(int(x) for x in rgb_pixel[0, 0])


if __name__ == "__main__":
    import sys
    import json

    result = extract_dominant_swatch_color(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
