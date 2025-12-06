from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Event(BaseModel):
    order_id: int
    product_id: int
    product_name: str
    date: datetime
    time_checkin: Optional[datetime] = None
    checkin_latitude: Optional[float] = None
    checkin_longitude: Optional[float] = None
