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

    # 逐段快取（2026-11-12 加）：edge-tts 被限流時一支片配音可拖 40 分鐘，心跳第 2 次嘗試又從頭配，
    # 結果兩次都逾時沒上傳。配好的段落存在 <輸出資料夾>\_tts_cache\，同一段文字再跑直接沿用。
    # 只快取 24kHz 的 edge-tts 人聲；降級的機器音（22050Hz）不快取，下次還會重試人聲。
    import hashlib
    import shutil as _sh
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(out_path)), "_tts_cache")
    os.makedirs(cache_dir, exist_ok=True)
    voice_key = os.environ.get("EDGE_TTS_VOICE", "zh-TW-YunJheNeural") + os.environ.get("TTS_ENGINE", "")

    def sample_rate(p):
        out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a:0", "-show_entries",
                              "stream=sample_rate", "-of", "csv=p=0", p], capture_output=True, text=True)
        return out.stdout.strip()

    # 分輪完成（2026-11-15 加）：被限流時整支配音可超過 10 分鐘，Agent 的指令會被自動丟到背景、
    # 它就說「等配音完成通知」結束回合 → 整條產線斷頭（11-11、11-15 兩次全滅）。
    # 所以每次呼叫最多跑 NARRATE_BUDGET_SEC 秒（預設 240），時間到就印 PARTIAL、exit 3；
    # 已配好的段落都在快取裡，**再執行同一個指令會接續**，重複到印出 OK 為止。
    import time as _time
    budget = float(os.environ.get("NARRATE_BUDGET_SEC", "240"))
    t0 = _time.monotonic()
    made_now = 0  # 本次新配的段數；每次呼叫至少配完一段才檢查時間，確保一定有進度

    tmp = tempfile.mkdtemp()
    seg_mp3s, durations = [], []
    try:
        for i, seg in enumerate(segs):
            key0 = hashlib.sha1((voice_key + "|" + seg).encode("utf-8")).hexdigest()[:16]
            is_cached = os.path.exists(os.path.join(cache_dir, key0 + ".mp3"))
            if not is_cached and made_now > 0 and _time.monotonic() - t0 > budget:
                done = sum(1 for s in segs if os.path.exists(os.path.join(
                    cache_dir, hashlib.sha1((voice_key + "|" + s).encode("utf-8")).hexdigest()[:16] + ".mp3")))
                print(f"PARTIAL：已配好 {done}/{len(segs)} 段（存在快取）。配音服務較慢，"
                      f"請【立刻再執行一次同一個指令】接續，重複到印出 OK 為止；不要丟背景、不要結束回合。")
                sys.exit(3)
            mp3 = os.path.join(tmp, f"s{i:03d}.mp3")
            key = hashlib.sha1((voice_key + "|" + seg).encode("utf-8")).hexdigest()[:16]
            cached = os.path.join(cache_dir, key + ".mp3")
            if os.path.exists(cached) and os.path.getsize(cached) > 1000:
                _sh.copy(cached, mp3)
                print(f"（第 {i + 1} 段沿用快取配音）")
            else:
                tts_lib.synth(seg, mp3)
                made_now += 1
                if sample_rate(mp3) == "24000":
                    _sh.copy(mp3, cached)
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
