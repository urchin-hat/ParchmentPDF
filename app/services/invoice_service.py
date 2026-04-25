from fpdf import FPDF
from app.models.invoice import InvoiceRequest
from app.utils.seal_generator import generate_seal_image
import io
import os

class InvoiceService:
    @staticmethod
    def generate_pdf(data: InvoiceRequest) -> bytes:
        pdf = FPDF()
        
        # 日本語フォントの登録
        font_dir = "static/fonts"
        regular_font = os.path.join(font_dir, "NotoSansJP-Regular.otf")
        bold_font = os.path.join(font_dir, "NotoSansJP-Bold.otf")
        
        if os.path.exists(regular_font):
            pdf.add_font("NotoSansJP", "", regular_font)
        else:
            pdf.set_font("Helvetica", "", 12)
            
        if os.path.exists(bold_font):
            pdf.add_font("NotoSansJP", "B", bold_font)
        
        pdf.add_page()
        
        # タイトル
        pdf.set_font("NotoSansJP", "B", 24)
        pdf.cell(0, 30, "御請求書", ln=True, align="C")
        pdf.ln(10)
        
        # メタデータ (番号と日付) - 右寄せ
        pdf.set_font("NotoSansJP", "", 10)
        pdf.cell(0, 5, f"請求書番号: {data.invoice_number}", align="R", ln=True)
        pdf.cell(0, 5, f"発行日: {data.issue_date}", align="R", ln=True)
        pdf.ln(10)
        
        # 宛先 (左寄せ)
        pdf.set_font("NotoSansJP", "B", 16)
        pdf.cell(0, 10, f"{data.client_name} 御中", ln=True)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 100, pdf.get_y()) # 下線
        pdf.ln(15)
        
        # 発行者情報 (右寄せ)
        issuer_y_start = pdf.get_y()
        pdf.set_font("NotoSansJP", "B", 11)
        pdf.set_x(120)
        pdf.cell(70, 7, "発行者:", ln=True, align="L")
        pdf.set_font("NotoSansJP", "", 11)
        pdf.set_x(120)
        pdf.cell(70, 7, data.issuer_name, ln=True, align="L")
        
        # 印影の生成と描画
        seal_text = data.seal_text or data.issuer_name[:4]
        if seal_text:
            try:
                seal_bytes = generate_seal_image(seal_text)
                # 印影を発行者名の横に配置
                pdf.image(io.BytesIO(seal_bytes), x=165, y=issuer_y_start, w=22, h=22)
            except Exception as e:
                print(f"Error generating seal: {e}")
        
        pdf.set_y(issuer_y_start + 25) # 情報量に合わせて調整
        
        # 合計金額の強調表示
        pdf.set_font("NotoSansJP", "B", 14)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 15, f"  合計金額:  ¥{data.grand_total:,} (税込)", border="TB", ln=True, fill=True)
        pdf.ln(10)
        
        # 表ヘッダー (190mm を分割: 100, 20, 35, 35)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("NotoSansJP", "B", 10)
        pdf.cell(100, 10, "内容 / 品目", border=1, fill=True, align="C")
        pdf.cell(20, 10, "数量", border=1, fill=True, align="C")
        pdf.cell(35, 10, "単価", border=1, fill=True, align="C")
        pdf.cell(35, 10, "金額", border=1, fill=True, align="C", ln=True)
        
        # 表データ
        pdf.set_font("NotoSansJP", "", 10)
        for item in data.items:
            pdf.cell(100, 10, f" {item.description}", border=1)
            pdf.cell(20, 10, str(item.quantity), border=1, align="C")
            pdf.cell(35, 10, f"¥{item.unit_price:,} ", border=1, align="R")
            pdf.cell(35, 10, f"¥{item.total:,} ", border=1, align="R", ln=True)
            
        # フッター
        pdf.set_y(-30)
        pdf.set_font("NotoSansJP", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "本請求書は ParchmentPDF により自動生成されました。", align="C")
        
        return bytes(pdf.output())
