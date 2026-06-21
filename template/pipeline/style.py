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
               jitter=True, stroke=0, highlight=None):
    """逐字輕微抖動的手寫標題，emphasis 子字串標紅。回傳結束的 y。

    stroke 預設 0：粉圓體本身已夠粗，加描邊會糊成一團（故不再描邊）。
    highlight 不為 None 時，在 emphasis 文字後方加一道螢光筆塗痕（傳 RGB tuple）。
    """
    tf = load_font(size)
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    line_gap = line_gap or int(size * 1.25)
    red_idx = set()
    if emphasis:
        pos = title.find(emphasis)
        if pos >= 0:
            red_idx = set(range(pos, pos + len(emphasis)))
    # 斷行：強調詞當整塊不拆、空白當斷點（與 fit_title_size 一致）
    tok_lines = _wrap_tokens(title_tokens(title, emphasis), tf, measure, avail)

    # 第一階段：把詞元攤回逐字並算每個字的座標
    placed = []  # (ch, idx, cx, cy)
    cy = y
    for line in tok_lines:
        cx = x
        for text, start in line:
            for j, ch in enumerate(text):
                placed.append((ch, start + j, cx, cy))
                cx += measure.textlength(ch, font=tf)
        cy += line_gap

    # 第二階段：emphasis 連續區段先畫螢光底，再畫字（字壓在螢光上）
    if highlight and red_idx:
        runs, run = [], []
        for ch, idx, px, py in placed:
            if idx in red_idx:
                run.append((ch, px, py))
            elif run:
                runs.append(run); run = []
        if run:
            runs.append(run)
        for run in runs:
            x0 = run[0][1]
            x1 = run[-1][1] + measure.textlength(run[-1][0], font=tf)
            ry = run[0][2]
            marker_highlight(base, (x0, ry + size * 0.12, x1, ry + size * 0.92), highlight)

    for ch, idx, px, py in placed:
        color = RED if idx in red_idx else INK
        dy = random.uniform(-size * 0.035, size * 0.035) if jitter else 0
        ang = random.uniform(-2.5, 2.5) if jitter else 0
        draw_char_rot(base, ch, px, py + dy, tf, color, ang, stroke)
    return cy


def draw_title_center(base, text, cx, cy, size, color=INK, jitter=True, stroke=0):
    """單行置中手寫標題（cx 為中心 x，cy 為頂端 y）。"""
    tf = load_font(size)
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = sum(measure.textlength(ch, font=tf) for ch in text)
    x = cx - tw / 2
    for ch in text:
        dy = random.uniform(-size * 0.03, size * 0.03) if jitter else 0
        ang = random.uniform(-2.5, 2.5) if jitter else 0
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


def marker_highlight(base, box, color, jitter=3.0):
    """在文字後方畫一道手繪螢光筆塗痕（半透明、來回兩筆），讓關鍵詞跳出來。"""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cy = (y0 + y1) / 2
    h = (y1 - y0)
    width = max(8, int(h * 0.72))
    # 來回兩筆，模擬螢光筆塗抹的不勻
    for pass_i in range(2):
        oy = cy + random.uniform(-jitter, jitter) + (h * 0.06 if pass_i else -h * 0.06)
        hand_line(ld, (x0 - h * 0.12, oy), (x1 + h * 0.12, oy),
                  color + (150,), width, jitter, seg=24)
    base.alpha_composite(layer)


def title_tokens(title, emphasis=""):
    """把標題切成「不可拆」的詞元：強調詞整塊不拆、空白當斷點、其餘逐字。

    回傳 list[(text, start_idx)]，start_idx 是該詞元在原字串的起始位置（給標紅用）。
    """
    toks = []
    i = 0
    n = len(title)
    while i < n:
        if emphasis and title.startswith(emphasis, i):
            toks.append((emphasis, i)); i += len(emphasis); continue
        ch = title[i]
        if ch == " ":
            toks.append((" ", i))
        elif ch == "\n":
            toks.append(("\n", i))
        else:
            toks.append((ch, i))
        i += 1
    return toks


def _wrap_tokens(toks, tf, measure, avail_w):
    """把詞元貪婪斷行成多行；強調詞不會被拆開。回傳 list[list[(text, idx)]]。"""
    lines, cur, cur_w = [], [], 0.0
    for text, idx in toks:
        if text == "\n":
            lines.append(cur); cur, cur_w = [], 0.0; continue
        w = measure.textlength(text, font=tf)
        if cur and cur_w + w > avail_w:
            lines.append(cur); cur, cur_w = [], 0.0
        if not cur and text == " ":
            continue  # 行首不留空白
        cur.append((text, idx)); cur_w += w
    if cur:
        lines.append(cur)
    return lines


def fit_title_size(title, avail_w, avail_h, max_size, min_size=48,
                   line_gap_ratio=1.35, emphasis=""):
    """挑出能塞進 (avail_w, avail_h) 的最大字級；強調詞當整塊不拆。回傳 (size, line_gap)。"""
    toks = title_tokens(title, emphasis)
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for size in range(max_size, min_size - 1, -4):
        tf = load_font(size)
        line_gap = int(size * line_gap_ratio)
        lines = _wrap_tokens(toks, tf, measure, avail_w)
        widest = max((sum(measure.textlength(t, font=tf) for t, _ in ln)
                      for ln in lines), default=0)
        if len(lines) * line_gap <= avail_h and widest <= avail_w:
            return size, line_gap
    return min_size, int(min_size * line_gap_ratio)


def fit_mascot(mascot_path, target_h, flip=False):
    """去背並縮放吉祥物；flip=True 水平翻轉（讓角色看向左邊）。"""
    m = remove_white_bg(Image.open(mascot_path))
    if flip:
        m = m.transpose(Image.FLIP_LEFT_RIGHT)
    ratio = target_h / m.height
    return m.resize((max(1, int(m.width * ratio)), target_h), Image.LANCZOS)
