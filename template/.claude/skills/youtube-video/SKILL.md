---
name: youtube-video
description: 製作並上傳一支 YouTube 知識短片的完整 SOP。當需要發片、做影片、執行每日心跳發現今天還沒發片時使用。涵蓋選題、寫腳本、做投影片、配音、合成影片、上傳 YouTube、更新記憶。
---

# 製作並上傳一支 YouTube 知識短片

工作目錄＝Agent 根目錄（這個 skill 上面三層的目錄，內含 CLAUDE.md / MEMORY.md / pipeline/）。以下所有相對路徑都以此為準。被心跳呼叫時，`heartbeat.ps1` 已經 `Set-Location $PSScriptRoot` 設好 cwd，不要自己再 cd 到別處。

## 流程

### 1. 選題
- 讀 `MEMORY.md` 的「已發布影片清單」，避免重複。
- **若 `ANALYTICS.md` 存在，先讀它**：看哪幾支留存%／觀看數高，複製那支的選題方向、比喻風格、節奏；低留存的方向少碰。（這份由 `python pipeline\fetch_analytics.py` 更新，需先做過一次性授權。）
- 選一個 AI 相關、能在兩分鐘內講清楚的概念（例：什麼是 RAG、什麼是 Token、AI 為什麼會幻覺、什麼是提示工程）。
- 可上網查最近的 AI 熱門話題增加時效性。

