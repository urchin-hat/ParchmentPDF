from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.models.invoice import InvoiceRequest, InvoiceItem
from app.services.invoice_service import InvoiceService
from datetime import date
from typing import List, Optional
from urllib.parse import quote
import io

app = FastAPI(title="Nami-Seikyu - 波請求")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 金額をカンマ区切りにするフィルタ
def format_currency(value):
    try:
        if value is None:
            return "0"
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return str(value)

templates.env.filters["font_format_currency"] = format_currency

def parse_invoice_form(
    invoice_number: str,
    issue_date: date,
    payment_deadline: Optional[date],
    client_name: str,
    issuer_name: str,
    issuer_address: Optional[str],
    bank_info: Optional[str],
    notes: Optional[str],
    seal_text: Optional[str],
    item_desc: List[str],
    item_qty: List[int],
    item_price: List[str],
    item_tax: List[int]
) -> InvoiceRequest:
    items = []
    for desc, qty, price_str, tax in zip(item_desc, item_qty, item_price, item_tax):
        if desc.strip():
            clean_price = int(price_str.replace(",", "")) if price_str else 0
            items.append(InvoiceRequest.Item(description=desc, quantity=qty, unit_price=clean_price, tax_rate=tax)) # 型ヒント調整
    
    # 実際には InvoiceItem を使う (インポート済み)
    items = []
    for desc, qty, price_str, tax in zip(item_desc, item_qty, item_price, item_tax):
        if desc.strip():
            clean_price = int(price_str.replace(",", "")) if price_str else 0
            items.append(InvoiceItem(description=desc, quantity=qty, unit_price=clean_price, tax_rate=tax))

    return InvoiceRequest(
        invoice_number=invoice_number,
        issue_date=issue_date,
        payment_deadline=payment_deadline,
        client_name=client_name,
        issuer_name=issuer_name,
        issuer_address=issuer_address,
        bank_info=bank_info,
        notes=notes,
        seal_text=seal_text,
        items=items
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "today": date.today().isoformat(),
            "default_invoice_no": f"INV-{date.today().strftime('%Y%m%d')}-01"
        }
    )

@app.get("/add-item", response_class=HTMLResponse)
async def add_item(request: Request):
    return templates.TemplateResponse(request=request, name="fragments/item_row.html", context={})

@app.post("/preview", response_class=HTMLResponse)
async def preview_invoice(
    request: Request,
    invoice_number: str = Form(...),
    issue_date: date = Form(...),
    payment_deadline: date = Form(None),
    client_name: str = Form(...),
    issuer_name: str = Form(...),
    issuer_address: str = Form(None),
    bank_info: str = Form(None),
    notes: str = Form(None),
    seal_text: str = Form(None),
    item_desc: List[str] = Form(...),
    item_qty: List[int] = Form(...),
    item_price: List[str] = Form(...),
    item_tax: List[int] = Form(...)
):
    invoice_data = parse_invoice_form(
        invoice_number, issue_date, payment_deadline, client_name, issuer_name, 
        issuer_address, bank_info, notes, seal_text, 
        item_desc, item_qty, item_price, item_tax
    )
    
    return templates.TemplateResponse(
        request=request,
        name="fragments/invoice_preview.html",
        context={
            "invoice": invoice_data,
            "grand_total": invoice_data.grand_total
        }
    )

@app.post("/generate")
async def generate_invoice(
    invoice_number: str = Form(...),
    issue_date: date = Form(...),
    payment_deadline: date = Form(None),
    client_name: str = Form(...),
    issuer_name: str = Form(...),
    issuer_address: str = Form(None),
    bank_info: str = Form(None),
    notes: str = Form(None),
    seal_text: str = Form(None),
    item_desc: List[str] = Form(...),
    item_qty: List[int] = Form(...),
    item_price: List[str] = Form(...),
    item_tax: List[int] = Form(...)
):
    invoice_data = parse_invoice_form(
        invoice_number, issue_date, payment_deadline, client_name, issuer_name, 
        issuer_address, bank_info, notes, seal_text, 
        item_desc, item_qty, item_price, item_tax
    )
    
    pdf_bytes = InvoiceService.generate_pdf(invoice_data)
    
    # Chrome の独自起源問題を避けるため、一旦 ASCII のみのファイル名に固定
    filename = f"invoice_{invoice_number}.pdf"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
