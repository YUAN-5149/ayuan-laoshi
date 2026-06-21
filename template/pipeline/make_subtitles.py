"""由分段腳本 + 字卡秒數產生燒錄用的 SRT 字幕。

用法:
    python make_subtitles.py segments.txt slides_dir [out.srt]

邏輯：
    - segments.txt 以「單獨一行的 ---」分段，第 i 段對應第 i 張字卡。
    - 每段長度取自 slides_dir/timing.txt（narrate_slides.py 產生，一行一個秒數）。
    - 把每段旁白切成好讀的短句（依標點＋字數），段內時間依字數比例分配。
    - 還原 TTS 用的拆字母縮寫：「L L M」→「LLM」、「A I」→「AI」。
    - 預設輸出到 slides_dir/subtitles.srt（make_video.py 會自動偵測並燒進影片）。
"""
import os
import re
import sys

MAX_CHARS = 22          # 單行最長字數（全形約 22 字在 1080p 好讀）
PUNCT = "，。！？、；：…—,!?;"   # 優先在這些標點後斷句


def collapse_spaced_acronyms(text: str) -> str:
    """把 TTS 拆開的單字母縮寫併回去：'L L M' -> 'LLM'，'A I' -> 'AI'。"""
    def join(m):
        return m.group(0).replace(" ", "")
    # 連續「單一字母＋空白」兩個以上，視為被拆開的縮寫
    return re.sub(r"\b(?:[A-Za-z] ){1,}[A-Za-z]\b", join, text)


def split_chunks(text: str):
    """把一段話切成數個短句。先在標點處切，過長再硬切到 MAX_CHARS。"""
    text = text.strip()
    # 依標點切，保留標點在前句尾
    parts, buf = [], ""
    for ch in text:
        buf += ch
        if ch in PUNCT and len(buf.strip()) >= 6:
            parts.append(buf.strip()); buf = ""
    if buf.strip():
        parts.append(buf.strip())
    # 把過長的句子再硬切
    chunks = []
    for p in parts:
        while len(p) > MAX_CHARS:
            chunks.append(p[:MAX_CHARS]); p = p[MAX_CHARS:]
        if p:
            chunks.append(p)
    # 把太短的句子併進前一句，避免一閃而過
    merged = []
    for c in chunks:
        if merged and len(merged[-1]) + len(c) <= MAX_CHARS:
            merged[-1] += c
        else:
            merged.append(c)
    return merged or [text]


def fmt_ts(t: float) -> str:
    h = int(t // 3600); m = int(t % 3600 // 60)
    s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    seg_path, slides_dir = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(slides_dir, "subtitles.srt")

    with open(seg_path, encoding="utf-8-sig") as f:
        segs = [s.strip() for s in re.split(r"(?m)^\s*---\s*$", f.read()) if s.strip()]

    timing_file = os.path.join(slides_dir, "timing.txt")
    if not os.path.exists(timing_file):
        sys.exit(f"找不到 {timing_file}（請先跑 narrate_slides.py 產生秒數）")
    with open(timing_file, encoding="utf-8") as f:
        durations = [float(x) for x in f if x.strip()]

    if len(durations) != len(segs):
        print(f"⚠ 段數({len(segs)}) 與 timing 行數({len(durations)}) 不一致，依較少者對齊。")
    n = min(len(segs), len(durations))

    blocks = []
    t0 = 0.0
    idx = 1
    for i in range(n):
        text = collapse_spaced_acronyms(segs[i])
        dur = durations[i]
        chunks = split_chunks(text)
        total_chars = sum(len(c) for c in chunks) or 1
        ct = t0
        for j, c in enumerate(chunks):
            share = dur * (len(c) / total_chars)
            start, end = ct, ct + share
            ct = end
            blocks.append(f"{idx}\n{fmt_ts(start)} --> {fmt_ts(end)}\n{c}\n")
            idx += 1
        t0 += dur

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    print(f"OK: {out_path} ｜ {idx-1} 條字幕 ｜ 總長 {t0:.1f}s")


if __name__ == "__main__":
    main()
