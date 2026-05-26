from pydantic import BaseModel
from typing import Optional


class WMSItem(BaseModel):
    item_code: str
    description: Optional[str] = None


class WMSOrderLine(BaseModel):
    order_number: str
    item_code: str
    quantity: float
    sub1: Optional[str] = None
    sub2: Optional[str] = None


class WMSOrder(BaseModel):
    order_number: str
    description: Optional[str] = None
    operation_type: str
    lines: list[WMSOrderLine]