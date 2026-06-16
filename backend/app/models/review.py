from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Review:
    review_id: str
    product_id: str
    content: str
    rating: int
    keywords: list
    sentiment: str
    create_time: datetime
    username: Optional[str] = None
