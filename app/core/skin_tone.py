"""
تحلیل تن پوست و پیشنهاد محصول بر اساس آندرتون.

⚠️ محدودیت مهم: تشخیص آندرتون اینجا یه heuristic ساده بر پایه‌ی
فضای رنگی Lab هست، نه یه روش علمی/کلینیکی معتبر. تحت تأثیر نور محیط،
تنظیمات دوربین، و کیفیت عکس قرار می‌گیره. برای MVP کافیه، ولی نباید
به‌عنوان تشخیص دقیق پوست‌شناسی تلقی بشه.

نکته‌ی طراحی مهم: پوست و رژ لب دو "جنس رنگ" متفاوتن و نمی‌شه یه فرمول
واحد برای هردو استفاده کرد:
  - پوست: کانال a (قرمزی) کوچیکه، بنابراین نسبت b/a معیار خوبیه.
  - رژ لب: کانال a همیشه بزرگه (پیگمنت غلیظ قرمز/صورتی)، پس نسبت b/a
    گمراه‌کننده می‌شه؛ به‌جاش از زاویه‌ی رنگ (hue) استفاده می‌کنیم.
به همین دلیل دو تابع طبقه‌بندی جدا داریم: classify_skin_undertone و
classify_lipstick_undertone.
"""

import math

import cv2
import numpy as np

from app.core.face_landmarks import get_cheek_forehead_landmarks

# --- آستانه‌های تشخیص آندرتون پوست (بر پایه‌ی نسبت b/a) ---
SKIN_WARM_RATIO = 1.2   # b/a بالاتر از این => warm
SKIN_COOL_RATIO = 0.8   # b/a پایین‌تر از این => cool

# --- آستانه‌های تشخیص آندرتون رژ لب (بر پایه‌ی زاویه‌ی رنگ hue) ---
# نکته: این دو عدد فقط یه حدس منطقی بر پایه‌ی چند نمونه‌ی اولیه‌ست.
# وقتی کاتالوگ واقعی (چند ده محصول) آماده شد، بهتره بر اساس توزیع
# واقعی رنگ‌ها دوباره کالیبره بشن.
LIPSTICK_WARM_HUE_DEG = 25.0
LIPSTICK_COOL_HUE_DEG = 15.0

# اگه تعداد محصولات هم‌آندرتون کمتر از این بود، از neutral هم قرض می‌گیریم
MIN_MATCHES_BEFORE_FALLBACK = 3


def _sample_patch_lab(image_bgr, point, patch_size=15):
    """میانگین رنگ Lab یه پچ کوچیک دور یه نقطه‌ی مشخص (نه فقط یه پیکسل تنها)."""
    h, w = image_bgr.shape[:2]
    x, y = point
    half = patch_size // 2

    x0, x1 = max(0, x - half), min(w, x + half + 1)
    y0, y1 = max(0, y - half), min(h, y + half + 1)

    patch = image_bgr[y0:y1, x0:x1]
    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB).astype(np.float32)

    l = lab[:, :, 0].mean() * (100.0 / 255.0)
    a = lab[:, :, 1].mean() - 128.0
    b = lab[:, :, 2].mean() - 128.0
    return l, a, b


def classify_skin_undertone(a: float, b: float) -> str:
    """طبقه‌بندی warm/cool/neutral برای رنگ پوست، بر اساس نسبت b به a."""
    if a == 0:
        return "neutral"
    ratio = b / a
    if ratio >= SKIN_WARM_RATIO:
        return "warm"
    if ratio <= SKIN_COOL_RATIO:
        return "cool"
    return "neutral"


def classify_lipstick_undertone(a: float, b: float) -> str:
    """طبقه‌بندی warm/cool/neutral برای رنگ رژ لب، بر اساس زاویه‌ی رنگ (hue)."""
    hue = math.degrees(math.atan2(b, a))
    if hue >= LIPSTICK_WARM_HUE_DEG:
        return "warm"
    if hue <= LIPSTICK_COOL_HUE_DEG:
        return "cool"
    return "neutral"


def compute_delta_e(lab1: dict, lab2: dict) -> float:
    """فاصله‌ی رنگی ساده (Euclidean) در فضای Lab بین دو رنگ."""
    return float(np.sqrt(
        (lab1["l"] - lab2["l"]) ** 2 +
        (lab1["a"] - lab2["a"]) ** 2 +
        (lab1["b"] - lab2["b"]) ** 2
    ))


def analyze_skin_tone(image_bgr, products: list) -> dict:
    """
    ورودی:
        image_bgr: عکس چهره (BGR، همون خروجی cv2.imread)
        products: لیست محصولات کاتالوگ، هرکدوم دیکشنری با کلیدهای
                  id, name, lab (و اختیاری brand, swatch_image_path)
    خروجی:
        دیکشنری شامل undertone, skin_lab, top_matches
        اگه چهره‌ای در عکس پیدا نشه، None برمی‌گردونه.
    """
    landmarks = get_cheek_forehead_landmarks(image_bgr)
    if landmarks is None:
        return None

    # از سه ناحیه (گونه‌ی چپ، گونه‌ی راست، پیشانی) نمونه می‌گیریم و میانگین می‌کنیم
    all_points = (
        landmarks["left_cheek"] + landmarks["right_cheek"] + landmarks["forehead"]
    )
    samples = [_sample_patch_lab(image_bgr, p) for p in all_points]
    l_avg = float(np.mean([s[0] for s in samples]))
    a_avg = float(np.mean([s[1] for s in samples]))
    b_avg = float(np.mean([s[2] for s in samples]))

    skin_lab = {"l": l_avg, "a": a_avg, "b": b_avg}
    undertone = classify_skin_undertone(a_avg, b_avg)

    # به هر محصول یه آندرتون نسبت می‌دیم (با منطق مخصوص رژ لب) و فاصله‌ی رنگی حساب می‌کنیم
    scored = []
    for p in products:
        p_undertone = classify_lipstick_undertone(p["lab"]["a"], p["lab"]["b"])
        delta_e = compute_delta_e(skin_lab, p["lab"])
        scored.append({**p, "_undertone": p_undertone, "delta_e": delta_e})

    # اول فقط هم‌آندرتون‌ها
    matches = [p for p in scored if p["_undertone"] == undertone]

    # اگه کافی نبود، neutral رو هم قرض بگیر (اگه خودِ کاربر neutral نبود)
    if len(matches) < MIN_MATCHES_BEFORE_FALLBACK and undertone != "neutral":
        neutral_extra = [p for p in scored if p["_undertone"] == "neutral"]
        matches += neutral_extra

    matches.sort(key=lambda p: p["delta_e"])

    top_matches = [
        {"product_id": p["id"], "name": p["name"], "delta_e": round(p["delta_e"], 2)}
        for p in matches[:3]
    ]

    return {
        "undertone": undertone,
        "skin_lab": skin_lab,
        "top_matches": top_matches,
    }