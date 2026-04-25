from fpdf import FPDF
from app.models.invoice import InvoiceRequest
from app.utils.seal_generator import generate_seal_image
import io
import os

class InvoiceService:
    @staticmethod
    def generate_pdf(data: InvoiceRequest) -> bytes:
        # ユニットを mm に設定
        pdf = FPDF(unit="mm", format="A4")
        
        # 日本語フォントのパスを絶対パスで解決
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        font_dir = os.path.join(base_dir, "static", "fonts")
        regular_font = os.path.join(font_dir, "NotoSansJP-Regular.otf")
        bold_font = os.path.join(font_dir, "NotoSansJP-Bold.otf")
        
        # フォント登録 (fpdf2 ではデフォルトで Unicode サポート)
        try:
            if os.path.exists(regular_font):
                pdf.add_font("NotoSansJP", "", regular_font)
            else:
                print(f"Warning: Regular font not found at {regular_font}")
                
            if os.path.exists(bold_font):
                pdf.add_font("NotoSansJP", "B", bold_font)
            else:
                print(f"Warning: Bold font not found at {bold_font}")
        except Exception as e:
            print(f"Error adding fonts: {e}")

        # フォントが追加できなかった場合のフォールバック（ただし日本語は化ける）
        available_fonts = pdf.fonts.keys()
        default_font = "NotoSansJP" if "notosansjp" in available_fonts else "Helvetica"
        
        pdf.add_page()
        
        # タイトル
        pdf.set_font(default_font, "B", 24)
        pdf.cell(0, 30, "御請求書", ln=True, align="C")
        pdf.ln(10)
        
        # メタデータ (番号と日付) - 右寄せ
        pdf.set_font(default_font, "", 10)
        pdf.cell(0, 5, f"請求書番号: {data.invoice_number}", align="R", ln=True)
        pdf.cell(0, 5, f"発行日: {data.issue_date}", align="R", ln=True)
        pdf.ln(10)
        
        # 宛先 (左寄せ)
        pdf.set_font(default_font, "B", 16)
        pdf.cell(0, 10, f"{data.client_name} 御中", ln=True)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 100, pdf.get_y()) # 下線
        pdf.ln(15)
        
        # 発行者情報 (右寄せ)
        issuer_y_start = pdf.get_y()
        pdf.set_font(default_font, "B", 11)
        pdf.set_x(120)
        pdf.cell(70, 7, "発行者:", ln=True, align="L")
        pdf.set_font(default_font, "", 11)
        pdf.set_x(120)
        pdf.cell(70, 7, data.issuer_name, ln=True, align="L")
        
        # 印影の生成と描画
        seal_text = data.seal_text or data.issuer_name[:4]
        if seal_text:
            try:
                seal_bytes = generate_seal_image(seal_text)
                pdf.image(io.BytesIO(seal_bytes), x=165, y=issuer_y_start, w=22, h=22)
            except Exception as e:
                print(f"Error generating seal: {e}")
        
        pdf.set_y(issuer_y_start + 25)
        
        # 合計金額の強調表示
        pdf.set_font(default_font, "B", 14)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 15, f"  合計金額:  ¥{data.grand_total:,} (税込)", border="TB", ln=True, fill=True)
        pdf.ln(10)
        
        # 表ヘッダー (190mm を分割: 90, 15, 15, 35, 35)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font(default_font, "B", 9)
        pdf.cell(90, 10, "内容 / 品目", border=1, fill=True, align="C")
        pdf.cell(15, 10, "数量", border=1, fill=True, align="C")
        pdf.cell(15, 10, "税率", border=1, fill=True, align="C")
        pdf.cell(35, 10, "単価", border=1, fill=True, align="C")
        pdf.cell(35, 10, "金額 (税抜)", border=1, fill=True, align="C", ln=True)
        
        # 表データ
        pdf.set_font(default_font, "", 9)
        for item in data.items:
            pdf.cell(90, 10, f" {item.description}", border=1)
            pdf.cell(15, 10, str(item.quantity), border=1, align="C")
            pdf.cell(15, 10, f"{item.tax_rate}%", border=1, align="C")
            pdf.cell(35, 10, f"¥{item.unit_price:,} ", border=1, align="R")
            pdf.cell(35, 10, f"¥{item.total_exclusive:,} ", border=1, align="R", ln=True)
            
        pdf.ln(5)
        
        # 集計セクション (右寄せ)
        pdf.set_x(130)
        pdf.set_font(default_font, "", 10)
        pdf.cell(35, 8, "小計 (税抜):", border="B", align="R")
        pdf.cell(35, 8, f"¥{data.subtotal:,} ", border="B", align="R", ln=True)
        
        for rate, amount in data.tax_breakdown.items():
            pdf.set_x(130)
            pdf.cell(35, 8, f"消費税 ({rate}):", border="B", align="R")
            pdf.cell(35, 8, f"¥{amount:,} ", border="B", align="R", ln=True)
            
        pdf.set_x(130)
        pdf.set_font(default_font, "B", 11)
        pdf.cell(35, 10, "税込合計金額:", border="B", align="R")
        pdf.cell(35, 10, f"¥{data.grand_total:,} ", border="B", align="R", ln=True)
        
        # フッター
        pdf.set_y(-30)
        pdf.set_font(default_font, "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "本請求書は Nami-Seikyu により自動生成されました。", align="C")
        
        return bytes(pdf.output())
