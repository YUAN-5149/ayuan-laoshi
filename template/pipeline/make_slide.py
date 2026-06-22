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

# 直式（Shorts 9:16）為預設；設環境變數 VIDEO_VERTICAL=0 可切回橫式 16:9。
VERTICAL = os.environ.get("VIDEO_VERTICAL", "1") != "0"
W, H = (1080, 1920) if VERTICAL else (1920, 1080)


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

    mascot_path = None
    if mascot_arg:
        mascot_path = mascot_lib.pick(mascot_arg[5:]) if mascot_arg.startswith("auto:") else mascot_arg

    if VERTICAL:
        # 直式 Shorts：標題置頂吃滿寬、內文中段、吉祥物置底置中。
        if mascot_path:
            mascot = S.fit_mascot(mascot_path, 700, flip=False)
            img.alpha_composite(mascot, ((W - mascot.width) // 2, H - mascot.height - 80))
        tx, ty, tsize = 96, 210, 122
        y = S.draw_title(img, title, "", tx, ty, tsize, W - tx - 80, line_gap=156)
        if body:
            bf = S.load_font(72)
            y += 48
            for b in [x.strip() for x in body.split("｜") if x.strip()]:
                lines = wrap(measure, b, bf, W - 180 - 90)
                d.ellipse([110, y + 30, 142, y + 62], fill=S.RED)
                for line in lines:
                    d.text((180, y), line, font=bf, fill=S.INK)
                    y += 100
                y += 28
    else:
        # 橫式 16:9：吉祥物右下，文字佔左側。
        text_right = W - 220
        if mascot_path:
            mascot = S.fit_mascot(mascot_path, 560, flip=True)  # 看向左邊（朝向內文）
            img.alpha_composite(mascot, (W - mascot.width - 90, H - mascot.height - 70))
            text_right = W - mascot.width - 170
        y = S.draw_title(img, title, "", 130, 140, 120, text_right - 130, line_gap=150)
        if body:
            bf = S.load_font(68)
            y += 36
            for b in [x.strip() for x in body.split("｜") if x.strip()]:
                lines = wrap(measure, b, bf, text_right - 210)
                d.ellipse([140, y + 26, 166, y + 52], fill=S.RED)
                for line in lines:
                    d.text((196, y), line, font=bf, fill=S.INK)
                    y += 92
                y += 22

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.convert("RGB").save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
