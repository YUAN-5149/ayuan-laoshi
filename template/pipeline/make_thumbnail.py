"""手繪風 YouTube 縮圖產生器（阿遠老師頻道視覺）。

用法:
    python make_thumbnail.py "主標題|紅字強調詞" "副標(可空)" <mascot> out.png

<mascot> 可以是：
    - 素材 png 路徑
    - auto:主題關鍵字   （依 mascot.py 對照表自動挑姿勢）

格式：依環境變數 VIDEO_VERTICAL（預設開）決定方向，與字卡/影片一致：
    - 直式 Shorts → 1080×1920（吉祥物置底置中、標題在上）
    - 橫式長片   → 1280×720（吉祥物右側、標題佔左）

設計重點（縮圖在 feed/手機是很小一張，要遠看就抓得到）：
    - 標題自動放到最大、吃滿可用寬度，不留大片空白。
    - 強調詞後面加一道手繪螢光，遠看第一眼就被吸住。
    - 副標短而粗（建議 ≤10 字的鮮明比喻），不是落落長的定義。
"""
import os
import random
import sys
from PIL import Image, ImageDraw

import mascot as mascot_lib
import style as S

VERTICAL = os.environ.get("VIDEO_VERTICAL", "1") != "0"
W, H = (1080, 1920) if VERTICAL else (1280, 720)
HILITE = (250, 204, 51)  # 螢光黃


def resolve_mascot(arg):
    if arg.startswith("auto:"):
        return mascot_lib.pick(arg[5:])
    return arg


def draw_subtitle(img, subtitle, x0, y, font_size, underline_w):
    bf = S.load_font(font_size)
    ImageDraw.Draw(img).text((x0 + 2, y), subtitle, font=bf, fill=S.INK)
    sw = ImageDraw.Draw(Image.new("RGB", (10, 10))).textlength(subtitle, font=bf)
    S.hand_line(ImageDraw.Draw(img), (x0, y + int(font_size * 1.36)),
                (x0 + sw, y + int(font_size * 1.36)), S.RED, underline_w, 2.7)


def main():
    random.seed(7)
    title_arg, subtitle, mascot_arg, out_path = sys.argv[1:5]
    title, emphasis = (title_arg.split("|", 1) + [""])[:2]

    img = S.paper_bg(W, H)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14 if VERTICAL else 12], fill=S.RED)
    S.hand_rect(d, [24, 24, W - 24, H - 24], S.INK, 4, 2.6)
    mpath = resolve_mascot(mascot_arg)

    if VERTICAL:
        # 直式 Shorts 縮圖：標題在上、吉祥物置底置中。
        S.hand_star(d, W - 116, 156, 34, S.RED, 6)
        S.hand_star(d, W - 196, 236, 18, S.LINE, 4)
        bottom = H - 90
        if mpath:
            mascot = S.fit_mascot(mpath, 780, flip=False)
            img.alpha_composite(mascot, ((W - mascot.width) // 2, H - mascot.height - 48))
            bottom = H - mascot.height - 70
        x0 = 74
        avail_w = W - 2 * x0
        title_top = 168
        sub_space = 168 if subtitle else 0
        avail_h = bottom - title_top - sub_space
        size, line_gap = S.fit_title_size(title, avail_w, avail_h,
                                          max_size=212, min_size=96, emphasis=emphasis)
        y = S.draw_title(img, title, emphasis, x0, title_top, size, avail_w,
                         line_gap=line_gap, highlight=HILITE)
        if subtitle:
            draw_subtitle(img, subtitle, x0, min(y + 18, bottom - 120), 78, 9)
    else:
        # 橫式長片縮圖：吉祥物右側、標題佔左。
        S.hand_star(d, 1180, 96, 30, S.RED, 5)
        S.hand_star(d, 1112, 162, 16, S.LINE, 4)
        if mpath:
            mascot = S.fit_mascot(mpath, 520, flip=True)  # 看向左邊
            mx = W - mascot.width - 40
            img.alpha_composite(mascot, (mx, H - mascot.height - 18))
            title_right = mx - 60
        else:
            title_right = W - 90
        x0 = 78
        avail_w = title_right - x0
        title_top = 92
        avail_h = (H - 150) - title_top if subtitle else (H - 90) - title_top
        size, line_gap = S.fit_title_size(title, avail_w, avail_h,
                                          max_size=156, min_size=76, emphasis=emphasis)
        y = S.draw_title(img, title, emphasis, x0, title_top, size, avail_w,
                         line_gap=line_gap, highlight=HILITE)
        if subtitle:
            draw_subtitle(img, subtitle, x0, min(y + 8, H - 120), 56, 7)

    img.convert("RGB").save(out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
