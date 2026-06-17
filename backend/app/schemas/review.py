from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReviewBase(BaseModel):
    content: str
    rating: int
    sentiment: str
    username: Optional[str] = None
    likes: Optional[int] = 0


class ReviewResponse(ReviewBase):
    review_id: str
    product_id: str
    create_time: datetime

    class Config:
        from_attributes = True
