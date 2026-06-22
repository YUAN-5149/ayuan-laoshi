"""把投影片圖片 + 旁白音檔合成影片。

用法:
    python make_video.py slides_dir narration.mp3 output.mp4

slides_dir 內放 001.png, 002.png ... (1920x1080)，會平均分配時間。
若 slides_dir 內有 timing.txt（每行一個秒數），則依指定秒數切換。
"""
import glob
import os
import subprocess
import sys

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")

_FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "assets", "fonts")
SUB_FONT = "jf-openhuninn-2.1"   # assets/fonts/openhuninn.ttf 的字型家族名

# 直式（Shorts 9:16）為預設；VIDEO_VERTICAL=0 可切回橫式 16:9。
VERTICAL = os.environ.get("VIDEO_VERTICAL", "1") != "0"
OUT_W, OUT_H = (1080, 1920) if VERTICAL else (1920, 1080)


def _ass_escape(path: str) -> str:
    """把 Windows 路徑轉成 ffmpeg subtitles filter 吃得下的字串（/ 取代 \\、跳脫冒號）。"""
    return path.replace("\\", "/").replace(":", "\\:")


def build_subs_filter(slides_dir: str):
    """slides_dir 內有 subtitles.srt 就回傳燒字幕用的 filter 片段，否則回傳 None。"""
    srt = os.path.join(slides_dir, "subtitles.srt")
    if not os.path.exists(srt):
        return None
    # 直式要避開 Shorts 底部 UI（標題/帳號/進度條），字幕往上抬、字級略調。
    fontsize, marginv = (13, 80) if VERTICAL else (20, 64)
    style = (
        f"FontName={SUB_FONT},Fontsize={fontsize},"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00282C2C,BackColour=&H64000000,"
        f"BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV={marginv},Bold=1"
    )
    return (f"subtitles=filename='{_ass_escape(os.path.abspath(srt))}'"
            f":fontsdir='{_ass_escape(_FONTS_DIR)}'"
            f":force_style='{style}'")


def audio_duration(path: str) -> float:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main():
    slides_dir, audio, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    slides = sorted(glob.glob(os.path.join(slides_dir, "*.png")))
    if not slides:
        sys.exit("no slides found")

    total = audio_duration(audio)
    timing_file = os.path.join(slides_dir, "timing.txt")
    durations = None
    if os.path.exists(timing_file):
        with open(timing_file, encoding="utf-8") as f:
            vals = [float(line) for line in f if line.strip()]
        # timing.txt 必須與投影片數量一致才採用，否則退回平均分配
        if len(vals) == len(slides) and sum(vals) > 0:
            durations = vals
    if durations is None:
        durations = [total / len(slides)] * len(slides)

    # 關鍵修正：等比例縮放，讓各張投影片秒數總和「剛好等於旁白長度」，
    # 避免影片軌比音軌長而出現尾巴定格＋無聲。
    scale = total / sum(durations)
    durations = [d * scale for d in durations]

    fps = 30
    subs = build_subs_filter(slides_dir)

    # 動態（Ken Burns）：每張圖緩慢推近、交替錨點，把靜態 PPT 變成會動的影片。
    # 用「單張靜圖 + zoompan d=幀數」的可靠做法（不用 -loop，避免倍幀）。
    inputs = []
    for img in slides:
        inputs += ["-i", os.path.abspath(img)]
    inputs += ["-i", os.path.abspath(audio)]
    audio_idx = len(slides)

    anchors = [
        ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),  # 置中推近
        ("0", "0"),                                  # 往左上漂
        ("iw-iw/zoom", "ih-ih/zoom"),                # 往右下漂
    ]
    parts = []
    for i, dur in enumerate(durations):
        dframes = max(1, round(dur * fps))
        ax, ay = anchors[i % len(anchors)]
        parts.append(
            f"[{i}:v]scale={OUT_W * 2}:{OUT_H * 2},"
            f"zoompan=z='min(zoom+0.0007,1.12)':d={dframes}:x='{ax}':y='{ay}':"
            f"s={OUT_W}x{OUT_H}:fps={fps},setsar=1[v{i}]"
        )
    parts.append("".join(f"[v{i}]" for i in range(len(slides)))
                 + f"concat=n={len(slides)}:v=1:a=0[vc]")
    if subs:
        parts.append(f"[vc]{subs}[vout]")
        vmap = "[vout]"
        print("（偵測到 subtitles.srt，燒錄字幕）")
    else:
        vmap = "[vc]"

    subprocess.run([
        FFMPEG, "-y", *inputs,
        "-filter_complex", ";".join(parts),
        "-map", vmap, "-map", f"{audio_idx}:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k",
        # -t 鎖在旁白長度（雙保險，杜絕尾巴定格）
        "-t", f"{total:.3f}",
        "-shortest", out_path,
    ], check=True)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
