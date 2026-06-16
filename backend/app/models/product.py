from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Product:
    product_id: str
    name: str
    category: str
    price: float
    sales: int
    rating: float
    hot_score: float
    image_url: str
    create_time: datetime
    description: Optional[str] = None
