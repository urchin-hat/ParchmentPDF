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

        # --- ヘッダー (タイトルとメタデータ) ---
        c.setFont(bold_font_name, 24)
        c.drawCentredString(width/2, height - 25*mm, "請求書")
        c.setLineWidth(0.8)
        c.setStrokeColor(colors.black)
        c.line(width/2 - 20*mm, height - 28*mm, width/2 + 20*mm, height - 28*mm)

        # メタデータ
        c.setFont(font_name, 10)
        curr_y = height - 40*mm
        c.drawRightString(width - 20*mm, curr_y, f"請求書番号: {data.invoice_number}")
        curr_y -= 5*mm
        c.drawRightString(width - 20*mm, curr_y, f"発行日: {data.issue_date}")
        if data.payment_deadline:
            curr_y -= 5*mm
            c.setFillColor(colors.red)
            c.setFont(bold_font_name, 10)
            c.drawRightString(width - 20*mm, curr_y, f"支払期限: {data.payment_deadline}")
            c.setFillColor(colors.black)

        # --- 宛先 (左側) ---
        # プレビューと同様に、上から順に要素を積み上げる
        client_y_top = height - 55*mm
        c.setFont(font_name, 9)
        c.setFillColor(colors.HexColor("#475569"))
        
        if data.client_postal_code:
            c.drawString(20*mm, client_y_top, f"〒{data.client_postal_code}")
            client_y_top -= 4.5*mm
        if data.client_address:
            for line in data.client_address.splitlines():
                c.drawString(20*mm, client_y_top, line)
                client_y_top -= 4*mm
        
        client_y_top -= 2*mm
        c.setFillColor(colors.black)
        c.setFont(bold_font_name, 16)
        c.drawString(20*mm, client_y_top, f"{data.client_name} 御中")
        c.setLineWidth(0.5)
        c.line(20*mm, client_y_top - 2*mm, 100*mm, client_y_top - 2*mm)
        
        if data.client_contact_person:
            client_y_top -= 10*mm
            c.setFont(font_name, 11)
            c.setFillColor(colors.HexColor("#334155"))
            c.drawString(25*mm, client_y_top, f"{data.client_contact_person} 様")

        # --- 発行者情報 (右側・固定位置) ---
        issuer_y_top = height - 105*mm
        c.setFont(bold_font_name, 11)
        c.drawRightString(width - 30*mm, issuer_y_top, "発行者:")
        c.setFont(bold_font_name, 12)
        c.drawRightString(width - 30*mm, issuer_y_top - 7*mm, data.issuer_name)
        
        c.setFont(font_name, 9)
        c.setFillColor(colors.HexColor("#475569"))
        addr_y = issuer_y_top - 12*mm
        if data.issuer_postal_code:
            c.drawRightString(width - 30*mm, addr_y, f"〒{data.issuer_postal_code}")
            addr_y -= 4.5*mm
        if data.issuer_address:
            for line in data.issuer_address.splitlines():
                c.drawRightString(width - 30*mm, addr_y, line)
                addr_y -= 4*mm
        
        # 印影
        seal_text = data.seal_text or data.issuer_name[:4]
        if seal_text:
            try:
                seal_bytes = generate_seal_image(seal_text)
                from reportlab.lib.utils import ImageReader
                seal_img = ImageReader(io.BytesIO(seal_bytes))
                c.drawImage(seal_img, width - 35*mm, issuer_y_top - 12*mm, width=22*mm, height=22*mm, mask='auto')
            except Exception as e:
                print(f"Error generating seal: {e}")

        # --- メッセージと合計金額バー ---
        # 宛先の長さに応じて位置を決定
        msg_y = min(client_y_top - 15*mm, issuer_y_top - 30*mm)
        c.setFillColor(colors.black)
        c.setFont(font_name, 10)
        c.drawString(20*mm, msg_y, "下記の通りご請求申し上げます。")
        
        bar_y = msg_y - 18*mm
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.rect(20*mm, bar_y, width - 40*mm, 16*mm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont(bold_font_name, 14)
        c.drawString(28*mm, bar_y + 6*mm, f"合計金額 (税込) :  ¥{data.grand_total:,}")

        # --- 請求明細テーブル ---
        table_top = bar_y - 15*mm
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

        # --- 下段セクション ---
        mid_y = y - 10*mm
        
        # 左側: 振込先
        bank_y_bottom = mid_y
        if data.bank_info:
            c.setFont(bold_font_name, 8)
            c.setFillColor(colors.HexColor("#94A3B8"))
            c.drawString(25*mm, mid_y, "【お振込先】")
            c.setFillColor(colors.black)
            c.setFont(font_name, 9)
            bank_curr_y = mid_y - 5*mm
            for line in data.bank_info.splitlines():
                c.drawString(25*mm, bank_curr_y, line)
                bank_curr_y -= 4.5*mm
            bank_y_bottom = bank_curr_y

        # 右側: 金額集計カード
        summary_w = 70
        tax_rows = len(data.tax_breakdown)
        # 高さを項目数に応じて調整 (基本 28mm + 税率1件につき 5mm)
        summary_h = 26 + (tax_rows * 5)
        summary_y_top = mid_y + 4*mm
        
        # 背景と枠線の描画
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.HexColor("#E2E8F0")) # slate-200
        c.setFillColor(colors.HexColor("#F8FAFC")) # slate-50
        # 枠の位置を少し調整して、テキストとのバランスを整える
        c.rect(width - 90*mm, summary_y_top - summary_h, summary_w*mm, summary_h, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        sy = summary_y_top - 7*mm # 1行目の開始位置
        
        c.setFont(font_name, 9)
        c.drawRightString(width - 55*mm, sy, "小計 (税抜)")
        c.drawRightString(width - 25*mm, sy, f"¥{data.subtotal:,}")
        
        sy -= 6*mm
        c.drawRightString(width - 55*mm, sy, "消費税 合計")
        c.drawRightString(width - 25*mm, sy, f"¥{data.total_tax:,}")
        
        # 税率別内訳 (インボイス要件)
        c.setFont(font_name, 7)
        c.setFillColor(colors.HexColor("#64748B")) # slate-500
        for rate, amount in data.tax_breakdown.items():
            sy -= 5*mm
            c.drawRightString(width - 55*mm, sy, f"（{rate}対象消費税）")
            c.drawRightString(width - 25*mm, sy, f"¥{amount:,}")
            
        # 税込合計 (強調ラインと太字)
        sy -= 9*mm
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.line(width - 85*mm, sy + 7*mm, width - 25*mm, sy + 7*mm)
        c.setFont(bold_font_name, 11)
        c.drawRightString(width - 55*mm, sy, "税込合計金額")
        c.drawRightString(width - 25*mm, sy, f"¥{data.grand_total:,}")

        # --- 最下段: 備考 ---
        if data.notes and data.notes.strip():
            notes_y_top = min(bank_y_bottom - 10*mm, summary_y_top - summary_h - 10*mm)
            note_lines = data.notes.splitlines()
            notes_h = 10 + (len(note_lines) * 4)
            
            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.rect(20*mm, notes_y_top - notes_h, width - 40*mm, notes_h, fill=0, stroke=1)
            
            c.setFont(bold_font_name, 8)
            c.setFillColor(colors.HexColor("#94A3B8"))
            c.drawString(25*mm, notes_y_top - 3*mm, "【備考 / 特記事項】")
            c.setFillColor(colors.black)
            c.setFont(font_name, 8)
            ny = notes_y_top - 8*mm
            for line in note_lines:
                c.drawString(25*mm, ny, line)
                ny -= 4*mm

        # フッター
        c.setFont(font_name, 8)
        c.setFillColor(colors.gray)
        c.drawCentredString(width/2, 12*mm, "本請求書は Nami-Seikyu により自動生成されました。")

        c.showPage()
        c.save()
        return buffer.getvalue()
