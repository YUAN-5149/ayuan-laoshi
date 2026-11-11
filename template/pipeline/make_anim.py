"""把 draw-gpt 畫的「2x2 動畫格」切開、對齊，組成會動的插圖（GIF）。

Codex 的 imagegen 只能出靜圖 PNG（2026-11-09 實測：要求 GIF 會回 "Animated GIF export is unavailable"），
所以改叫 GPT 在一張圖裡畫 4 格連續動作（sprite sheet），再由這支切開組成循環動畫。

用法：
  python pipeline\\make_anim.py <sheet.png> <輸出主檔名> [fps=6] [順序=1,2,3,4,3,2] [noalign]
    （角色會移動的動作，例如鑽到桌下：順序給 1,2,3,4,4,4、第 5 參數 noalign，播一次動作再停在最後一格）
    例：python pipeline\\make_anim.py output\\20261110\\illust\\seg3_xxx.png output\\20261110\\illust\\seg3_anim
產出：
  <輸出主檔名>.png  第 1 格（給 make_slide 當插圖用，字卡排版照舊）
  <輸出主檔名>.gif  循環動畫（make_video 看到同名 .gif 就在插圖框裡播動畫，取代鏡頭微動）
"""
import os
import subprocess
import sys

from PIL import Image, ImageChops

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def split_sheet(path, cols=2, rows=2):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    fw, fh = W // cols, H // rows
    return [im.crop((c * fw, r * fh, c * fw + fw, r * fh + fh)) for r in range(rows) for c in range(cols)]


def anchor(frame):
    """角色腳底中心：和背景色（取四角平均）差異大的像素 → 取最下面 25% 的寬度中心與底邊。"""
    w, h = frame.size
    corners = [frame.getpixel(p) for p in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    diff = ImageChops.difference(frame, Image.new("RGB", frame.size, bg)).convert("L")
    mask = diff.point(lambda v: 255 if v > 40 else 0)
    box = mask.getbbox()
    if not box:
        return w // 2, h
    x0, y0, x1, y1 = box
    legs = mask.crop((0, y1 - (y1 - y0) // 4, w, y1)).getbbox()
    cx = (legs[0] + legs[2]) // 2 if legs else (x0 + x1) // 2
    return cx, y1, bg


def align(frames):
    """以第 1 格腳底位置為準，把其他格平移對齊（GPT 每格位置會差幾個像素，不對齊會抖）。"""
    a0 = anchor(frames[0])
    out = [frames[0]]
    for f in frames[1:]:
        a = anchor(f)
        dx, dy = a0[0] - a[0], a0[1] - a[1]
        bg = a[2] if len(a) > 2 else (250, 245, 235)
        canvas = Image.new("RGB", f.size, bg)
        canvas.paste(f, (dx, dy))
        out.append(canvas)
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sheet, base = sys.argv[1], sys.argv[2]
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    order = [int(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "1,2,3,4,3,2").split(",")]
    # 第 5 參數 noalign：角色本身會移動的動作（走過去、鑽到桌下）不要以腳底對齊，否則場景物件會跟著晃。
    raw = split_sheet(sheet)
    frames = raw if (len(sys.argv) > 5 and sys.argv[5] == "noalign") else align(raw)
    os.makedirs(os.path.dirname(os.path.abspath(base)), exist_ok=True)
    frames[0].save(base + ".png")
    tmp = base + "_frames"
    os.makedirs(tmp, exist_ok=True)
    for i, n in enumerate(order):
        frames[n - 1].save(os.path.join(tmp, f"{i:02d}.png"))
    subprocess.run([FFMPEG, "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%02d.png"),
                    "-vf", "scale=600:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse",
                    "-loop", "0", base + ".gif"], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    print(f"OK: {base}.png ＋ {base}.gif（{len(order)} 幀 @ {fps}fps）")


if __name__ == "__main__":
    main()
