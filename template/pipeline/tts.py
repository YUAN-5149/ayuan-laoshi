"""文字轉語音，後端依環境變數自動選擇（優先序由上到下）：
  1. GPT-SoVITS 本地 API   －－ 設定 GPT_SOVITS_API（你自己訓練的聲音、離線免費）
  2. ElevenLabs           －－ 設定 ELEVENLABS_API_KEY（雲端客製聲音）
  3. edge-tts             －－ 預設備援（免費，非本人聲音）

用法:
    python tts.py script.txt output.mp3
"""
import asyncio
import os
import subprocess
import sys
import tempfile


async def tts_edge(text: str, out_path: str):
    """edge-tts 逐句合成再串接（短句較不會觸發 NoAudioReceived），每句重試。"""
    import asyncio as _a
    import re
    import shutil
    import edge_tts
    # zh-TW 男聲: zh-TW-YunJheNeural, 女聲: zh-TW-HsiaoChenNeural
    voice = os.environ.get("EDGE_TTS_VOICE", "zh-TW-YunJheNeural")
    rate = os.environ.get("EDGE_TTS_RATE", "+8%")
    parts = [p.strip() for p in re.split(r"(?<=[。！？!?\n])", text) if p.strip()]
    if not parts:
        parts = [text]

    tmpdir = tempfile.mkdtemp()
    seg_files = []
    try:
        for i, part in enumerate(parts):
            seg = os.path.join(tmpdir, f"seg_{i:03d}.mp3")
            done, last_err = False, None
            tries = int(os.environ.get("EDGE_TTS_TRIES", "8"))
            for _ in range(tries):
                try:
                    await edge_tts.Communicate(part, voice, rate=rate).save(seg)
                    if os.path.exists(seg) and os.path.getsize(seg) > 200:
                        done = True
                        break
                except Exception as e:  # NoAudioReceived 等間歇性錯誤
                    last_err = e
                await _a.sleep(1.5)
            if not done:
                raise RuntimeError(f"edge-tts 此句重試後仍失敗：{part!r}（{last_err}）")
            seg_files.append(seg)

        listfile = os.path.join(tmpdir, "list.txt")
        with open(listfile, "w", encoding="utf-8") as f:
            for s in seg_files:
                f.write(f"file '{s}'\n")
        ffmpeg = os.environ.get("FFMPEG", "ffmpeg")
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                        "-c", "copy", out_path], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def tts_elevenlabs(text: str, out_path: str):
    import requests
    api_key = os.environ["ELEVENLABS_API_KEY"]
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "")  # 你客製的聲音 ID
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
        },
        timeout=300,
    )
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)


def tts_gpt_sovits(text: str, out_path: str):
    """呼叫本地 GPT-SoVITS api_v2 服務（你自己訓練的聲音）。

    需要的環境變數:
        GPT_SOVITS_API        本地端點，例如 http://127.0.0.1:9880
        GPT_SOVITS_REF_AUDIO  參考人聲檔(3~10秒, wav)的絕對路徑
        GPT_SOVITS_REF_TEXT   上述參考音檔「逐字」的文字內容
        GPT_SOVITS_REF_LANG   參考音語言(預設 zh)
        GPT_SOVITS_TEXT_LANG  合成文字語言(預設 zh)
    """
    import requests
    base = os.environ["GPT_SOVITS_API"].rstrip("/")
    payload = {
        "text": text,
        "text_lang": os.environ.get("GPT_SOVITS_TEXT_LANG", "zh"),
        "ref_audio_path": os.environ["GPT_SOVITS_REF_AUDIO"],
        "prompt_text": os.environ.get("GPT_SOVITS_REF_TEXT", ""),
        "prompt_lang": os.environ.get("GPT_SOVITS_REF_LANG", "zh"),
        "media_type": "wav",
        "streaming_mode": False,
    }
    resp = requests.post(f"{base}/tts", json=payload, timeout=600)
    resp.raise_for_status()

    # GPT-SoVITS 回傳 wav；產線要 mp3，用 ffmpeg 轉檔
    if out_path.lower().endswith(".wav"):
        with open(out_path, "wb") as f:
            f.write(resp.content)
        return
    ffmpeg = os.environ.get("FFMPEG", "ffmpeg")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(resp.content)
        tmp_wav = tmp.name
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", tmp_wav, "-b:a", "192k", out_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        os.remove(tmp_wav)


def tts_sapi(text: str, out_path: str):
    """Windows 內建離線語音（保底，永遠可用、不需網路）。預設 zh-TW 漢漢。"""
    import shutil
    voice = os.environ.get("SAPI_VOICE", "Microsoft Hanhan Desktop")
    rate = os.environ.get("SAPI_RATE", "-2")  # -10~10，負值較慢
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav = tmp.name
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"try {{ $s.SelectVoice('{voice}') }} catch {{}};"
        f"$s.Rate = {rate};"
        f"$s.SetOutputToWaveFile('{wav}');"
        "$s.Speak([Console]::In.ReadToEnd());$s.Dispose()"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       input=text, text=True, check=True)
        if out_path.lower().endswith(".wav"):
            shutil.move(wav, out_path)
        else:
            ffmpeg = os.environ.get("FFMPEG", "ffmpeg")
            subprocess.run([ffmpeg, "-y", "-i", wav, "-b:a", "192k", out_path],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        if os.path.exists(wav):
            os.remove(wav)


def synth(text: str, out_path: str):
    """單段文字轉語音，依環境變數選後端，edge-tts 失敗自動降級離線語音。"""
    if os.environ.get("GPT_SOVITS_API"):
        tts_gpt_sovits(text, out_path)
    elif os.environ.get("ELEVENLABS_API_KEY"):
        tts_elevenlabs(text, out_path)
    else:
        try:
            asyncio.run(tts_edge(text, out_path))
            if not (os.path.exists(out_path) and os.path.getsize(out_path) > 1000):
                raise RuntimeError("edge-tts 產出為空")
        except Exception as e:
            print(f"edge-tts 失敗，改用 Windows 離線語音保底：{e}")
            tts_sapi(text, out_path)


def main():
    script_path, out_path = sys.argv[1], sys.argv[2]
    with open(script_path, encoding="utf-8") as f:
        text = f.read().strip()
    synth(text, out_path)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
