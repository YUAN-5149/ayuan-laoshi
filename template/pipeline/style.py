"""阿遠老師頻道共用手繪風格工具（縮圖、投影片、頻道門面共用）。"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont

PAPER = (247, 242, 231)   # 米白紙張
INK = (44, 40, 35)        # 墨黑
RED = (214, 48, 40)       # 強調紅
LINE = (70, 64, 58)       # 塗鴉線
GREEN = (122, 168, 76)    # 消防綠點綴

_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
CUTE_FONTS = [os.path.join(_FONT_DIR, "openhuninn.ttf"),
              r"C:\Windows\Fonts\kaiu.ttf", r"C:\Windows\Fonts\msjhbd.ttc"]


def load_font(size):
    for p in CUTE_FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def remove_white_bg(img, thresh=42):
    """以邊緣洪水填充去除近白背景，回傳裁切到內容的 RGBA。"""
    img = img.convert("RGBA")
    rgb = img.convert("RGB")
    seed = (255, 0, 255)
    w, h = rgb.size
    for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
               (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        ImageDraw.floodfill(rgb, pt, seed, thresh=thresh)
    src = list(img.getdata())
    mask = list(rgb.getdata())
    out = Image.new("RGBA", img.size)
    out.putdata([(0, 0, 0, 0) if mask[i] == seed else src[i] for i in range(len(src))])
    bbox = out.getbbox()
    return out.crop(bbox) if bbox else out


def paper_bg(w, h):
    base = Image.new("RGBA", (w, h), PAPER + (255,))
    noise = Image.effect_noise((w, h), 16).convert("L")
    grain = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (w, h), 16)))
    return Image.alpha_composite(base, grain)


def hand_line(d, p1, p2, color, width=4, jitter=2.2, seg=18):
    x1, y1 = p1
    x2, y2 = p2
    dist = max(1.0, math.hypot(x2 - x1, y2 - y1))
    n = max(2, int(dist / seg))
    nx, ny = -(y2 - y1) / dist, (x2 - x1) / dist
    pts = []
    for i in range(n + 1):
        t = i / n
        off = random.uniform(-jitter, jitter) if 0 < i < n else 0
        pts.append((x1 + (x2 - x1) * t + nx * off, y1 + (y2 - y1) * t + ny * off))
    d.line(pts, fill=color, width=width, joint="curve")


def hand_rect(d, box, color, width=4, jitter=2.2):
    x0, y0, x1, y1 = box
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for i in range(4):
        hand_line(d, c[i], c[(i + 1) % 4], color, width, jitter)


def hand_star(d, cx, cy, r, color, width=4):
    pts = []
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        pts.append((cx + r * math.cos(a) + random.uniform(-1.5, 1.5),
                    cy + r * math.sin(a) + random.uniform(-1.5, 1.5)))
    order = [pts[0], pts[2], pts[4], pts[1], pts[3], pts[0]]
    d.line(order, fill=color, width=width, joint="curve")


def draw_char_rot(base, ch, x, y, font, color, angle, stroke=4):
    """單字渲染後旋轉再貼上，做出手寫不規則感。"""
    pad = int(font.size * 0.8)
    tile = Image.new("RGBA", (font.size + pad * 2, font.size + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((pad, pad), ch, font=font, fill=color,
                              stroke_width=stroke, stroke_fill=color)
    tile = tile.rotate(angle, resample=Image.BICUBIC, expand=False)
    base.alpha_composite(tile, (int(x - pad), int(y - pad)))


def draw_title(base, title, emphasis, x, y, size, avail, line_gap=None,
               jitter=True, stroke=4):
    """逐字抖動旋轉的手寫標題，emphasis 子字串標紅。回傳結束的 y。"""
    d = ImageDraw.Draw(base)
    tf = load_font(size)
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    line_gap = line_gap or int(size * 1.25)
    red_idx = set()
    if emphasis:
        pos = title.find(emphasis)
        if pos >= 0:
            red_idx = set(range(pos, pos + len(emphasis)))
    lines, cur = [], []
    for idx, ch in enumerate(title):
        w_now = measure.textlength("".join(c for c, _ in cur) + ch, font=tf)
        if ch == "\n" or w_now > avail:
            lines.append(cur); cur = [] if ch == "\n" else [(ch, idx)]
        else:
            cur.append((ch, idx))
    if cur:
        lines.append(cur)
    cy = y
    for line in lines:
        cx = x
        for ch, idx in line:
            color = RED if idx in red_idx else INK
            dy = random.uniform(-size * 0.06, size * 0.06) if jitter else 0
            ang = random.uniform(-5, 5) if jitter else 0
            draw_char_rot(base, ch, cx, cy + dy, tf, color, ang, stroke)
            cx += measure.textlength(ch, font=tf)
        cy += line_gap
    return cy


def draw_title_center(base, text, cx, cy, size, color=INK, jitter=True, stroke=4):
    """單行置中手寫標題（cx 為中心 x，cy 為頂端 y）。"""
    tf = load_font(size)
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = sum(measure.textlength(ch, font=tf) for ch in text)
    x = cx - tw / 2
    for ch in text:
        dy = random.uniform(-size * 0.05, size * 0.05) if jitter else 0
        ang = random.uniform(-4, 4) if jitter else 0
        draw_char_rot(base, ch, x, cy + dy, tf, color, ang, stroke)
        x += measure.textlength(ch, font=tf)


def hand_circle(d, cx, cy, rx, ry, color, width=8, passes=2):
    pts_passes = []
    for _ in range(passes):
        pts = []
        for i in range(49):
            a = i / 48 * 2 * math.pi
            r1 = rx + random.uniform(-3, 3)
            r2 = ry + random.uniform(-3, 3)
            pts.append((cx + r1 * math.cos(a), cy + r2 * math.sin(a)))
        pts_passes.append(pts)
    for pts in pts_passes:
        d.line(pts, fill=color, width=width, joint="curve")


def fit_mascot(mascot_path, target_h):
    m = remove_white_bg(Image.open(mascot_path))
    ratio = target_h / m.height
    return m.resize((max(1, int(m.width * ratio)), target_h), Image.LANCZOS)
