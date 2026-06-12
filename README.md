# 阿遠老師 🦞 — 自主經營 YouTube 的 AI 網紅（懶人安裝包）

> 靈感來自李宏毅老師的「小金老師」：一個會**自己選題、寫腳本、做投影片、配音、剪片、上傳 YouTube、寫記憶**的 AI Agent。
> 本專案用 **Claude Code** 當 Agent 框架——有 Claude 訂閱就能跑，不需要另外買 API key。

## 架構

```
心跳（Windows 工作排程器，每天 09:00）
   └─> claude -p「心跳」(無頭模式)
         ├─ CLAUDE.md      人格與行為準則（自動載入）
         ├─ HEARTBEAT.md   待辦檢查清單
         ├─ MEMORY.md      長期記憶（發片紀錄、觀眾回饋）
         └─ Skill: youtube-video（製片 SOP）
               ├─ make_slide.py   產生 1080p 字卡
               ├─ tts.py          文字轉語音（免費 edge-tts / 可換 ElevenLabs 本人聲音）
               ├─ make_video.py   ffmpeg 合成影片
               └─ upload_youtube.py  YouTube Data API 上傳
```

## 系統需求

- Windows 10/11
- [Node.js 18+](https://nodejs.org)、[Python 3.10+](https://python.org)、git
- Claude 訂閱（Pro/Max，供 Claude Code 使用）

## 一鍵安裝

```powershell
git clone https://github.com/YUAN-5149/ayuan-laoshi.git
cd ayuan-laoshi
powershell -ExecutionPolicy Bypass -File install.ps1
```

安裝程式會自動：安裝 Claude Code CLI、下載 ffmpeg 並設定 PATH、安裝 Python 套件、
把 Agent 工作區部署到 `%USERPROFILE%\ayuan-laoshi-agent`、註冊每日心跳排程（預設停用）。

自訂選項：

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -AgentName "小金老師" -DailyTime "20:00" -InstallDir "D:\my-agent"
```

## 安裝後的 3 個一次性設定

### 1. Claude Code 登入
```powershell
cd $env:USERPROFILE\ayuan-laoshi-agent
claude          # 進入後輸入 /login，用 Claude 訂閱帳號登入
```
登入後可以直接跟阿遠老師聊聊，確認它知道自己的身分。

### 2. YouTube 上傳授權
1. 到 [Google Cloud Console](https://console.cloud.google.com) 建立專案
2. 「API 和服務」→ 啟用 **YouTube Data API v3**
3. 「憑證」→ 建立 **OAuth 2.0 用戶端 ID**（類型選「桌面應用程式」）
4. 下載 JSON，存成 `<安裝目錄>\pipeline\client_secret.json`
5. 「OAuth 同意畫面」→ 測試使用者加入你的 Google 帳號
6. 手動跑一次心跳，第一次上傳會跳出瀏覽器授權，之後全自動

### 3. 開啟每日自動發片
```powershell
Enable-ScheduledTask -TaskName "AI-YouTuber-Heartbeat"
```

## 測試與維運

```powershell
# 手動觸發一次心跳（看著它跑完整個發片流程）
powershell -ExecutionPolicy Bypass -File $env:USERPROFILE\ayuan-laoshi-agent\heartbeat.ps1

# 查執行紀錄
Get-Content $env:USERPROFILE\ayuan-laoshi-agent\logs\heartbeat-*.log -Tail 50

# 暫停自動發片
Disable-ScheduledTask -TaskName "AI-YouTuber-Heartbeat"
```

## 選配：用你自己的聲音（像小金老師）

預設用免費的微軟台灣中文聲音（男聲雲哲；女聲設環境變數 `EDGE_TTS_VOICE=zh-TW-HsiaoChenNeural`）。
想用本人聲音：到 [ElevenLabs](https://elevenlabs.io) 做 voice cloning，然後：

```powershell
[Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY","你的key","User")
[Environment]::SetEnvironmentVariable("ELEVENLABS_VOICE_ID","你的voiceID","User")
```

`tts.py` 偵測到環境變數會自動切換。

## ⚠️ 守則

- `heartbeat.ps1` 使用 `--dangerously-skip-permissions` 讓無人值守可行——**只在 Agent 工作目錄使用**，不要複製到其他專案。
- 頻道簡介請註明「本頻道由 AI Agent 自主經營」，並在 YouTube Studio 勾選「變造或合成內容」聲明（平台政策要求）。
- 前幾支影片先設 `$env:YT_PRIVACY="unlisted"` 測試品質，滿意再公開。
- `client_secret.json` 與 `token.json` 是機密，已寫進 .gitignore，**絕對不要上傳**。
- 每天心跳會消耗 Claude 訂閱用量（一次發片約一個中型對話）。

## License

MIT
