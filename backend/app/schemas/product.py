from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    category: str
    price: float
    sales: int
    rating: float
    hot_score: float
    image_url: str
    description: Optional[str] = None

class ProductResponse(ProductBase):
    product_id: str
    create_time: datetime

    class Config:
        from_attributes = True
