"""頻道大頭貼產生器（800x800，YouTube 會圓形裁切）。

用法:
    python make_avatar.py mascot.png out.png ["頻道名"]
"""
import random
import sys
from PIL import Image, ImageDraw

import style as S

W = H = 800


def main():
    random.seed(11)
    mascot_path = sys.argv[1]
    out_path = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "阿遠老師"

    img = S.paper_bg(W, H)
    d = ImageDraw.Draw(img)
    # 米白圓底 + 手繪紅圈（YouTube 圓裁後仍好看）
    d.ellipse([24, 24, W - 24, H - 24], fill=S.PAPER + (255,))
    S.hand_circle(d, W / 2, H / 2, (W - 80) / 2, (H - 80) / 2, S.RED, 8, 2)

    # 吉祥物置中偏上
    mascot = S.fit_mascot(mascot_path, 520)
    img.alpha_composite(mascot, ((W - mascot.width) // 2, 140))

    # 頻道名（底部置中手寫）
    S.draw_title_center(img, name, W / 2, H - 175, 96, S.INK)

    img.convert("RGB").save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
