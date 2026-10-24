# ILLUST.md — 每日插圖指南（消防員阿遠 3D 公仔風）

> 2026-09-06 起：金主訂了 ChatGPT 月費並開通生圖，**每支片可以生 4 張插圖**（不花 API 錢，走月費額度）。
> 插圖讓字卡從「純文字」升級成「有畫面」，是目前最能拉高質感的一步。
> **2026-10-24 起（金主訂）：插圖一律以「消防員阿遠」素材為主要範本**——每次生圖都要帶參考圖 `_style\sheet.jpg`，
> 讓阿遠親自演出比喻，整個頻道的畫面長同一個樣。不再生沒有阿遠的泛用 Q 版公仔。

## 什麼時候用
每天做字卡前先生圖。**4 張的建議分配**（以 5 段 Shorts 為例）：
- 第 1 段（標題卡）→ 用**吉祥物阿遠**（維持品牌識別，不用插圖）
- 第 2~5 段 → **各配一張插圖**，正好 4 張
- 收尾段若要催訂閱，也可改回吉祥物、把該張插圖挪到別段

長片（週日 6~9 段）：一樣生 4 張，挑**最需要畫面輔助的 4 段**用，其餘維持文字卡。

## 範本素材（阿遠長什麼樣）
- 正本來源：金主桌面 `C:\Users\高知淵\Desktop\阿遠老師\阿遠老師素材(正黃色)\`（設定表、各種姿勢、場景圖、工具圖）。
- 生圖用的參考圖已複製到工作區 **`_style\`**（英文檔名，排程傳路徑才不會出錯）：
  - **`sheet.jpg`** ＝ 角色設定表 CHIBA-01（三視圖＋表情＋動作）——**每次生圖都帶這張**
  - `scene_truck.png`（雲梯車場景）、`pose_light.png`（搬照明燈）、`pose_welcome.png`（張手歡迎）＝風格對照用
- 阿遠外型（寫 prompt 時照抄，別自己改）：淺綠頭盔＋咖啡色盔飾、黃色消防衣＋螢光綠反光條、灰色半罩口罩、
  黑手套黑靴、背後灰色空氣瓶；3D 軟膠公仔質感，大頭 Q 版比例。

## 四種用途（4 張裡**至少 3 張要有阿遠**）
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

## 接進字卡
`make_slide.py` 第 **5** 個參數就是插圖（第 4 個是吉祥物，兩者擇一）：
```powershell
# 有插圖（第4參數放 "-" 代表不要吉祥物）
python pipeline\make_slide.py "標題" "重點一｜重點二" output\<日期>\slides\002.png "-" output\<日期>\illust\seg2_xxx.png

# 標題卡／收尾卡照舊用吉祥物
python pipeline\make_slide.py "標題" "內文" output\<日期>\slides\001.png "auto:<主題關鍵字>"
```
有插圖時版型會自動切成「標題 → 插圖 → 精簡內文」，**內文請縮到 1~2 個短重點**，否則會被擠掉。

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
