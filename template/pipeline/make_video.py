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


def find_bgm():
    """找背景配樂：環境變數 AYUAN_BGM 優先，否則 assets/music/bg.*。沒有就回 None。"""
    env = os.environ.get("AYUAN_BGM")
    if env and os.path.exists(env):
        return env
    mdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "music")
    for name in ("bg.mp3", "bg.m4a", "bg.wav", "bg.ogg"):
        p = os.path.join(mdir, name)
        if os.path.exists(p):
            return p
    return None


def load_illust_box(slide_path: str):
    """讀 make_slide 寫的 <字卡>.illust.json；沒有、壞掉或插圖檔不見就回 None（照舊整張推近）。"""
    import json
    side = os.path.splitext(slide_path)[0] + ".illust.json"
    if not os.path.exists(side):
        return None
    try:
        with open(side, encoding="utf-8") as f:
            box = json.load(f)
        if os.path.exists(box["path"]) and box["w"] >= 16 and box["h"] >= 16:
            return box
    except Exception as e:
        print(f"WARN: 讀不到 {side}，該張改用整張推近：{e}")
    return None


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
    next_idx = audio_idx + 1

    anchors = [
        ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),  # 置中推近
        ("0", "0"),                                  # 往左上漂
        ("iw-iw/zoom", "ih-ih/zoom"),                # 往右下漂
    ]
    # 插圖字卡的「框內鏡頭微動」：字卡文字不動，只有插圖在框裡整段持續慢慢動（金主 2026-10-24 訂）。
    # 用 on/D（輸出幀/總幀，D 在下面換成實際幀數）算位置，整張字卡從頭動到尾；三種動法輪流，避免每張都一樣。
    amp = float(os.environ.get("AYUAN_ILLUST_MOTION", "0.12"))
    center = ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)")
    illust_moves = [
        (f"1+{amp}*on/D", *center),                          # 推近
        (f"1+{amp}-{amp}*on/D", *center),                    # 拉遠
        (f"1+{amp}", "(iw-iw/zoom)*on/D", "ih/2-(ih/zoom/2)"),  # 左→右平移
    ]
    parts = []
    n_illust = 0
    for i, dur in enumerate(durations):
        dframes = max(1, round(dur * fps))
        box = load_illust_box(slides[i])
        if box:
            # 字卡本體靜止，插圖放大 4 倍再 zoompan（降低整數座標造成的抖動），疊回原位。
            z, mx, my = (e.replace("/D", f"/{dframes}") for e in illust_moves[n_illust % len(illust_moves)])
            n_illust += 1
            w, h = box["w"] // 2 * 2, box["h"] // 2 * 2
            inputs += ["-i", box["path"]]
            parts.append(
                f"[{i}:v]scale={OUT_W}:{OUT_H},setsar=1,"
                f"loop=loop={dframes - 1}:size=1:start=0,setpts=N/{fps}/TB[bg{i}]"
            )
            parts.append(
                f"[{next_idx}:v]scale={w * 4}:{h * 4},"
                f"zoompan=z='{z}':d={dframes}:x='{mx}':y='{my}':s={w}x{h}:fps={fps},setsar=1[il{i}]"
            )
            parts.append(f"[bg{i}][il{i}]overlay={box['x']}:{box['y']}:shortest=1,format=yuv420p[v{i}]")
            next_idx += 1
            continue
        ax, ay = anchors[i % len(anchors)]
        parts.append(
            f"[{i}:v]scale={OUT_W * 2}:{OUT_H * 2},"
            f"zoompan=z='min(zoom+0.0007,1.12)':d={dframes}:x='{ax}':y='{ay}':"
            f"s={OUT_W}x{OUT_H}:fps={fps},setsar=1,format=yuv420p[v{i}]"
        )
    if n_illust:
        print(f"（{n_illust} 張插圖字卡套用框內鏡頭微動）")
    parts.append("".join(f"[v{i}]" for i in range(len(slides)))
                 + f"concat=n={len(slides)}:v=1:a=0[vc]")
    if subs:
        parts.append(f"[vc]{subs}[vout]")
        vmap = "[vout]"
        print("（偵測到 subtitles.srt，燒錄字幕）")
    else:
        vmap = "[vc]"

    # 背景配樂（選填）：偵測到就低音量墊在旁白下、結尾淡出。
    bgm = find_bgm()
    if bgm:
        vol = os.environ.get("AYUAN_BGM_VOLUME", "0.12")
        inputs += ["-stream_loop", "-1", "-i", os.path.abspath(bgm)]
        fade_st = max(0.0, total - 2.0)
        parts.append(
            f"[{audio_idx}:a]volume=1.0[an];"
            f"[{next_idx}:a]volume={vol},afade=t=out:st={fade_st:.2f}:d=2[am];"
            f"[an][am]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
        )
        amap = "[aout]"
        print(f"（偵測到背景配樂 {os.path.basename(bgm)}，音量 {vol}）")
    else:
        amap = f"{audio_idx}:a"

    subprocess.run([
        FFMPEG, "-y", *inputs,
        "-filter_complex", ";".join(parts),
        "-map", vmap, "-map", amap,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k",
        # -t 鎖在旁白長度（雙保險，杜絕尾巴定格）
        "-t", f"{total:.3f}",
        "-shortest", out_path,
    ], check=True)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
