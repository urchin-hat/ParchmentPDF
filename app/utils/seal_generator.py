from PIL import Image, ImageDraw, ImageFont
import io
import os

def generate_seal_image(text: str) -> bytes:
    """
    指定された文字列から赤い角印（電子印鑑）の画像を生成します。
    """
    size = 128
    # 透過背景の画像を作成
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 濃い赤色 (朱色に近い)
    red = (200, 40, 40, 255)
    
    # 外枠の描画 (太い枠)
    border_width = 8
    draw.rectangle(
        [border_width, border_width, size - border_width, size - border_width], 
        outline=red, 
        width=border_width
    )
    
    # フォントの設定
    font_path = "static/fonts/NotoSansJP-Bold.otf"
    if not os.path.exists(font_path):
        # フォントがない場合のフォールバック
        font = ImageFont.load_default()
    else:
        # 文字数に応じてフォントサイズを調整
        if len(text) <= 4:
            font_size = 40
        else:
            font_size = 30
        font = ImageFont.truetype(font_path, font_size)
    
    # テキストを中央に配置
    # 2x2の配置を試みる (4文字の場合)
    if len(text) == 4:
        lines = [text[:2], text[2:]]
        y_offset = 20
        for line in lines:
            # bbox = draw.textbbox((0, 0), line, font=font)
            # w = bbox[2] - bbox[0]
            # draw.text(((size - w) / 2, y_offset), line, font=font, fill=red)
            # シンプルに中央揃え
            w = draw.textlength(line, font=font)
            draw.text(((size - w) / 2, y_offset), line, font=font, fill=red)
            y_offset += 45
    else:
        # それ以外は単純な中央配置 (改行なし)
        w = draw.textlength(text, font=font)
        draw.text(((size - w) / 2, (size - font_size) / 2 - 5), text, font=font, fill=red)
    
    # バイトデータとして返す
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
