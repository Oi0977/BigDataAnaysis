from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    product_id: str
    name: str
    category: str
    brand: str
    price: float
    image_url: str
    create_time: datetime
    original_price: Optional[float] = None
    description: Optional[str] = None
    shop_name: Optional[str] = None


@dataclass
class ProductAnalysis:
    """Spark计算的商品分析结果"""
    product_id: str
    hot_score: float = 0.0
    positive_rate: float = 0.0
    negative_rate: float = 0.0
    review_count: int = 0
    avg_rating: float = 0.0
    monthly_growth: float = 0.0
    total_sales: int = 0
    top_tags: str = ""
    sales_trend: str = ""
    update_time: Optional[datetime] = None
