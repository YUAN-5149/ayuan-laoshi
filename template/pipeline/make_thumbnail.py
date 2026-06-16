"""手繪風 YouTube 縮圖產生器（阿遠老師頻道視覺）。

用法:
    python make_thumbnail.py "主標題|紅字強調詞" "副標(可空)" <mascot> out.png

<mascot> 可以是：
    - 素材 png 路徑
    - auto:主題關鍵字   （依 mascot.py 對照表自動挑姿勢）
"""
import random
import sys
from PIL import Image, ImageDraw

import mascot as mascot_lib
import style as S

W, H = 1280, 720


def resolve_mascot(arg):
    if arg.startswith("auto:"):
        return mascot_lib.pick(arg[5:])
    return arg


def main():
    random.seed(7)
    title_arg, subtitle, mascot_arg, out_path = sys.argv[1:5]
    title, emphasis = (title_arg.split("|", 1) + [""])[:2]

    img = S.paper_bg(W, H)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, 12], fill=S.RED)
    S.hand_rect(d, [24, 24, W - 24, H - 24], S.INK, 4, 2.6)

    # 角落塗鴉
    cx, cy = 103, 615
    S.hand_rect(d, [cx - 43, cy - 30, cx + 43, cy + 30], S.LINE, 4, 2.0)
    d.polygon([(cx - 12, cy - 12), (cx - 12, cy + 12), (cx + 12, cy)], outline=S.LINE, width=4)
    S.hand_star(d, 1175, 110, 30, S.RED, 5)
    S.hand_star(d, 1110, 175, 16, S.LINE, 4)

    # 吉祥物（右側入鏡）
    mascot = S.fit_mascot(resolve_mascot(mascot_arg), 480, flip=True)  # 看向左邊
    mx = W - mascot.width - 48
    img.alpha_composite(mascot, (mx, H - mascot.height - 28))

    # 標題
    y = S.draw_title(img, title, emphasis, 76, 78, 104, mx - 100, line_gap=128)

    # 副標題 + 紅色手繪底線
    if subtitle:
        bf = S.load_font(48)
        ImageDraw.Draw(img).text((80, y + 4), subtitle, font=bf, fill=S.LINE)
        sw = ImageDraw.Draw(Image.new("RGB", (10, 10))).textlength(subtitle, font=bf)
        S.hand_line(ImageDraw.Draw(img), (80, y + 74), (80 + sw, y + 74), S.RED, 6, 2.4)

    img.convert("RGB").save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
