from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.models.invoice import InvoiceRequest, InvoiceItem
from app.services.invoice_service import InvoiceService
from datetime import date
from typing import List, Optional
import io

app = FastAPI(title="ParchmentPDF - Invoice Generator")

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
    client_name: str,
    issuer_name: str,
    seal_text: Optional[str],
    item_desc: List[str],
    item_qty: List[int],
    item_price: List[str] # カンマ付きで送られるため str に変更
) -> InvoiceRequest:
    items = []
    for desc, qty, price_str in zip(item_desc, item_qty, item_price):
        if desc.strip():
            # カンマを除去して数値に変換
            clean_price = int(price_str.replace(",", "")) if price_str else 0
            items.append(InvoiceItem(description=desc, quantity=qty, unit_price=clean_price))
    
    return InvoiceRequest(
        invoice_number=invoice_number,
        issue_date=issue_date,
        client_name=client_name,
        issuer_name=issuer_name,
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
    client_name: str = Form(...),
    issuer_name: str = Form(...),
    seal_text: str = Form(None),
    item_desc: List[str] = Form(...),
    item_qty: List[int] = Form(...),
    item_price: List[str] = Form(...)
):
    invoice_data = parse_invoice_form(
        invoice_number, issue_date, client_name, issuer_name, seal_text, 
        item_desc, item_qty, item_price
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
    client_name: str = Form(...),
    issuer_name: str = Form(...),
    seal_text: str = Form(None),
    item_desc: List[str] = Form(...),
    item_qty: List[int] = Form(...),
    item_price: List[str] = Form(...)
):
    invoice_data = parse_invoice_form(
        invoice_number, issue_date, client_name, issuer_name, seal_text, 
        item_desc, item_qty, item_price
    )
    
    pdf_bytes = InvoiceService.generate_pdf(invoice_data)
    
    headers = {
        'Content-Disposition': f'attachment; filename="invoice_{invoice_number}.pdf"'
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
