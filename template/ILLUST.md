# ILLUST.md — 每日插圖指南（消防員阿遠 3D 公仔風）

> 2026-09-06 起：金主訂了 ChatGPT 月費並開通生圖，**每支片可以生 4 張插圖**（不花 API 錢，走月費額度）。
> 插圖讓字卡從「純文字」升級成「有畫面」，是目前最能拉高質感的一步。
> **2026-10-24 起（金主訂）：插圖一律以「消防員阿遠」素材為主要範本**——每次生圖都要帶參考圖 `_style\sheet.jpg`，
> 讓阿遠親自演出比喻，整個頻道的畫面長同一個樣。不再生沒有阿遠的泛用 Q 版公仔。

## 什麼時候用
每天做字卡前先生圖。**4 張的建議分配**（以 5 段 Shorts 為例，系列片／GitHub 片同）：
- 標題卡用**吉祥物阿遠**（品牌識別），第 2~5 段 → **各配一張插圖**，正好 4 張
- 收尾段若要催訂閱，也可改回吉祥物、把該張插圖挪到別段
- **週日阿遠實測**：阿遠插圖**至少 2 張、最多 4 張**（實驗前、得出結論），結果揭曉的字卡改用 `ask_ai.py` 產的對話截圖卡當插圖（不算進生圖額度）。
- 配角規則照下方「配角」段，比例以實際插圖張數計算（有配角的不超過一半）。

## 範本素材（阿遠長什麼樣）
- 正本來源：金主桌面 `C:\Users\高知淵\Desktop\阿遠老師\阿遠老師素材(正黃色)\`（設定表、各種姿勢、場景圖、工具圖）。
- 生圖用的參考圖已複製到工作區 **`_style\`**（英文檔名，排程傳路徑才不會出錯）：
  - **`sheet.jpg`** ＝ 角色設定表 CHIBA-01（三視圖＋表情＋動作）——**每次生圖都帶這張**
  - `scene_truck.png`（雲梯車場景）、`pose_light.png`（搬照明燈）、`pose_welcome.png`（張手歡迎）＝風格對照用
- 阿遠外型（寫 prompt 時照抄，別自己改）：淺綠頭盔＋咖啡色盔飾、黃色消防衣＋螢光綠反光條、灰色半罩口罩、
  黑手套黑靴、背後灰色空氣瓶；3D 軟膠公仔質感，大頭 Q 版比例。

## 四種用途（4 張裡**至少 3 張要有阿遠**；需要第二個人時見下方「配角」）
| 類型 | 什麼時候用 | 提示詞怎麼寫 | 背景 |
|---|---|---|---|
| **角色情境圖**（最常用） | 講痛點、講比喻時 | 讓**阿遠親自演出比喻**：「阿遠抓著頭盔、困惑地看著一長串每格都一樣的蘋果清單」 | 暖白底 |
| **場景圖** | 比喻需要一個「地方」（辦公室、廚房、街頭、教室…） | 阿遠在完整的小模型場景裡做事，像素材裡的雲梯車圖 | 完整場景 |
| **圖表示意** | 講對比、流程、比例時 | 阿遠指著／搬著示意物件；⚠️ **只畫示意，不要讓模型寫字**：「阿遠站在一高一矮兩疊積木旁」而不是「長條圖含標籤」 | 暖白底 |
| **主題物件圖** | 抽象概念需要一個象徵物、畫面放不下人時 | 物件本身用同樣的 3D 公仔質感（Token→積木、記憶→便利貼）；可以的話讓阿遠在旁邊探頭 | 暖白底 |

## 風格模板（固定不要改，這是視覺一致的關鍵）
prompt 一律英文，結構＝**角色開頭句 → 主體描述（動作、道具、表情）→ 固定結尾**。

角色開頭句（有阿遠的圖都要放最前面）：
```
The chibi firefighter character from the attached reference sheet (pale lime-green helmet with brown crest,
yellow turnout coat with lime reflective stripes, grey half face mask, black gloves and boots)
```
固定結尾 A（暖白底：角色情境圖／圖表示意／主題物件圖）：
```
Keep the character design exactly identical to the reference. Same 3D chibi vinyl figure render style as the
reference: matte soft surface with subtle sheen, rounded chunky shapes, soft studio lighting,
warm off-white cream background, centered composition, no text, no letters, no words
```
固定結尾 B（場景圖）：
```
Keep the character design exactly identical to the reference. Same 3D chibi vinyl figure render style as the
reference: matte soft surface with subtle sheen, rounded chunky shapes, warm soft lighting,
full detailed miniature diorama background, no text, no letters, no words
```

- **`warm off-white cream background` 不能拿掉**（A 款）：純白底貼進紙色字卡會像突兀的白方塊，暖白才融得進去（實測過）。
- **`no text, no letters, no words` 不能拿掉**：模型寫中文字幾乎必錯，所有文字一律交給 `make_slide` 疊上去。
- **`Keep the character design exactly identical to the reference` 不能拿掉**：少了它阿遠會被「改造」（換頭盔色、拿掉口罩）。
- 主體描述盡量具體（動作、道具、表情），表情可參考設定表的六種：neutral / joy / sadness / anger / surprise / fear。
- 2026-10-24 實測：帶 `sheet.jpg` 一張約 65~70 秒，角色一致度很高（頭盔、口罩、反光條、氣瓶都對）。

## 怎麼呼叫
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\高知淵\.claude\skills\draw-gpt\draw-gpt.ps1" `
  -Prompt "<英文 prompt>" -Name seg2 -OutDir "output\<日期>\illust" -Aspect square -Ref "_style\sheet.jpg"
