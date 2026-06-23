# -*- coding: utf-8 -*-
"""把 _ref 的阿遠素材整理成 SDXL LoRA 訓練資料集。

輸出到 _lora_dataset/：每張 1024x1024 白底 PNG + 同名 .txt caption。
觸發詞 ayuanff（生成時打這個詞就會召喚阿遠）。caption 描述「會變動的東西」
（姿勢/道具/同框物件），讓 LoRA 把不變的「角色本身」綁到觸發詞、其餘可編輯。

用法: python pipeline/prep_lora_dataset.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "_ref")
OUT = os.path.join(ROOT, "_lora_dataset")
TRIGGER = "ayuanff"
SIZE = 1024

# 來源檔 → caption（觸發詞 + 變動描述；不要描述固定不變的長相細節）
ITEMS = [
    ("黃色-指向前方介紹.png",
     "ayuanff, 3d chibi firefighter mascot, pointing to the side with one hand, friendly smile, plain white background"),
    ("黃色-消防機器人2.png",
     "ayuanff, 3d chibi firefighter mascot, standing next to a red firefighting robot tank, plain white background"),
    ("黃色-救援犬搜救.png",
     "ayuanff, 3d chibi firefighter mascot, holding a leash with a search and rescue dog beside him, determined expression, plain white background"),
    ("黃色-放水瞄準子.png",
     "ayuanff, two 3d chibi firefighters spraying water from a fire hose, plain white background"),
    ("黃色-圓盤切割機.png",
     "ayuanff, 3d chibi firefighter mascot, holding a disc cutter rescue saw, plain white background"),
    ("黃色-電動油壓破壞器.png",
     "ayuanff, 3d chibi firefighter mascot, holding a hydraulic rescue spreader tool, plain white background"),
]


def square_white(im, size):
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    w, h = im.size
    side = max(w, h)
    canvas = Image.new("RGB", (side, side), (255, 255, 255))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for i, (fname, caption) in enumerate(ITEMS, 1):
        src = os.path.join(REF, fname)
        if not os.path.exists(src):
            print("  缺檔，跳過:", fname)
            continue
        img = square_white(Image.open(src), SIZE)
        stem = "%02d" % i
        img.save(os.path.join(OUT, stem + ".png"))
        with open(os.path.join(OUT, stem + ".txt"), "w", encoding="utf-8") as f:
            f.write(caption)
        n += 1
        print("  OK %s.png  <- %s" % (stem, fname))
    print("\n完成 %d 張 -> %s" % (n, OUT))
    print("觸發詞: %s（生圖 prompt 打這個詞召喚阿遠）" % TRIGGER)


if __name__ == "__main__":
    main()
