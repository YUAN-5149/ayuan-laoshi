"""頻道橫幅 banner 產生器（2560x1440，安全區 1546x423 置中）。

用法:
    python make_banner.py mascot.png out.png ["頻道名"] ["標語"]
"""
import random
import sys
from PIL import Image, ImageDraw

import style as S

W, H = 2560, 1440
# YouTube 各裝置都看得到的中央安全區
SAFE_W, SAFE_H = 1546, 423
SX = (W - SAFE_W) // 2
SY = (H - SAFE_H) // 2


def main():
    random.seed(5)
    mascot_path = sys.argv[1]
    out_path = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "阿遠老師"
    tagline = sys.argv[4] if len(sys.argv) > 4 else "用最白話的方式，講懂 AI"

    img = S.paper_bg(W, H)
    d = ImageDraw.Draw(img)

    # 安全區手繪外框 + 散落星星塗鴉
    S.hand_rect(d, [SX, SY, SX + SAFE_W, SY + SAFE_H], S.INK, 5, 3.0)
    S.hand_star(d, SX + 60, SY + 70, 26, S.RED, 5)
    S.hand_star(d, SX + SAFE_W - 80, SY + SAFE_H - 70, 22, S.GREEN, 5)

    # 吉祥物（安全區左側，指向右邊文字）
    mascot = S.fit_mascot(mascot_path, SAFE_H - 30)
    img.alpha_composite(mascot, (SX + 30, SY + (SAFE_H - mascot.height) // 2))

    # 文字（安全區右側）
    text_cx = SX + int(SAFE_W * 0.62)
    S.draw_title_center(img, name, text_cx, SY + 90, 150, S.INK)
    S.draw_title_center(img, tagline, text_cx, SY + 270, 60, S.RED, jitter=False, stroke=2)
    # 標語底線
    bf = S.load_font(60)
    m = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = sum(m.textlength(c, font=bf) for c in tagline)
    S.hand_line(d, (text_cx - tw / 2, SY + 350), (text_cx + tw / 2, SY + 350), S.RED, 5, 2.2)

    img.convert("RGB").save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
