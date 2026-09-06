"""
استخراج رنگ غالب رژ لب از عکس سواچ (لکه‌ی رنگ روی دست/مچ/ساعد).
...(همون توضیحات قبلی)...
"""

import cv2
import math
import numpy as np
from sklearn.cluster import KMeans

LIPSTICK_HUE_MIN_DEG = -50
LIPSTICK_HUE_MAX_DEG = 60


def extract_dominant_swatch_color(image_path: str, k: int = 5,
                                   min_cluster_fraction: float = 0.03,
                                   top_vivid_fraction: float = 0.08):
    """
    top_vivid_fraction: به‌جای میانگین کل خوشه‌ی برنده، فقط از پررنگ‌ترین
    این درصد پیکسل‌های همون خوشه میانگین می‌گیریم. چون لبه‌های سواچ همیشه
    محوتر/رقیق‌تر از مرکز رژ هستن، میانگینِ کل خوشه رنگ رو کدرتر از
    واقعیت نشون می‌داد.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"نتوانستم عکس را بخوانم: {image_path}")

    h, w = img_bgr.shape[:2]
    scale = 300 / max(h, w)
    if scale < 1:
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))

    img_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
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
        idx_mask = labels == i
        count = np.sum(idx_mask)
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
            "_pixel_mask": idx_mask,  # فقط داخلی، در خروجی نهایی حذف می‌شه
        })

    valid_clusters = [c for c in clusters_info if c["fraction"] >= min_cluster_fraction]
    if not valid_clusters:
        valid_clusters = clusters_info

    hue_filtered = [
        c for c in valid_clusters
        if LIPSTICK_HUE_MIN_DEG <= c["hue_deg"] <= LIPSTICK_HUE_MAX_DEG
    ]
    if not hue_filtered:
        hue_filtered = valid_clusters

    swatch_cluster = max(hue_filtered, key=lambda c: c["chroma"])

    # --- بخش جدید: به‌جای مرکز خوشه، پررنگ‌ترین زیرمجموعه‌ی همون خوشه ---
    cluster_pixels = pixels[swatch_cluster["_pixel_mask"]]
    cl, ca, cb = cluster_pixels[:, 0], cluster_pixels[:, 1], cluster_pixels[:, 2]
    cluster_chroma = np.sqrt(ca ** 2 + cb ** 2)
    n_top = max(1, int(len(cluster_chroma) * top_vivid_fraction))
    top_idx = np.argsort(-cluster_chroma)[:n_top]

    vivid_lab = {
        "l": float(cl[top_idx].mean()),
        "a": float(ca[top_idx].mean()),
        "b": float(cb[top_idx].mean()),
    }
    # ---------------------------------------------------------------

    for c in clusters_info:
        del c["_pixel_mask"]

    return {
        "swatch_lab": vivid_lab,
        "swatch_fraction": swatch_cluster["fraction"],
        "all_clusters": sorted(clusters_info, key=lambda c: -c["chroma"]),
    }


def lab_to_rgb_preview(l, a, b):
    lab_pixel = np.array([[[l * 255.0 / 100.0, a + 128.0, b + 128.0]]], dtype=np.uint8)
    rgb_pixel = cv2.cvtColor(lab_pixel, cv2.COLOR_LAB2RGB)
    return tuple(int(x) for x in rgb_pixel[0, 0])