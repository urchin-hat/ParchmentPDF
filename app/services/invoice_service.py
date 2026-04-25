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

        # フォント登録 (真の TrueType を使用)
        font_dir = os.path.join(os.getcwd(), "static", "fonts")
        regular_font_path = os.path.join(font_dir, "JPFont-Regular.ttf")
        bold_font_path = os.path.join(font_dir, "JPFont-Bold.ttf")

        # pdfmetrics.registerFont で TTFont を登録
        # TrueType アウトラインのため、Chrome/ReportLab ともに完璧に動作します。
        pdfmetrics.registerFont(TTFont('JPFont', regular_font_path))
        pdfmetrics.registerFont(TTFont('JPFont-Bold', bold_font_path))
        
        font_name = 'JPFont'
        bold_font_name = 'JPFont-Bold'

        width, height = A4

        # --- 描画開始 ---
        # タイトル
        c.setFont(bold_font_name, 24)
        c.drawCentredString(width/2, height - 30*mm, "御請求書")
        
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.line(width/2 - 20*mm, height - 33*mm, width/2 + 20*mm, height - 33*mm)

        # メタデータ (右寄せ)
        c.setFont(font_name, 10)
        c.drawRightString(width - 20*mm, height - 45*mm, f"請求書番号: {data.invoice_number}")
        c.drawRightString(width - 20*mm, height - 51*mm, f"発行日: {data.issue_date}")

        # 宛先 (左寄せ)
        c.setFont(bold_font_name, 16)
        c.drawString(20*mm, height - 65*mm, f"{data.client_name} 御中")
        c.setLineWidth(0.5)
        c.line(20*mm, height - 67*mm, 100*mm, height - 67*mm)

        # 合計金額バー
        c.setFillColor(colors.HexColor("#F8FAFC")) # slate-50
        c.setStrokeColor(colors.HexColor("#E2E8F0")) # slate-200
        c.rect(20*mm, height - 88*mm, width - 40*mm, 16*mm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont(bold_font_name, 14)
        c.drawString(28*mm, height - 80*mm, f"合計金額 (税込) :  ¥{data.grand_total:,}")
        
        # 発行者情報 (右寄せ)
        issuer_y = height - 105*mm
        c.setFont(bold_font_name, 11)
        c.drawString(130*mm, issuer_y, "発行者:")
        c.setFont(font_name, 11)
        c.drawString(130*mm, issuer_y - 7*mm, data.issuer_name)

        # 印影
        seal_text = data.seal_text or data.issuer_name[:4]
        if seal_text:
            try:
                seal_bytes = generate_seal_image(seal_text)
                from reportlab.lib.utils import ImageReader
                seal_img = ImageReader(io.BytesIO(seal_bytes))
                c.drawImage(seal_img, 165*mm, issuer_y - 15*mm, width=22*mm, height=22*mm, mask='auto')
            except Exception as e:
                print(f"Error generating seal: {e}")

        # 表ヘッダー
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

        # 表データ
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

        # 集計セクション
        y -= 15*mm
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.rect(width - 95*mm, y - 30*mm, 75*mm, 40*mm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        
        current_y = y + 2*mm
        c.setFont(font_name, 9)
        c.drawRightString(width - 60*mm, current_y, "小計 (税抜)")
        c.drawRightString(width - 25*mm, current_y, f"¥{data.subtotal:,}")
        
        for rate, amount in data.tax_breakdown.items():
            current_y -= 8*mm
            c.drawRightString(width - 60*mm, current_y, f"消費税 ({rate})")
            c.drawRightString(width - 25*mm, current_y, f"¥{amount:,}")
            
        current_y -= 10*mm
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.line(width - 90*mm, current_y + 8*mm, width - 25*mm, current_y + 8*mm)
        c.setFont(bold_font_name, 11)
        c.drawRightString(width - 60*mm, current_y, "税込合計金額")
        c.drawRightString(width - 25*mm, current_y, f"¥{data.grand_total:,}")

        # フッター
        c.setFont(font_name, 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 20*mm, "本請求書は Nami-Seikyu により自動生成されました。")

        c.showPage()
        c.save()
        return buffer.getvalue()