```
- **`-Ref "_style\sheet.jpg"` 每張都要帶**。⚠️ 用 `powershell -File` 呼叫時 **`-Ref` 只能給一張**（給兩張會被黏成一個路徑而 FAIL），只帶 `sheet.jpg` 就夠。
- `_style\sheet.jpg` 不見時（換電腦），從上面的正本資料夾複製「阿遠老師角色圖.jpg」過來改名；真的找不到就照舊不帶 `-Ref`，不要因此擋發片。
- **`-Aspect square`**：字卡的插圖框接近方形，square 最合身。
- **`-Name`** 用 `seg2`／`seg3`… 對應段號，方便對照。
- 中文 prompt 要先寫成 UTF-8 檔再傳路徑；**英文可直接傳字串**（建議都用英文，比較準）。
- 回傳 `OK path=... size=...` 就是成功，把那個路徑接到 make_slide。

## 配角（人物資產包，2026-11-09 金主提供）
金主為了人物多樣性做了一批同畫風的配角。**主角永遠是阿遠，出場比例最高**；配角只在劇情需要「第二個人」時才請出來。
正本：`C:\Users\高知淵\Documents\Codex\2026-10-24(各人物)\referenced-chatgpt-conversation-this-is-an\outputs\`
工作區副本：`_style\cast\`（四面轉面圖，英文檔名）。

### 使用規則（硬性）
1. **每支片有配角的插圖不超過一半**（4 張最多 2 張、2~3 張最多 1 張）；其餘照舊只有阿遠。**標題卡、收尾卡、縮圖一律只用阿遠**。
2. **有配角的圖，阿遠一定也在畫面裡，而且是主角**：站前面、比較大、焦點在他身上，配角在旁邊或後方。
3. **一張圖最多 1 位配角**（搜救隊員＋搜救犬算一組）。
4. 依劇情挑人，**沒有適合的情境就不要硬塞**。只用下表的角色；資產包裡的「紅色消防員_造型提案」「女性紅色制服消防員_造型提案」是舊版草稿（已被紅色制服男女定稿取代），**不要用**。

### 角色表
| 參考圖（`-Ref`） | 角色 | 適合的情境 | prompt 裡的配角描述（照抄） |
|---|---|---|---|
| `_style\cast\pair_red_m.jpg` | 男性紅色制服消防員（未戴帽） | 同事、對話、一起看電腦、被阿遠解說的人、辦公室日常 | the chibi male firefighter with short black hair, red short-sleeve uniform shirt with chest pockets, dark navy trousers, black belt with silver buckle, black shoes |
| `_style\cast\pair_red_m_cap.jpg` | 男性紅色制服消防員（戴帽） | 正式場合、長官、指揮、宣導、檢查 | same as above plus a dark grey service cap with gold emblem |
| `_style\cast\pair_red_f.jpg` | 女性紅色制服消防員（未戴帽） | 同事、對話、提問的人、一起學習 | the chibi female firefighter with short black bob hair, red short-sleeve uniform shirt, dark navy trousers, black shoes |
| `_style\cast\pair_red_f_cap.jpg` | 女性紅色制服消防員（戴帽） | 正式場合、講師、宣導、評審 | same as above plus a dark grey service cap with gold emblem |
| `_style\cast\pair_emt.jpg` | 男性 EMT 緊急救護技術員（2026-11-09 定稿，有四面轉面圖） | 醫療、健康、急救、AI 看病／AI 醫療建議、「找真正的專業人員」 | the chibi male EMT with short black hair, red short-sleeve duty shirt under a fluorescent yellow medical response vest with red-and-silver checker reflective bands, dark navy trousers, black shoes |
| `_style\cast\pair_white_m.jpg` | 白色制服消防員・男（2026-11-09 定稿，有四面轉面圖） | 正式場合、典禮、頒獎、主管、評審、行政文書 | the chibi male firefighter with short black hair, white short-sleeve collared uniform shirt with two chest pockets and a small red chest badge, dark navy trousers, black belt with silver buckle, black leather shoes |
| `_style\cast\pair_lifeguard.jpg` | 救生隊員 | 水、游泳、救溺、「被救起來」的比喻 | the chibi lifeguard rescuer with a yellow rescue helmet, blue uniform, red life vest with two black straps, black gloves and boots |
| `_style\cast\pair_rescue_team.jpg` | 搜救隊員＋搜救犬 | 搜尋、找東西、檢索（RAG、搜尋引擎）、聞線索 | the chibi search-and-rescue handler with a yellow rescue helmet with clear visor, yellow rescue suit with red chest panel and silver reflective bands, together with a slim tan German-shepherd-type search dog with black muzzle wearing an orange rescue harness and blue booties |
| `_style\cast\pair_rescue_dog.jpg` | 搜救犬（單獨） | 只需要狗的畫面（嗅聞、找到東西、忠實夥伴） | a slim tan German-shepherd-type search dog with black muzzle, orange rescue harness, blue booties |

### 有配角時的 prompt 結構
```
Two characters from the attached reference image. MAIN CHARACTER (left sheet): the chibi firefighter with pale
lime-green helmet with brown crest, yellow turnout coat with lime reflective stripes, grey half face mask, black
gloves and boots - he is in front, larger and in focus, <阿遠在做什麼>. SUPPORTING CHARACTER (right sheet):
<上表的配角描述> - <配角在旁邊做什麼>. Keep both character designs exactly identical to their reference sheets.
<固定結尾 A 或 B 從 "Same 3D chibi vinyl figure render style" 開始>
```
- `-Ref` 改傳上表的 pair 檔（阿遠設定表＋配角轉面圖已拼成一張，因為 `-Ref` 只能一張）。
- 所有配角都有四面轉面圖（搜救犬為定裝＋三面），任何角度都可以畫。
- 2026-11-09 實測：阿遠＋女性紅色制服、阿遠＋EMT，兩組造型都準（範例：`_style\cast\_example_pair_red_f.png`），一張約 50 秒。
- 生圖失敗的處理規則同下面的🛑段（配角圖 FAIL 也算進連續 FAIL）。

## 接進字卡
`make_slide.py` 第 **5** 個參數就是插圖（第 4 個是吉祥物，兩者擇一）：
```powershell
# 有插圖（第4參數放 "-" 代表不要吉祥物）
python pipeline\make_slide.py "標題" "重點一｜重點二" output\<日期>\slides\002.png "-" output\<日期>\illust\seg2_xxx.png

