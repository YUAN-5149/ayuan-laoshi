"""逐張字卡對齊旁白：每段旁白各自配音、量測秒數，產生與字卡同步的 narration.mp3 + timing.txt。

腳本檔以「單獨一行的 ---」分隔每張字卡的旁白，段數需與字卡張數相同。

用法:
    python narrate_slides.py script_segments.txt slides_dir narration.mp3
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

import tts as tts_lib

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")


def duration(path):
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main():
    script_path, slides_dir, out_path = sys.argv[1:4]
    with open(script_path, encoding="utf-8") as f:
        raw = f.read()
    segs = [s.strip() for s in re.split(r"(?m)^\s*---\s*$", raw) if s.strip()]
    if not segs:
        sys.exit("腳本沒有內容")

    n_slides = len(glob.glob(os.path.join(slides_dir, "*.png")))
    if n_slides and n_slides != len(segs):
        print(f"⚠ 警告：旁白段數({len(segs)}) 與字卡張數({n_slides}) 不一致，請對齊。")

    tmp = tempfile.mkdtemp()
    seg_mp3s, durations = [], []
    try:
        for i, seg in enumerate(segs):
            mp3 = os.path.join(tmp, f"s{i:03d}.mp3")
            tts_lib.synth(seg, mp3)
            seg_mp3s.append(mp3)
            durations.append(duration(mp3))

        listf = os.path.join(tmp, "list.txt")
        with open(listf, "w", encoding="utf-8") as f:
            for m in seg_mp3s:
                f.write(f"file '{m}'\n")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listf,
                        "-c", "copy", out_path], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with open(os.path.join(slides_dir, "timing.txt"), "w", encoding="utf-8") as f:
            for d in durations:
                f.write(f"{d:.3f}\n")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"OK: {out_path} ｜ 段數={len(segs)} ｜ 總長={sum(durations):.1f}s ｜ 各段={[round(d,1) for d in durations]}")


if __name__ == "__main__":
    main()
