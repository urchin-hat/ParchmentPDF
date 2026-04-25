from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib import colors
from app.models.invoice import InvoiceRequest
from app.utils.seal_generator import generate_seal_image
import io
import os

class InvoiceService:
    @staticmethod
    def generate_pdf(data: InvoiceRequest) -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setTitle(f"Invoice_{data.invoice_number}")

        # フォント登録
        font_dir = os.path.join(os.getcwd(), "static", "fonts")
        regular_font_path = os.path.join(font_dir, "Business-Regular.ttf")
        bold_font_path = os.path.join(font_dir, "Business-Bold.ttf")

        pdfmetrics.registerFont(TTFont('BusinessFont', regular_font_path))
        pdfmetrics.registerFont(TTFont('BusinessFont-Bold', bold_font_path))
        
        font_name = 'BusinessFont'
        bold_font_name = 'BusinessFont-Bold'

        width, height = A4

        # --- タイトル ---
        c.setFont(bold_font_name, 24)
        c.drawCentredString(width/2, height - 25*mm, "御請求書")
        c.setLineWidth(0.8)
        c.setStrokeColor(colors.black)
        c.line(width/2 - 20*mm, height - 28*mm, width/2 + 20*mm, height - 28*mm)

        # --- メタデータ ---
        c.setFont(font_name, 10)
        c.drawRightString(width - 20*mm, height - 40*mm, f"請求書番号: {data.invoice_number}")
        c.drawRightString(width - 20*mm, height - 45*mm, f"発行日: {data.issue_date}")
        if data.payment_deadline:
            c.setFillColor(colors.red)
            c.setFont(bold_font_name, 10)
            c.drawRightString(width - 20*mm, height - 50*mm, f"支払期限: {data.payment_deadline}")
            c.setFillColor(colors.black)

        # --- 宛先 ---
        c.setFont(font_name, 9)
        c.setFillColor(colors.HexColor("#475569"))
        client_y = height - 55*mm
        if data.client_address:
            for line in data.client_address.splitlines():
                c.drawString(20*mm, client_y, line)
                client_y -= 4*mm
        
        c.setFillColor(colors.black)
        c.setFont(bold_font_name, 16)
        c.drawString(20*mm, client_y - 2*mm, f"{data.client_name} 御中")
        c.setLineWidth(0.5)
        c.line(20*mm, client_y - 4*mm, 100*mm, client_y - 4*mm)

        # --- 合計金額バー ---
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.rect(20*mm, height - 83*mm, width - 40*mm, 16*mm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont(bold_font_name, 14)
        c.drawString(28*mm, height - 75*mm, f"合計金額 (税込) :  ¥{data.grand_total:,}")
        
        # --- 発行者情報 ---
        issuer_y = height - 100*mm
        c.setFont(bold_font_name, 11)
        c.drawRightString(width - 30*mm, issuer_y, "発行者:")
        c.setFont(bold_font_name, 12)
        c.drawRightString(width - 30*mm, issuer_y - 7*mm, data.issuer_name)
        
        if data.issuer_address:
            c.setFont(font_name, 9)
            c.setFillColor(colors.HexColor("#475569"))
            addr_y = issuer_y - 12*mm
            for line in data.issuer_address.splitlines():
                c.drawRightString(width - 30*mm, addr_y, line)
                addr_y -= 4*mm
            c.setFillColor(colors.black)

        # 印影
        seal_text = data.seal_text or data.issuer_name[:4]
        if seal_text:
            try:
                seal_bytes = generate_seal_image(seal_text)
                from reportlab.lib.utils import ImageReader
                seal_img = ImageReader(io.BytesIO(seal_bytes))
                c.drawImage(seal_img, width - 35*mm, issuer_y - 12*mm, width=22*mm, height=22*mm, mask='auto')
            except Exception as e:
                print(f"Error generating seal: {e}")

        # --- 表ヘッダー ---
        table_top = height - 135*mm
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.rect(20*mm, table_top - 10*mm, width - 40*mm, 10*mm, fill=1, stroke=0)
        c.line(20*mm, table_top, width - 20*mm, table_top)
        c.line(20*mm, table_top - 10*mm, width - 20*mm, table_top - 10*mm)
        
        c.setFillColor(colors.black)
        c.setFont(bold_font_name, 9)
        c.drawString(25*mm, table_top - 7*mm, "内容 / 品目")
        c.drawCentredString(110*mm, table_top - 7*mm, "数量")
        c.drawCentredString(125*mm, table_top - 7*mm, "税率")
        c.drawRightString(155*mm, table_top - 7*mm, "単価")
        c.drawRightString(width - 25*mm, table_top - 7*mm, "金額 (税抜)")

        # --- 表データ ---
        y = table_top - 10*mm
        c.setFont(font_name, 9)
        for item in data.items:
            y -= 10*mm
            c.drawString(25*mm, y + 3*mm, item.description)
            c.drawCentredString(110*mm, y + 3*mm, str(item.quantity))
            c.drawCentredString(125*mm, y + 3*mm, f"{item.tax_rate}%")
            c.drawRightString(155*mm, y + 3*mm, f"¥{item.unit_price:,}")
            c.drawRightString(width - 25*mm, y + 3*mm, f"¥{item.total_exclusive:,}")
            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.setLineWidth(0.3)
            c.line(20*mm, y, width - 20*mm, y)

        # --- 中段セクション (振込先と金額内訳) ---
        mid_section_y = y - 10*mm
        
        # 左側: 振込先
        if data.bank_info:
            c.setFont(bold_font_name, 8)
            c.setFillColor(colors.HexColor("#94A3B8"))
            c.drawString(25*mm, mid_section_y, "【お振込先】")
            c.setFillColor(colors.black)
            c.setFont(font_name, 9)
            bank_y = mid_section_y - 5*mm
            for line in data.bank_info.splitlines():
                c.drawString(25*mm, bank_y, line)
                bank_y -= 4.5*mm

        # 右側: 金額集計カード
        summary_w = 70
        summary_h = 24 + (len(data.tax_breakdown) * 5)
        summary_y_top = mid_section_y + 4*mm
        
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.rect(width - 90*mm, summary_y_top - summary_h, 70*mm, summary_h, fill=1, stroke=1)
        c.setFillColor(colors.black)
        
        curr_y = summary_y_top - 6*mm
        c.setFont(font_name, 9)
        c.drawRightString(width - 55*mm, curr_y, "小計 (税抜)")
        c.drawRightString(width - 25*mm, curr_y, f"¥{data.subtotal:,}")
        
        curr_y -= 6*mm
        c.drawRightString(width - 55*mm, curr_y, "消費税 合計")
        c.drawRightString(width - 25*mm, curr_y, f"¥{data.total_tax:,}")
        
        # 税率別内訳 (インボイス要件)
        c.setFont(font_name, 7)
        c.setFillColor(colors.HexColor("#64748B"))
        for rate, amount in data.tax_breakdown.items():
            curr_y -= 4.5*mm
            c.drawRightString(width - 55*mm, curr_y, f"（{rate}対象消費税）")
            c.drawRightString(width - 25*mm, curr_y, f"¥{amount:,}")
            
        curr_y -= 8*mm
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.line(width - 85*mm, curr_y + 6*mm, width - 25*mm, curr_y + 6*mm)
        c.setFont(bold_font_name, 11)
        c.drawRightString(width - 55*mm, curr_y, "税込合計金額")
        c.drawRightString(width - 25*mm, curr_y, f"¥{data.grand_total:,}")

        # --- 最下段: 備考 ---
        if data.notes and data.notes.strip():
            notes_y = summary_y_top - summary_h - 15*mm
            c.setStrokeColor(colors.HexColor("#F1F5F9"))
            c.line(20*mm, notes_y + 5*mm, width - 20*mm, notes_y + 5*mm)
            
            c.setFont(bold_font_name, 8)
            c.setFillColor(colors.HexColor("#94A3B8"))
            c.drawString(25*mm, notes_y, "【備考 / 特記事項】")
            c.setFillColor(colors.black)
            c.setFont(font_name, 8)
            notes_y -= 5*mm
            for line in data.notes.splitlines():
                c.drawString(25*mm, notes_y, line)
                notes_y -= 4*mm

        # --- フッター ---
        c.setFont(font_name, 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 12*mm, "本請求書は Nami-Seikyu により自動生成されました。")

        c.showPage()
        c.save()
        return buffer.getvalue()
