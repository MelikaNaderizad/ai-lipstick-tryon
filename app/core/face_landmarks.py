"""
تشخیص لندمارک‌های صورت با MediaPipe Face Mesh و ساخت ماسک لب.

نکتهٔ مهم نصب: باید نسخهٔ 0.10.13 نصب شود (نسخه‌های 0.10.30+ دیگر
شامل API قدیمی mp.solutions نمی‌شوند و نیاز به دانلود مدل جدا دارند):
    pip install mediapipe==0.10.13
"""

import cv2
import numpy as np
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

# اندیس تمام نقاط مرتبط با لب (داخلی + خارجی) طبق FACEMESH_LIPS مدیاپایپ
_LIP_INDICES = sorted({idx for pair in mp_face_mesh.FACEMESH_LIPS for idx in pair})

# نقاط تقریبی گونهٔ چپ/راست و پیشانی (برای فاز ۴ - تحلیل تن پوست)
# این‌ها اندیس‌های استاندارد و مستند مدیاپایپ برای نواحی مسطح صورت هستند
# که کمترین احتمال همپوشانی با سایه/مو/چشم را دارند.
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


def get_lip_landmarks(image_bgr):
    """
    ورودی: تصویر BGR (numpy array، همان چیزی که cv2.imread برمی‌گرداند)
    خروجی: لیستی از نقاط (x, y) به پیکسل، مربوط به مرز لب
    اگر چهره‌ای تشخیص داده نشود، None برمی‌گرداند.
    """
    landmarks = _run_face_mesh(image_bgr)
    if landmarks is None:
        return None

    h, w = image_bgr.shape[:2]
    points = []
    for idx in _LIP_INDICES:
        lm = landmarks.landmark[idx]
        points.append((int(lm.x * w), int(lm.y * h)))
    return points


def get_cheek_forehead_landmarks(image_bgr):
    """
    ورودی: تصویر BGR
    خروجی: دیکشنری با نقاط (x, y) گونهٔ چپ، راست، و پیشانی
    برای فاز ۴ - تحلیل تن پوست (نمونه‌برداری رنگ پوست).
    """
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


def build_lip_mask(image_shape, landmarks, feather_px=5):
    """
    ورودی:
        image_shape: (h, w) یا (h, w, c) تصویر اصلی
        landmarks: خروجی get_lip_landmarks (لیست نقاط x,y)
        feather_px: میزان بلور لبهٔ ماسک برای طبیعی‌تر شدن مرز رنگ
    خروجی: ماسک float32 با مقادیر ۰ تا ۱، هم‌اندازهٔ تصویر اصلی
    """
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    points = np.array(landmarks, dtype=np.int32)
    hull = cv2.convexHull(points)
    cv2.fillConvexPoly(mask, hull, 255)

    # نرم کردن لبه‌ها تا مرز رنگ مصنوعی به نظر نرسد
    if feather_px > 0:
        mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=feather_px)

    return mask.astype(np.float32) / 255.0
