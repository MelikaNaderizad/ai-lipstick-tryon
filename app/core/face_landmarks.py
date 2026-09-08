"""
تشخیص لندمارک‌های صورت با MediaPipe Face Mesh و ساخت ماسک دقیق لب.

نکتهٔ مهم نصب: باید نسخهٔ 0.10.13 نصب شود (نسخه‌های 0.10.30+ دیگر
شامل API قدیمی mp.solutions نمی‌شوند):
    pip install mediapipe==0.10.13

🔧 CHANGE (کیفیت ماسک لب): قبلاً یک convex hull ساده روی مجموعه‌ی
نامرتب نقاط لب کشیده می‌شد (FACEMESH_LIPS به‌صورت set، بدون ترتیب).
این باعث دو مشکل بود:
  ۱) گوشه‌های لب گم می‌شد و مسک به‌جای شکل واقعی لب، یک بیضی/چندضلعی
     کدر و غیرطبیعی می‌شد.
  ۲) چون convex hull هست، اگر دهان کمی باز بود داخل دهان (دندان/زبان)
     هم پر از رنگ می‌شد.

حالا از دو کانتور بستهٔ *مرتب* استفاده می‌کنیم — کانتور بیرونی لب و
کانتور داخلی (مرز دهان) — دقیقاً همون منطقی که در static/live_tryon.html
(نسخهٔ جاوااسکریپت لایو) از قبل جواب داده بود؛ این‌جا معادل
سروری/پایتونی‌ش اضافه شده تا کیفیت عکس استاتیک هم به همون سطح برسه.
"""

import cv2
import numpy as np
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

# ترتیب این دو لیست مهمه: باید دورتادور لب رو به‌ترتیب (نه نامرتب) بپیمایند.
# همون اندیس‌هایی که در static/live_tryon.html استفاده شدن (بر پایه‌ی
# توپولوژی استاندارد ۴۶۸ نقطه‌ای FaceMesh — بین نسخه‌ی پایتونی و
# جاوااسکریپتی مدیاپایپ مشترکه، پس عیناً قابل استفاده‌ست).
_LIP_OUTER_IDX = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
_LIP_INNER_IDX = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]

# نقاط تقریبی گونهٔ چپ/راست و پیشانی (فاز ۴ - تحلیل تن پوست). بدون تغییر.
_CHEEK_LEFT_IDX = [50]
_CHEEK_RIGHT_IDX = [280]
_FOREHEAD_IDX = [151]


def _run_face_mesh(image_bgr):
    with mp_face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1, refine_landmarks=True
    ) as face_mesh:
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return None
        return results.multi_face_landmarks[0]


def get_lip_contours(image_bgr):
    """
    ورودی: تصویر BGR (خروجی cv2.imread)
    خروجی: دیکشنری {"outer": [...], "inner": [...]}‌ — هرکدوم لیست نقاط
    (x, y) پیکسلی، *به‌ترتیب* دور لب (نه یک مجموعه‌ی نامرتب مثل قبل).
    اگر چهره‌ای تشخیص داده نشود، None برمی‌گرداند.
    """
    landmarks = _run_face_mesh(image_bgr)
    if landmarks is None:
        return None

    h, w = image_bgr.shape[:2]

    def _to_px(idx_list):
        return [(int(landmarks.landmark[i].x * w), int(landmarks.landmark[i].y * h)) for i in idx_list]

    return {
        "outer": _to_px(_LIP_OUTER_IDX),
        "inner": _to_px(_LIP_INNER_IDX),
    }


def get_cheek_forehead_landmarks(image_bgr):
    """(بدون تغییر) برای فاز ۴ - تحلیل تن پوست."""
    landmarks = _run_face_mesh(image_bgr)
    if landmarks is None:
        return None

    h, w = image_bgr.shape[:2]

    def _to_px(idx_list):
        return [(int(landmarks.landmark[i].x * w), int(landmarks.landmark[i].y * h)) for i in idx_list]

    return {
        "left_cheek": _to_px(_CHEEK_LEFT_IDX),
        "right_cheek": _to_px(_CHEEK_RIGHT_IDX),
        "forehead": _to_px(_FOREHEAD_IDX),
    }


def build_lip_mask(image_shape, contours, feather_px=4):
    """
    ورودی:
        image_shape: (h, w) یا (h, w, c) تصویر اصلی
        contours: خروجی get_lip_contours — دیکشنری با کلیدهای outer/inner
        feather_px: میزان بلور لبه‌ی ماسک (برای مرز طبیعی‌تر)
    خروجی: ماسک float32 با مقادیر ۰ تا ۱، هم‌اندازه‌ی تصویر اصلی.

    منطق: ابتدا کانتور بیرونی به‌صورت کامل پر می‌شود، سپس کانتور داخلی
    (مرز دهان) از آن کم می‌شود — یعنی اگر دهان باز باشد، داخلش
    (دندان/زبان) رنگی نمی‌شود. این همون منطق evenodd نسخهٔ جاوااسکریپته.
    """
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    outer = np.array(contours["outer"], dtype=np.int32)
    inner = np.array(contours["inner"], dtype=np.int32)

    cv2.fillPoly(mask, [outer], 255)
    cv2.fillPoly(mask, [inner], 0)

    if feather_px > 0:
        mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=feather_px)

    return mask.astype(np.float32) / 255.0


# --- سازگاری با کد قدیمی، اگه جای دیگه‌ای صدا زده می‌شد ---
# ⚠️ منسوخ: به‌جاش از get_lip_contours + build_lip_mask جدید استفاده کن.
def get_lip_landmarks(image_bgr):
    contours = get_lip_contours(image_bgr)
    if contours is None:
        return None
    return contours["outer"] + contours["inner"]
