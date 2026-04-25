from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class InvoiceItem(BaseModel):
    description: str = Field(..., description="品目名")
    quantity: int = Field(..., gt=0, description="数量")
    unit_price: int = Field(..., gt=0, description="単価")

    @property
    def total(self) -> int:
        return self.quantity * self.unit_price

class InvoiceRequest(BaseModel):
    invoice_number: str = Field(..., description="請求書番号")
    issue_date: date = Field(default_factory=date.today, description="発行日")
    client_name: str = Field(..., description="請求先名")
    issuer_name: str = Field(..., description="発行者名")
    seal_text: Optional[str] = Field(None, description="印影のテキスト（例：代表之印）")
    items: List[InvoiceItem] = Field(..., min_items=1, description="品目リスト")

    @property
    def grand_total(self) -> int:
        return sum(item.total for item in self.items)
