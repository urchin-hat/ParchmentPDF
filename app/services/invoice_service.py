from fpdf import FPDF
from app.models.invoice import InvoiceRequest
from app.utils.seal_generator import generate_seal_image
import io
import os

class InvoiceService:
    @staticmethod
    def generate_pdf(data: InvoiceRequest) -> bytes:
        # FPDF インスタンスの生成 (A4, 単位 mm)
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        
        # PDF 1.5 を明示 (Chrome との互換性を考慮)
        pdf.pdf_version = "1.5"
        
        # フォント登録
        font_dir = os.path.join(os.getcwd(), "static", "fonts")
        # 実体が OTF であっても、明示的に指定して埋め込みを促す
        regular_font = os.path.join(font_dir, "NotoSansJP-Regular.otf")
        bold_font = os.path.join(font_dir, "NotoSansJP-Bold.otf")
        
        pdf.add_font("NotoSansJP", style="", fname=regular_font)
        pdf.add_font("NotoSansJP", style="B", fname=bold_font)
        
        # マージンの設定 (左, 上, 右)
        pdf.set_margins(20, 20, 20)
        pdf.add_page()
        
        # --- タイトル ---
        pdf.set_font("NotoSansJP", "B", 24)
        # align="C" で消えるのを防ぐため、明示的な幅を指定
        pdf.cell(170, 20, "御請求書", ln=1, align="C")
        pdf.ln(5)
        
        # --- メタデータ (番号と日付) ---
        pdf.set_font("NotoSansJP", "", 10)
        pdf.cell(0, 6, f"請求書番号: {data.invoice_number}", align="R", ln=1)
        pdf.cell(0, 6, f"発行日: {data.issue_date}", align="R", ln=1)
        pdf.ln(5)
        
        # --- 宛先 ---
        pdf.set_font("NotoSansJP", "B", 16)
        pdf.cell(0, 10, f"{data.client_name} 御中", ln=1)
        # 下線
        current_y = pdf.get_y()
        pdf.line(20, current_y, 100, current_y)
        pdf.ln(10)

        # --- 合計金額バー ---
        pdf.set_font("NotoSansJP", "B", 14)
        pdf.set_fill_color(248, 250, 252) # slate-50
        pdf.set_draw_color(226, 232, 240) # slate-200
        # セルの高さを確保し、内側に余白を持たせる
        pdf.cell(0, 16, f" 合計金額 (税込) :  ¥{data.grand_total:,}", border=1, ln=1, fill=True)
        pdf.ln(10)
        
        # --- 発行者情報 ---
        # 後の印影のために y 座標を記録
        issuer_y_start = pdf.get_y()
        pdf.set_font("NotoSansJP", "B", 11)
        pdf.set_x(130)
        pdf.cell(0, 7, "発行者:", ln=1)
        pdf.set_font("NotoSansJP", "", 11)
        pdf.set_x(130)
        pdf.cell(0, 7, data.issuer_name, ln=1)
        
        # 印影
        seal_text = data.seal_text or data.issuer_name[:4]
        if seal_text:
            try:
                seal_bytes = generate_seal_image(seal_text)
                # 画像の配置
                pdf.image(io.BytesIO(seal_bytes), x=165, y=issuer_y_start - 2, w=22, h=22)
            except Exception as e:
                print(f"Error generating seal: {e}")
        
        pdf.set_y(issuer_y_start + 25)
        
        # --- 表ヘッダー ---
        pdf.set_draw_color(30, 41, 59) # slate-800
        pdf.set_fill_color(248, 250, 252)
        pdf.set_font("NotoSansJP", "B", 9)
        # 列幅の設定 (計 170mm)
        w_desc, w_qty, w_tax, w_unit, w_total = 75, 15, 15, 30, 35
        
        pdf.cell(w_desc, 10, "内容 / 品目", border="TB", fill=True, align="C")
        pdf.cell(w_qty, 10, "数量", border="TB", fill=True, align="C")
        pdf.cell(w_tax, 10, "税率", border="TB", fill=True, align="C")
        pdf.cell(w_unit, 10, "単価", border="TB", fill=True, align="C")
        pdf.cell(w_total, 10, "金額 (税抜)", border="TB", fill=True, align="C", ln=1)
        
        # --- 表データ ---
        pdf.set_draw_color(226, 232, 240) # slate-200
        pdf.set_font("NotoSansJP", "", 9)
        for item in data.items:
            pdf.cell(w_desc, 10, f" {item.description}", border="B")
            pdf.cell(w_qty, 10, str(item.quantity), border="B", align="C")
            pdf.cell(w_tax, 10, f"{item.tax_rate}%", border="B", align="C")
            pdf.cell(w_unit, 10, f"¥{item.unit_price:,} ", border="B", align="R")
            pdf.cell(w_total, 10, f"¥{item.total_exclusive:,} ", border="B", align="R", ln=1)
            
        pdf.ln(8)
        
        # --- 集計セクション ---
        summary_w = 70
        pdf.set_x(120)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_font("NotoSansJP", "", 9)
        
        pdf.cell(summary_w/2, 8, "小計 (税抜) ", align="R", fill=True)
        pdf.cell(summary_w/2, 8, f"¥{data.subtotal:,} ", align="R", fill=True, ln=1)
        
        for rate, amount in data.tax_breakdown.items():
            pdf.set_x(120)
            pdf.cell(summary_w/2, 8, f"消費税 ({rate}) ", align="R", fill=True)
            pdf.cell(summary_w/2, 8, f"¥{amount:,} ", align="R", fill=True, ln=1)
            
        pdf.set_x(120)
        pdf.set_draw_color(30, 41, 59)
        pdf.set_font("NotoSansJP", "B", 11)
        pdf.cell(summary_w/2, 10, "税込合計金額 ", border="T", align="R", fill=True)
        pdf.cell(summary_w/2, 10, f"¥{data.grand_total:,} ", border="T", align="R", fill=True, ln=1)
        
        # --- フッター ---
        pdf.set_y(-25)
        pdf.set_font("NotoSansJP", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "本請求書は Nami-Seikyu により自動生成されました。", align="C")
        
        return bytes(pdf.output())
