from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ReviewBase(BaseModel):
    content: str
    rating: int
    keywords: List[str]
    sentiment: str
    username: Optional[str] = None

class ReviewResponse(ReviewBase):
    review_id: str
    product_id: str
    create_time: datetime

    class Config:
        from_attributes = True
