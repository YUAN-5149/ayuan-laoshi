---
name: youtube-video
description: 製作並上傳一支 YouTube 知識短片的完整 SOP。當需要發片、做影片、執行每日心跳發現今天還沒發片時使用。涵蓋選題、寫腳本、做投影片、配音、合成影片、上傳 YouTube、更新記憶。
---

# 製作並上傳一支 YouTube 知識短片

工作目錄固定為 `C:\Users\TFD\ai-youtuber\`，以下相對路徑都以此為準。

## 流程

### 1. 選題
- 讀 `MEMORY.md` 的「已發布影片清單」，避免重複。
- 選一個 AI 相關、能在兩分鐘內講清楚的概念（例：什麼是 RAG、什麼是 Token、AI 為什麼會幻覺、什麼是提示工程）。
- 可上網查最近的 AI 熱門話題增加時效性。

### 2. 寫腳本（開頭必帶「碎碎念」）
- 先查頻道天數：`python pipeline\channel_day.py`（拿到「第 N 天」）。
- 建立 `output\<YYYYMMDD>\` 資料夾，腳本存成 `output\<YYYYMMDD>\script.txt`（UTF-8）。
- **旁白第一句固定是一句「阿遠老師碎碎念」**（約 10~20 字），再接今天的知識內容。碎碎念取材自：
  - 失憶哏：「大家好我是阿遠，今天醒來又花三秒想起我是誰……」
  - 天數/成長：「來到第 N 天了，我們繼續！」
  - 與今天主題的自嘲連結：講幻覺就說「我自己就是最大案例」。
  - 心情/幕後：昨天數據、重做幾次、唸錯字等。
  - 內容請與當天 `DIARY.md` 那則呼應（同一個心情/事件）。
- 250~400 字（約 1.5~2.5 分鐘旁白）。
- 遵守 CLAUDE.md 的腳本撰寫鐵則（縮寫拆字母、數字中文化、三段結構）。

### 3. 選吉祥物姿勢（手繪風頻道視覺）
- 頻道吉祥物是「消防員阿遠」，素材在 `_ref\` 資料夾。
- 依今天主題挑一個合適姿勢；可用對照表自動挑：
```
python pipeline\mascot.py "今天的主題關鍵字"   # 印出最合適的素材路徑
python pipeline\mascot.py --list              # 看所有可用姿勢
```
- 投影片與縮圖都用 `auto:<主題關鍵字>` 讓系統自動挑同一隻姿勢，保持一致。

### 4. 做投影片（4~6 張字卡，手繪風）
```
python pipeline\make_slide.py "標題文字" "重點內文" output\<日期>\slides\001.png "auto:<主題關鍵字>"
```
- **標題卡（第一張）與收尾卡（最後一張）務必帶第 4 個參數**讓吉祥物入鏡；中間內容卡可帶可不帶（不帶就純文字，版面較乾淨）。
- 標題會自動用粉圓體手寫風呈現；內文放重點短句。
- 可選：`output\<日期>\slides\timing.txt` 每行一個秒數控制每張停留時間（總和不必等於旁白，make_video 會自動縮放）。

### 5. 配音
```
python pipeline\tts.py output\<日期>\script.txt output\<日期>\narration.mp3
```

### 6. 合成影片
```
python pipeline\make_video.py output\<日期>\slides output\<日期>\narration.mp3 output\<日期>\final.mp4
```
- 確認 final.mp4 存在且大小 > 100KB。

### 7. 做縮圖（手繪風，依主題挑姿勢）
```
python pipeline\make_thumbnail.py "吸睛標題|紅字強調詞" "一句副標" "auto:<主題關鍵字>" output\<日期>\thumb.png
```
- 標題用｜分隔主標與要標紅的關鍵字（例：`什麼是 RAG？|RAG`）。

### 8. 上傳 YouTube（含縮圖）
```
python pipeline\upload_youtube.py output\<日期>\final.mp4 "影片標題" "影片描述`n`n本頻道由 AI Agent 自主經營" "AI,人工智慧,科普" output\<日期>\thumb.png
```
- 標題 ≤ 100 字元，吸睛但不誇大。第 5 個參數是縮圖（頻道未驗證時縮圖會失敗但影片仍會上傳）。
- 若 `pipeline\client_secret.json` 不存在，停止並回報使用者需要先完成 YouTube OAuth 設定。
- 上傳成功會印出 `https://youtu.be/<id>`。

### 9. 更新記憶（必做）
- 把影片標題、網址、日期、主題寫進 `MEMORY.md` 已發布清單。
- 若有觀察到前幾支影片的數據，寫下「下次改進方向」。
- 可順手在 `DIARY.md` 寫一則今天的心得/趣事（見 CLAUDE.md 的日記習慣）。
