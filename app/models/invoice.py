from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class InvoiceItem(BaseModel):
    description: str = Field(..., description="品目名")
    quantity: int = Field(..., gt=0, description="数量")
    unit_price: int = Field(..., gt=0, description="単価")
    tax_rate: int = Field(10, description="消費税率 (%)")

    @property
    def total_exclusive(self) -> int:
        """税抜金額"""
        return self.quantity * self.unit_price

    @property
    def tax_amount(self) -> int:
        """この品目の消費税額 (小数点以下切り捨て)"""
        return int(self.total_exclusive * (self.tax_rate / 100))

    @property
    def total_inclusive(self) -> int:
        """税込金額"""
        return self.total_exclusive + self.tax_amount

class InvoiceRequest(BaseModel):
    invoice_number: str = Field(..., description="請求書番号")
    issue_date: date = Field(default_factory=date.today, description="発行日")
    payment_deadline: Optional[date] = Field(None, description="支払期限")
    client_name: str = Field(..., description="請求先名")
    client_address: Optional[str] = Field(None, description="請求先住所")
    issuer_name: str = Field(..., description="発行者名")
    issuer_address: Optional[str] = Field(None, description="発行者住所・連絡先")
    bank_info: Optional[str] = Field(None, description="振込先情報")
    notes: Optional[str] = Field(None, description="備考")
    seal_text: Optional[str] = Field(None, description="印影のテキスト（例：代表之印）")
    items: List[InvoiceItem] = Field(..., min_items=1, description="品目リスト")

    @property
    def subtotal(self) -> int:
        """全体の税抜小計"""
        return sum(item.total_exclusive for item in self.items)

    @property
    def total_tax(self) -> int:
        """消費税額の合計"""
        return sum(item.tax_amount for item in self.items)

    @property
    def grand_total(self) -> int:
        """税込合計金額"""
        return self.subtotal + self.total_tax

    @property
    def tax_breakdown(self) -> dict:
        """税率別の税額内訳"""
        breakdown = {}
        for item in self.items:
            rate = f"{item.tax_rate}%"
            breakdown[rate] = breakdown.get(rate, 0) + item.tax_amount
        return breakdown