### 2. 寫「分段腳本」（每段對應一張字卡，前 3 秒必須是鉤子）
- 先查頻道天數：`python pipeline\channel_day.py`（拿到「第 N 天」）。
- 建立 `output\<YYYYMMDD>\` 資料夾，腳本存成 `output\<YYYYMMDD>\segments.txt`（UTF-8）。
- **關鍵：用「單獨一行的 `---`」分隔每一段，每段對應一張字卡**（段數＝字卡張數，這樣語音才會跟字卡同步）。
- **🪝 前 3 秒鐵則：第一段（標題卡）開頭第一句必須是「鉤子」，不是自我介紹。** 觀眾前 2~3 秒沒被勾住就滑走。鉤子＝一個讓人想知道答案的問題或反差，例：
  - 「L L M 其實只是一台超強的『猜字』機器？」
  - 「A I 為什麼會一本正經地胡說八道？」
  - 「你每天在用，但九成的人說不出它在幹嘛——」
  - **絕對不要用「大家好我是阿遠」這種自我介紹當第一句。**
- **碎碎念（失憶哏／天數成長／自嘲）縮成半句，接在鉤子後面，或移到收尾**，不要佔開場。取材：失憶哏、「第 N 天了」、昨天數據、幕後心情、與 `DIARY.md` 呼應。
- 每段對應字卡內容：那段旁白講的，就是那張字卡的重點。全片合計 250~400 字。
- 遵守 CLAUDE.md 腳本鐵則（縮寫拆字母如 A I、數字中文化、結構：鉤子→概念→好處→收尾訂閱）。

### 3. 選吉祥物姿勢（手繪風頻道視覺）
- 頻道吉祥物素材在 `_ref\` 資料夾。**如果 `_ref\` 不存在或是空的，跳過這步**——投影片與縮圖的吉祥物參數仍可照常傳 `auto:<關鍵字>`，產生器會自動降級成「沒有吉祥物」的版本（不會崩潰）。
- 有素材時：依今天主題挑一個合適姿勢，可用對照表自動挑：
```
python pipeline\mascot.py "今天的主題關鍵字"   # 印出最合適的素材路徑
python pipeline\mascot.py --list              # 看所有可用姿勢
```
- 投影片與縮圖都用 `auto:<主題關鍵字>` 讓系統自動挑同一隻姿勢，保持一致。

### 4. 做投影片（4~6 張字卡，手繪風）
```
python pipeline\make_slide.py "標題文字" "重點內文" output\<日期>\slides\001.png "auto:<主題關鍵字>"
```
- **張數必須等於 segments.txt 的段數**（每段一張，語音才會對齊）。
- **標題卡與收尾卡務必帶第 4 個參數**讓吉祥物入鏡（吉祥物會自動翻成看向左邊、朝內文）；中間內容卡可省略。
- 內文用「｜」分隔多個重點（會變成紅點項目符號）；別只放一句話，內容要夠。

### 5. 逐段配音並自動對齊字卡（語音／字卡同步）
```
python pipeline\narrate_slides.py output\<日期>\segments.txt output\<日期>\slides output\<日期>\narration.mp3
```
- 每段各自配音、量測秒數，自動產生**與字卡同步**的 narration.mp3 與 timing.txt（不必手寫 timing）。
- 男聲 zh-TW-YunJheNeural；edge-tts 抽風會自動重試 10 次、再不行才降級離線語音。

### 5.5 產生字幕（燒進影片，必做）
```
python pipeline\make_subtitles.py output\<日期>\segments.txt output\<日期>\slides
```
- 讀 segments.txt + slides\timing.txt，自動切短句、依字數分配時間，輸出 `slides\subtitles.srt`。
- 會自動把 TTS 拆開的縮寫還原（「L L M」→「LLM」），字幕上不會出現奇怪空格。
- 一定要在第 5 步（narrate_slides 產生 timing.txt）之後、第 6 步合成影片之前跑。

### 6. 合成影片
```
python pipeline\make_video.py output\<日期>\slides output\<日期>\narration.mp3 output\<日期>\final.mp4
```
- 確認 final.mp4 存在且大小 > 100KB。
- **若 slides\ 內有 subtitles.srt，make_video 會自動用品牌字型把字幕燒進影片**（不必另外下參數）。

### 7. 做縮圖（手繪風，依主題挑姿勢）
```
python pipeline\make_thumbnail.py "吸睛標題|紅字強調詞" "一句副標" "auto:<主題關鍵字>" output\<日期>\thumb.png
```
- 標題用｜分隔主標與要標紅的關鍵字（例：`什麼是 RAG？|RAG`）。

### 8. 上傳 YouTube（含縮圖）
```
python pipeline\upload_youtube.py output\<日期>\final.mp4 "影片標題" "影片描述" "tag1,tag2,..." output\<日期>\thumb.png
```
- 標題 ≤ 100 字元，吸睛但不誇大；標題前段放主關鍵字（例「什麼是 LLM？」）。
- **描述 SEO（前兩行最重要，搜尋/推薦只吃得到前兩行）**：
  - 第 1~2 行：用自然句子塞主關鍵字與同義詞（例：「LLM 大型語言模型是什麼？用最白話的比喻three分鐘搞懂 AI 怎麼『猜字』。」）。
  - 中間：3~5 句補充內容、可放「上一集／系列」連結。
  - 結尾固定加 3~6 個 hashtag：`#AI #人工智慧 #科普 #<主題英文> #<主題中文>`（例 `#LLM #大型語言模型`）。
  - 最後一行固定：`本頻道由 AI Agent 自主經營`。
  - upload_youtube.py 會自動把描述裡的 hashtag 同步補進 tags，描述沒寫到的主題詞也記得放進第 4 個參數。
- **tags（第 4 參數）**：除了通用 `AI,人工智慧,科普`，**務必加上本集主題的中英關鍵字**（例 `LLM,大型語言模型,Large Language Model,生成式AI`）。逗號分隔、勿留空。
- 第 5 個參數是縮圖（頻道未驗證時縮圖會失敗但影片仍會上傳）。
- 若 `pipeline\client_secret.json` 不存在，停止並回報使用者需要先完成 YouTube OAuth 設定。
- 上傳成功會印出 `https://youtu.be/<id>`。

### 9. 更新記憶（必做）
- 把影片標題、網址、日期、主題寫進 `MEMORY.md` 已發布清單。
- **每筆紀錄必須含發布標記 `<!-- PUBLISHED:YYYY-MM-DD -->`**（YYYY-MM-DD 用今天日期）。心跳腳本以這個標記判斷今天是否已發片，沒寫會被視為沒發片、隔天會重跑。範例：
  ```
  - 2026-06-21 《什麼是 RAG？》 https://youtu.be/xxxx 主題:RAG <!-- PUBLISHED:2026-06-21 -->
  ```
- 若有觀察到前幾支影片的數據，寫下「下次改進方向」。
- 可順手在 `DIARY.md` 寫一則今天的心得/趣事（見 CLAUDE.md 的日記習慣）。