# 標題卡／收尾卡照舊用吉祥物
python pipeline\make_slide.py "標題" "內文" output\<日期>\slides\001.png "auto:<主題關鍵字>"
```
有插圖時版型會自動切成「標題 → 插圖 → 精簡內文」，**內文請縮到 1~2 個短重點**，否則會被擠掉。

**鏡頭微動是自動的，不用做任何事**（2026-10-24 起）：`make_slide` 會在字卡旁寫 `<編號>.illust.json`（插圖位置），
`make_video` 看到就讓**字卡文字靜止、只有框內插圖整段慢慢動**（推近／拉遠／左右平移輪流）。
不要刪這些 .json、不要另外對插圖做動畫。幅度可用環境變數 `AYUAN_ILLUST_MOTION` 調（預設 0.12）。

## 🛑 叫不動生圖時：直接放棄插圖，走原本流程（金主訂的規則）
**插圖是加分項，不是必要條件。發片永遠優先於插圖。**

判斷與處置：
1. **單張 `FAIL`** → 那一段改用純文字字卡，其他段照常繼續。
2. **連續 2 張 `FAIL`** → 判定為「**額度用光或服務不可用**」（月費生圖有用量上限，可能這週已用完）。
   → **本支片完全放棄插圖，整支回到原本的純文字字卡流程**（標題卡／收尾卡照舊用吉祥物）。
   → **不要再試第 3 張、不要重試、不要等待**——每張要等 40~60 秒，硬試只是白白拖長產線、可能拖到發片失敗。
3. 放棄後在 `MEMORY.md`「下次改進方向」記一行：`YYYY-MM-DD 生圖叫不動（疑似額度用完），本日走純文字字卡`，
   讓金主知道、也讓自己隔天不必重新診斷。

> 常見 `FAIL` 原因：額度用完、`codex` 登入掉了（log 有 auth 字樣）、內容被安全政策擋、逾時。
> 除了「內容被擋」（改寫 prompt 可救）之外，其餘都不該當場排除——**當天先把片發出去，問題留給金主處理**。

## ⚠️ 時間成本要算進去
**帶參考圖一張約 65~70 秒，4 張約 5 分鐘。** 加上原本的配音與合成，整輪大約 13~14 分鐘（心跳逾時上限 1500 秒仍夠）。
- 遵守 SKILL 的鐵則：**生圖指令也要前景跑完**，不要丟背景。
- 但「前景跑完」不等於「無限重試」——踩到上面第 2 條就果斷收手。

## 用量
記在 ChatGPT 月費訂閱額度，不扣 API 儲值。短時間連續猛生仍可能被限流——**每天 4 張是安全範圍**，不要為了單支片一次生十幾張。
