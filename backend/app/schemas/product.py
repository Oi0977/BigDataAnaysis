from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProductBase(BaseModel):
    name: str
    category: str
    brand: str
    price: float
    original_price: Optional[float] = None
    image_url: str
    description: Optional[str] = None
    shop_name: Optional[str] = None


class ProductResponse(ProductBase):
    product_id: str
    create_time: datetime

    class Config:
        from_attributes = True


class ProductAnalysis(BaseModel):
    """Spark计算的商品分析结果"""
    product_id: str
    hot_score: float
    positive_rate: float
    negative_rate: float
    review_count: int
    avg_rating: float
    monthly_growth: float
    total_sales: int
    top_tags: Optional[str] = None
    sales_trend: Optional[str] = None
    update_time: Optional[datetime] = None
