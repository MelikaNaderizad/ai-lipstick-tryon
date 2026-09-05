"""
مدل‌های Pydantic برای ورودی/خروجی endpoint های FastAPI.
"""

from pydantic import BaseModel
from typing import List, Optional


class LabColor(BaseModel):
    l: float
    a: float
    b: float


class ProductColorResponse(BaseModel):
    swatch_lab: LabColor
    swatch_fraction: float


class ProductMatch(BaseModel):
    product_id: int
    name: str
    delta_e: float


class SkinToneResponse(BaseModel):
    undertone: str  # "warm" | "cool" | "neutral"
    skin_lab: LabColor
    top_matches: List[ProductMatch]


class ApplyLipstickRequest(BaseModel):
    product_id: Optional[int] = None
    lab: Optional[LabColor] = None
