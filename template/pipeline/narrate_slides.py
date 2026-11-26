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
    made_now = 0  # 本次嘗試配音的段數；每次呼叫至少試過一段才檢查時間，確保一定有進度

    # 耐心重試人聲（2026-11-25 加）：11-24 只有 YunJhe 這個聲音間歇 NoAudioReceived（其他聲音正常），
    # 舊流程一段失敗就立刻降級漢漢機器音。現在 edge-tts 失敗的段落先「跳過」、其他段照配，
    # 結束時印 PARTIAL exit 3 讓 Agent 重跑同一指令再試；第一次失敗起超過 NARRATE_PATIENCE_SEC
    # （預設 1200 秒＝20 分鐘）仍配不出來，才對剩下的段落降級機器音保發片。
    # 計時存在 _tts_cache\_first_fail.txt，跨次呼叫延續。設 NARRATE_PATIENCE_SEC=0 等於舊行為。
    patience = float(os.environ.get("NARRATE_PATIENCE_SEC", "600"))  # 11-27 由 1200 降為 600
    fail_mark = os.path.join(cache_dir, "_first_fail.txt")
    use_edge = not (os.environ.get("GPT_SOVITS_API") or os.environ.get("ELEVENLABS_API_KEY"))

    def waited():
        try:
            with open(fail_mark, encoding="utf-8") as f:
                return _time.time() - float(f.read().strip())
        except (OSError, ValueError):
            return 0.0

    def mark_fail():
        if not os.path.exists(fail_mark):
            with open(fail_mark, "w", encoding="utf-8") as f:
                f.write(str(_time.time()))

    def try_edge(seg, mp3):
        """只試 edge-tts 人聲，成功（24kHz）回 True；失敗不降級。"""
        import asyncio
        # 2026-11-27：YunJhe 對特定字串「固定」失敗（同一句連打必敗、改參數/標點/簡體都救不了），
        # tts_edge 內建的 5 次重試＋冷卻 20/40 秒每句白耗 3~5 分鐘 → 11-25、11-27 整次逾時沒上傳。
        # 跨輪重試交給本程式的耐心機制，這裡每句只快速試 2 次、不冷卻。
        os.environ.setdefault("EDGE_TTS_TRIES", "2")
        os.environ["EDGE_TTS_COOLDOWNS"] = os.environ.get("NARRATE_EDGE_COOLDOWNS", "")
        try:
            asyncio.run(tts_lib.tts_edge(seg, mp3))
            return os.path.exists(mp3) and os.path.getsize(mp3) > 1000 and sample_rate(mp3) == "24000"
        except Exception as e:
            print(f"edge-tts 這段暫時配不出來，先跳過、稍後重試：{e}")
            return False

    def n_done():
        return sum(1 for s in segs if os.path.exists(os.path.join(
            cache_dir, hashlib.sha1((voice_key + "|" + s).encode("utf-8")).hexdigest()[:16] + ".mp3")))

    give_up = use_edge and patience > 0 and waited() > patience
    if give_up:
        print(f"⚠ 人聲已重試超過 {patience:.0f} 秒仍有段落失敗，剩下的段落降級機器音保發片。")

    tmp = tempfile.mkdtemp()
    seg_mp3s, durations = [], []
    skipped = 0
    try:
        for i, seg in enumerate(segs):
            key0 = hashlib.sha1((voice_key + "|" + seg).encode("utf-8")).hexdigest()[:16]
            is_cached = os.path.exists(os.path.join(cache_dir, key0 + ".mp3"))
            if not is_cached and made_now > 0 and _time.monotonic() - t0 > budget:
                print(f"PARTIAL：已配好 {n_done()}/{len(segs)} 段（存在快取）。配音服務較慢，"
                      f"請【立刻再執行一次同一個指令】接續，重複到印出 OK 為止；不要丟背景、不要結束回合。")
                sys.exit(3)
            mp3 = os.path.join(tmp, f"s{i:03d}.mp3")
            key = hashlib.sha1((voice_key + "|" + seg).encode("utf-8")).hexdigest()[:16]
            cached = os.path.join(cache_dir, key + ".mp3")
            if os.path.exists(cached) and os.path.getsize(cached) > 1000:
                _sh.copy(cached, mp3)
                print(f"（第 {i + 1} 段沿用快取配音）")
            elif use_edge and patience > 0 and not give_up:
                made_now += 1
                if try_edge(seg, mp3):
                    _sh.copy(mp3, cached)
                else:
                    mark_fail()
                    skipped += 1
                    continue
            elif give_up:
                # 已等超過耐心上限 → 直接機器音（不再跑一輪 edge 重試，否則每段又耗數分鐘、超出預算無限 PARTIAL）
                if skipped == 0:
                    tts_lib.alert_fallback(RuntimeError(f"人聲重試超過 {patience:.0f} 秒仍失敗"))
                skipped = -1  # 只告警一次（之後不再進 PARTIAL 判斷，見下方 skipped > 0）
                tts_lib.tts_sapi(seg, mp3)
                made_now += 1
            else:
                tts_lib.synth(seg, mp3)  # 非 edge 後端（GPT-SoVITS / ElevenLabs）或 NARRATE_PATIENCE_SEC=0 → 原本行為
                made_now += 1
                if sample_rate(mp3) == "24000":
                    _sh.copy(mp3, cached)
            seg_mp3s.append(mp3)
            durations.append(duration(mp3))

        if skipped > 0:
            print(f"PARTIAL：已配好 {n_done()}/{len(segs)} 段，有 {skipped} 段人聲暫時失敗"
                  f"（已重試 {waited():.0f}/{patience:.0f} 秒）。請【立刻再執行一次同一個指令】接續，"
                  f"重複到印出 OK 為止；不要丟背景、不要結束回合。")
            sys.exit(3)

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

    if os.path.exists(fail_mark):  # 全部配好 → 清掉計時，之後同一天改稿重配時重新計算耐心
        os.remove(fail_mark)
    print(f"OK: {out_path} ｜ 段數={len(segs)} ｜ 總長={sum(durations):.1f}s ｜ 各段={[round(d,1) for d in durations]}")


if __name__ == "__main__":
    main()
