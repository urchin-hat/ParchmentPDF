from fpdf import FPDF
from app.models.invoice import InvoiceRequest
from app.utils.seal_generator import generate_seal_image
import io
import os

class InvoiceService:
    @staticmethod
    def generate_pdf(data: InvoiceRequest) -> bytes:
        # FPDF インスタンスの生成 (ユニットを mm に設定)
        pdf = FPDF(unit="mm", format="A4")
        
        # PDF バージョンを 1.5 に設定 (互換性重視)
        try:
            pdf.pdf_version = "1.5"
        except:
            pass

        # フォント登録 (fname 引数を明示)
        font_dir = os.path.join(os.getcwd(), "static", "fonts")
        regular_font = os.path.join(font_dir, "NotoSansJP-Regular.otf")
        bold_font = os.path.join(font_dir, "NotoSansJP-Bold.otf")
        
        pdf.add_font("NotoSansJP", style="", fname=regular_font)
        pdf.add_font("NotoSansJP", style="B", fname=bold_font)
        
        pdf.add_page()
        
        # タイトル
        pdf.set_font("NotoSansJP", "B", 24)
        pdf.cell(0, 30, "御請求書", ln=True, align="C")
        pdf.ln(5)
        
        # メタデータ (番号と日付)
        pdf.set_font("NotoSansJP", "", 10)
        pdf.cell(0, 5, f"請求書番号: {data.invoice_number}", align="R", ln=True)
        pdf.cell(0, 5, f"発行日: {data.issue_date}", align="R", ln=True)
        pdf.ln(5)
        
        # 宛先
        pdf.set_font("NotoSansJP", "B", 16)
        pdf.cell(0, 10, f"{data.client_name} 御中", ln=True)
        pdf.set_line_width(0.5)
        pdf.set_draw_color(30, 41, 59)
        pdf.line(10, pdf.get_y(), 100, pdf.get_y())
        pdf.ln(10)

        # 合計金額バー (横幅いっぱい)
        pdf.set_font("NotoSansJP", "B", 14)
        pdf.set_fill_color(248, 250, 252) # slate-50
        pdf.set_draw_color(226, 232, 240) # slate-200
        pdf.cell(0, 16, f"  合計金額 (税込) :  ¥{data.grand_total:,}", border=1, ln=True, fill=True)
        pdf.ln(10)
        
        # 発行者情報
        issuer_y_start = pdf.get_y()
        pdf.set_font("NotoSansJP", "B", 11)
        pdf.set_x(120)
        pdf.cell(70, 7, "発行者:", ln=True, align="L")
        pdf.set_font("NotoSansJP", "", 11)
        pdf.set_x(120)
        pdf.cell(70, 7, data.issuer_name, ln=True, align="L")
        
        # 印影
        seal_text = data.seal_text or data.issuer_name[:4]
        if seal_text:
            try:
                seal_bytes = generate_seal_image(seal_text)
                pdf.image(io.BytesIO(seal_bytes), x=165, y=issuer_y_start, w=22, h=22)
            except Exception as e:
                print(f"Error generating seal: {e}")
        
        pdf.set_y(issuer_y_start + 25)
        
        # 表ヘッダー
        pdf.set_draw_color(30, 41, 59)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_font("NotoSansJP", "B", 9)
        pdf.cell(90, 10, "内容 / 品目", border="TB", fill=True, align="C")
        pdf.cell(15, 10, "数量", border="TB", fill=True, align="C")
        pdf.cell(15, 10, "税率", border="TB", fill=True, align="C")
        pdf.cell(35, 10, "単価", border="TB", fill=True, align="C")
        pdf.cell(35, 10, "金額 (税抜)", border="TB", fill=True, align="C", ln=True)
        
        # 表データ
        pdf.set_draw_color(226, 232, 240)
        pdf.set_font("NotoSansJP", "", 9)
        for item in data.items:
            pdf.cell(90, 10, f" {item.description}", border="B")
            pdf.cell(15, 10, str(item.quantity), border="B", align="C")
            pdf.cell(15, 10, f"{item.tax_rate}%", border="B", align="C")
            pdf.cell(35, 10, f"¥{item.unit_price:,} ", border="B", align="R")
            pdf.cell(35, 10, f"¥{item.total_exclusive:,} ", border="B", align="R", ln=True)
            
        pdf.ln(8)
        
        # 集計セクション
        summary_x, summary_w = 125, 75
        pdf.set_x(summary_x)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_font("NotoSansJP", "", 9)
        pdf.cell(summary_w/2, 8, "小計 (税抜) ", align="R", fill=True)
        pdf.cell(summary_w/2, 8, f"¥{data.subtotal:,} ", align="R", fill=True, ln=True)
        
        for rate, amount in data.tax_breakdown.items():
            pdf.set_x(summary_x)
            pdf.cell(summary_w/2, 8, f"消費税 ({rate}) ", align="R", fill=True)
            pdf.cell(summary_w/2, 8, f"¥{amount:,} ", align="R", fill=True, ln=True)
            
        pdf.set_x(summary_x)
        pdf.set_draw_color(30, 41, 59)
        pdf.set_font("NotoSansJP", "B", 11)
        pdf.cell(summary_w/2, 10, "税込合計金額 ", border="T", align="R", fill=True)
        pdf.cell(summary_w/2, 10, f"¥{data.grand_total:,} ", border="T", align="R", fill=True, ln=True)
        
        pdf.set_y(-30)
        pdf.set_font("NotoSansJP", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "本請求書は Nami-Seikyu により自動生成されました。", align="C")
        
        return bytes(pdf.output())
