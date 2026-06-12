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
    if os.path.exists(timing_file):
        with open(timing_file, encoding="utf-8") as f:
            durations = [float(line) for line in f if line.strip()]
    else:
        durations = [total / len(slides)] * len(slides)

    # 用 concat demuxer 串接靜態圖
    concat_path = os.path.join(slides_dir, "_concat.txt")
    with open(concat_path, "w", encoding="utf-8") as f:
        for img, dur in zip(slides, durations):
            f.write(f"file '{os.path.abspath(img)}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{os.path.abspath(slides[-1])}'\n")

    subprocess.run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-i", audio,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", out_path,
    ], check=True)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
