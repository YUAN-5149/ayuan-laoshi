# ILLUST.md — 每日插圖指南（Q 版矽膠風）

> 2026-08-27 起：金主訂了 ChatGPT 月費並開通生圖，**每支片可以生 4 張插圖**（不花 API 錢，走月費額度）。
> 插圖讓字卡從「純文字」升級成「有畫面」，是目前最能拉高質感的一步。

## 什麼時候用
每天做字卡前先生圖。**4 張的建議分配**（以 5 段 Shorts 為例）：
- 第 1 段（標題卡）→ 用**吉祥物阿遠**（維持品牌識別，不用插圖）
- 第 2~5 段 → **各配一張插圖**，正好 4 張
- 收尾段若要催訂閱，也可改回吉祥物、把該張插圖挪到別段

長片（週日 6~9 段）：一樣生 4 張，挑**最需要畫面輔助的 4 段**用，其餘維持文字卡。

## 三種用途
| 類型 | 什麼時候用 | 提示詞怎麼寫 |
|---|---|---|
| **情境圖** | 講痛點、講比喻時（最常用） | 把比喻直接畫出來：「一個背下所有安慰話術卻沒哭過的機器人」 |
| **圖表示意** | 講對比、流程、比例時 | ⚠️ **只畫示意，不要讓模型寫字**：畫「兩個大小差很多的堆疊方塊」而不是「長條圖含標籤」 |
| **主題圖** | 抽象概念需要一個象徵物 | 例：Token→積木、記憶→便利貼、護欄→橡皮牆 |

## 風格模板（固定不要改，這是視覺一致的關鍵）
主體描述用英文寫在最前面，後面**固定接這段**：

```
cute chibi 3D illustration in soft silicone vinyl toy style, matte surface with subtle sheen,
rounded chunky shapes, warm pastel color palette, soft studio lighting,
warm off-white cream background, centered composition, no text, no letters, no words
```

- **`warm off-white cream background` 不能拿掉**：純白底貼進紙色字卡會像突兀的白方塊，暖白才融得進去（實測過）。
- **`no text, no letters, no words` 不能拿掉**：模型寫中文字幾乎必錯，所有文字一律交給 `make_slide` 疊上去。
- 主體描述盡量具體（角色、動作、道具、情緒），不要只寫抽象名詞。

## 怎麼呼叫
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\高知淵\.claude\skills\draw-gpt\draw-gpt.ps1" `
  -Prompt "<英文 prompt>" -Name seg2 -OutDir "output\<日期>\illust" -Aspect square
```
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

## ⚠️ 時間成本要算進去
**一張約 40~60 秒，4 張約 3~4 分鐘。** 加上原本的配音與合成，整輪大約 12 分鐘（心跳逾時上限 1500 秒仍夠）。
- 遵守 SKILL 的鐵則：**生圖指令也要前景跑完**，不要丟背景。
- 生圖失敗（`FAIL`）不要卡住整條產線：**那一段改用純文字字卡照常出片**，別為了插圖犧牲當天更新。

## 用量
記在 ChatGPT 月費訂閱額度，不扣 API 儲值。短時間連續猛生仍可能被限流——**每天 4 張是安全範圍**，不要為了單支片一次生十幾張。
