"""產生一首自製的輕柔背景配樂（100% 原創、無版權疑慮）。

用法:
    python make_bgm.py [out.mp3]     # 預設 ../assets/music/bg.mp3

設計：C–G–Am–F（I–V–vi–IV）柔和 pad 進行，純正弦＋輕微泛音、慢起音，
低音量當「氛圍墊底」用（make_video 會再壓低音量混在旁白下面）。
換首歌：直接把你喜歡的無版權音樂放成 assets/music/bg.mp3 即可（例：YouTube 創作者音效庫）。
"""
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")

# 和弦（三和音的頻率，Hz）；每個和弦持續 chord_sec 秒
CHORDS = [
    [261.63, 329.63, 392.00],   # C
    [196.00, 246.94, 293.66],   # G
    [220.00, 261.63, 329.63],   # Am
    [174.61, 220.00, 261.63],   # F
]
CHORD_SEC = 4.0
REPEATS = 2   # 整段 = 4 和弦 × 4 秒 × 2 = 32 秒


def note(freq, dur):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # 基音 + 弱八度泛音，聲音較圓潤
    wave_ = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t)
    # 慢起音 / 慢收尾包絡（避免爆音）
    env = np.ones_like(t)
    a = int(SR * 0.5)   # attack 0.5s
    r = int(SR * 0.8)   # release 0.8s
    env[:a] = np.linspace(0, 1, a)
    env[-r:] = np.linspace(1, 0, r)
    # 輕微顫音增加溫度
    trem = 1 + 0.05 * np.sin(2 * np.pi * 0.2 * t)
    return wave_ * env * trem


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "music", "bg.mp3")

    seg = []
    for _ in range(REPEATS):
        for chord in CHORDS:
            mix = np.zeros(int(SR * CHORD_SEC))
            for f in chord:
                mix += note(f, CHORD_SEC)
            mix += 0.6 * note(chord[0] / 2, CHORD_SEC)   # 低八度貝斯墊底
            seg.append(mix)
    audio = np.concatenate(seg)
    audio /= np.max(np.abs(audio)) + 1e-9     # 正規化
    audio *= 0.6                               # 留 headroom
    pcm = (audio * 32767).astype(np.int16)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    wav_path = out + ".tmp.wav"
    with wave.open(wav_path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run([FFMPEG, "-y", "-i", wav_path, "-codec:a", "libmp3lame",
                    "-b:a", "128k", out], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(wav_path)
    print(f"OK: {out}（{len(audio)/SR:.0f}s）")


if __name__ == "__main__":
    main()
