---
name: youtube-video
description: 製作並上傳一支 YouTube 知識短片的完整 SOP。當需要發片、做影片、執行每日心跳發現今天還沒發片時使用。涵蓋選題、寫腳本、做投影片、配音、合成影片、上傳 YouTube、更新記憶。
---

# 製作並上傳一支 YouTube 知識短片

工作目錄為本專案根目錄（CLAUDE.md 所在處），以下相對路徑都以此為準。

## 流程

### 1. 選題
- 讀 `MEMORY.md` 的「已發布影片清單」，避免重複。
- 選一個 AI 相關、能在兩分鐘內講清楚的概念（例：什麼是 RAG、什麼是 Token、AI 為什麼會幻覺、什麼是提示工程）。
- 可上網查最近的 AI 熱門話題增加時效性。

### 2. 寫腳本
- 建立 `output\<YYYYMMDD>\` 資料夾，腳本存成 `output\<YYYYMMDD>\script.txt`（UTF-8）。
- 250~400 字（約 1.5~2.5 分鐘旁白）。
- 遵守 CLAUDE.md 的腳本撰寫鐵則（縮寫拆字母、數字中文化、三段結構）。

### 3. 做投影片（4~6 張字卡）
```
python pipeline\make_slide.py "標題文字" "重點內文" output\<日期>\slides\001.png
```
- 第一張：影片標題卡。中間：每個重點一張。最後一張：「謝謝收看／請訂閱」收尾卡。
- 可選：在 `output\<日期>\slides\timing.txt` 每行寫一個秒數控制每張停留時間（需與旁白段落對齊），不寫則平均分配。

### 4. 配音
```
python pipeline\tts.py output\<日期>\script.txt output\<日期>\narration.mp3
```

### 5. 合成影片
```
python pipeline\make_video.py output\<日期>\slides output\<日期>\narration.mp3 output\<日期>\final.mp4
```
- 確認 final.mp4 存在且大小 > 100KB。

### 6. 上傳 YouTube
```
python pipeline\upload_youtube.py output\<日期>\final.mp4 "影片標題" "影片描述`n`n本頻道由 AI Agent 自主經營" "AI,人工智慧,科普"
```
- 標題 ≤ 100 字元，吸睛但不誇大。
- 若 `pipeline\client_secret.json` 不存在，停止並回報使用者需要先完成 YouTube OAuth 設定。
- 上傳成功會印出 `https://youtu.be/<id>`。

### 7. 更新記憶（必做）
- 把影片標題、網址、日期、主題寫進 `MEMORY.md` 已發布清單。
- 若有觀察到前幾支影片的數據，寫下「下次改進方向」。
