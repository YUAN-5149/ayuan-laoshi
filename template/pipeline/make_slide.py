"""產生簡單的字卡投影片 PNG（1920x1080，深色背景＋大字）。

用法:
    python make_slide.py "標題文字" "內文文字(可空)" output.png
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (18, 24, 38)
FG = (240, 240, 245)
ACCENT = (255, 196, 60)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msjhbd.ttc",   # 微軟正黑體 粗體
    r"C:\Windows\Fonts\msjh.ttc",
    r"C:\Windows\Fonts\arialbd.ttf",
]


def load_font(size):
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw, text, font, max_w):
    lines, line = [], ""
    for ch in text:
        if ch == "\n" or draw.textlength(line + ch, font=font) > max_w:
            lines.append(line)
            line = "" if ch == "\n" else ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def main():
    title, body, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=ACCENT)

    tf = load_font(96)
    bf = load_font(56)
    y = 200
    for line in wrap(d, title, tf, W - 300):
        d.text((150, y), line, font=tf, fill=ACCENT)
        y += 130
    y += 60
    if body:
        for line in wrap(d, body, bf, W - 300):
            d.text((150, y), line, font=bf, fill=FG)
            y += 84
    img.save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
