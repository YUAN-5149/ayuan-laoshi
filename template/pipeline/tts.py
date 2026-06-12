"""文字轉語音：預設 edge-tts（免費），設定 ELEVENLABS_API_KEY 後自動改用 ElevenLabs 客製聲音。

用法:
    python tts.py script.txt output.mp3
"""
import asyncio
import os
import sys


async def tts_edge(text: str, out_path: str):
    import edge_tts
    # zh-TW 男聲: zh-TW-YunJheNeural, 女聲: zh-TW-HsiaoChenNeural
    voice = os.environ.get("EDGE_TTS_VOICE", "zh-TW-YunJheNeural")
    communicate = edge_tts.Communicate(text, voice, rate="+8%")
    await communicate.save(out_path)


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


def main():
    script_path, out_path = sys.argv[1], sys.argv[2]
    with open(script_path, encoding="utf-8") as f:
        text = f.read().strip()
    if os.environ.get("ELEVENLABS_API_KEY"):
        tts_elevenlabs(text, out_path)
    else:
        asyncio.run(tts_edge(text, out_path))
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
