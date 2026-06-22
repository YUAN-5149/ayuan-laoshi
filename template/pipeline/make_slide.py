"""手繪風投影片字卡產生器（1920x1080）。

用法:
    python make_slide.py "標題文字" "內文文字(可空)" output.png [mascot]

[mascot] 選填：素材 png 路徑，或 auto:主題關鍵字。給了就讓吉祥物在右下角入鏡。
相容舊版三參數呼叫（無吉祥物）。
"""
import os
import random
import sys
from PIL import Image, ImageDraw

import mascot as mascot_lib
import style as S

W, H = 1920, 1080


def wrap(measure, text, font, max_w):
    lines, line = [], ""
    for ch in text:
        if ch == "\n" or measure.textlength(line + ch, font=font) > max_w:
            lines.append(line); line = "" if ch == "\n" else ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def main():
    random.seed(3)
    title = sys.argv[1]
    body = sys.argv[2]
    out_path = sys.argv[3]
    mascot_arg = sys.argv[4] if len(sys.argv) > 4 else ""

    # 防呆：輸出必須是 .png（避免空參數位移時誤覆蓋素材檔）
    if not out_path.lower().endswith(".png"):
        sys.exit(f"拒絕執行：輸出路徑必須是 .png，收到 '{out_path}'（可能是空的內文參數造成位移）")
    # 空內文請用 '-' 代表，避免 PowerShell 丟棄空字串參數
    if body == "-":
        body = ""

    img = S.paper_bg(W, H)
    d = ImageDraw.Draw(img)
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    # 頂部紅條 + 手繪外框
    d.rectangle([0, 0, W, 16], fill=S.RED)
    S.hand_rect(d, [40, 40, W - 40, H - 40], S.INK, 5, 3.0)
    S.hand_star(d, 110, 120, 22, S.RED, 5)

    # 吉祥物（右下入鏡，選填）
    text_right = W - 220
    if mascot_arg:
        path = mascot_lib.pick(mascot_arg[5:]) if mascot_arg.startswith("auto:") else mascot_arg
        if path:
            mascot = S.fit_mascot(path, 560, flip=True)  # 看向左邊（朝向內文）
            img.alpha_composite(mascot, (W - mascot.width - 90, H - mascot.height - 70))
            text_right = W - mascot.width - 170

    # 標題（手寫輕抖，米白底）
    y = S.draw_title(img, title, "", 130, 140, 120, text_right - 130, line_gap=150)

    # 內文：以 ｜ 分隔多個重點，每點一個紅色項目符號，深色大字好讀
    if body:
        bf = S.load_font(68)
        y += 36
        bullets = [b.strip() for b in body.split("｜") if b.strip()]
        for b in bullets:
            lines = wrap(measure, b, bf, text_right - 210)
            d.ellipse([140, y + 26, 166, y + 52], fill=S.RED)   # 紅點對齊首行
            for line in lines:
                d.text((196, y), line, font=bf, fill=S.INK)
                y += 92
            y += 22

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.convert("RGB").save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
