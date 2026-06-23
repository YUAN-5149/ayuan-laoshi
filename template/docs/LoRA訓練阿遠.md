# 免費訓練「阿遠」LoRA（Google Colab T4）

目標：用既有阿遠素材訓一個角色 LoRA，之後能無限免費生成「長一樣的阿遠」做各種新姿勢。
全程免費（Colab 免費版 T4 16GB 即可訓 SDXL LoRA）。

---

## 0. 前置（已由 Claude 完成）

- **資料集**：6 張阿遠去背鋪白底、裁 1024×1024，每張配好英文 caption。
- **觸發詞**：`ayuanff`（生圖 prompt 打這個詞就會召喚阿遠）。
- **位置**：已放你的 Google Drive →「阿遠老師本人」資料夾：
  - `ayuanff_lora_dataset.zip`（壓縮版）
  - `ayuanff_lora_dataset/`（解開版，12 個檔）
- 重新產生資料集：`python pipeline\prep_lora_dataset.py`（改 caption 或加圖後重跑）。

> ⚠️ 只有 6 張偏少，品質會有上限。之後在 `_ref\` 多放幾張**單人、不同角度**的阿遠再重訓會更穩。
> 第 04 張是「雙人射水」，訓練後生圖偶爾可能跑出兩個人 → 生成時 negative prompt 加 `two people, 2 characters`。

---

## 1. 開 Colab + 免費 GPU

1. 到 https://colab.research.google.com
2. 「執行階段」→「變更執行階段類型」→ 選 **T4 GPU** → 儲存。

## 2. 用現成的 SDXL LoRA 訓練 Colab

推薦 **Hollowstrawberry 的 XL LoRA trainer**（新手友善、用 Drive 流程）：
- GitHub：`github.com/hollowstrawberry/kohya-colab` → 開 **Lora_Trainer_XL.ipynb** 的 Colab。
- （備案：搜尋「kohya SDXL lora colab」找維護中的 notebook；介面會變，以實際畫面為準。）

在 notebook 裡：
1. **掛載 Google Drive**（執行第一格會跳授權，用 bbbb086110 帳號）。
2. **project_name** 填 `ayuanff`。
3. **dataset 來源**指向 Drive 的 `阿遠老師本人/ayuanff_lora_dataset`（解開版資料夾）。
   - 若 notebook 要求自己放：把資料夾放到它指定的 `…/Loras/ayuanff/dataset/`。

## 3. 關鍵設定（角色 LoRA）

| 項目 | 建議值 | 說明 |
|---|---|---|
| Base model | SDXL 1.0 base | 通用相容性最好 |
| resolution | 1024 | 配合素材 |
| trigger / activation tag | `ayuanff` | caption 已含，不必重設 |
| num_repeats | 15~20 | 圖少要多重複 |
| epochs | 10 | 約 900~1200 步 |
| network_dim / alpha | 16 / 8 | 角色夠用、檔案小 |
| unet_lr | 1e-4 | 文字編碼器設更低或關 |
| 輸出 | `ayuanff.safetensors` | 訓完存到 Drive |

> 總步數抓 ~1000~1500 步即可；步數太多會「過擬合」(每張都像背景白底、姿勢僵)。

## 4. 訓練（免費 T4 約 30~60 分鐘）

跑訓練格，等它把 `ayuanff.safetensors` 存到 Drive。中途斷線就重連、重跑（Colab 免費版有時間限制）。

## 5. 生成新姿勢（也在 Colab，免費）

同個 notebook（或任何「SDXL + LoRA 生圖」notebook）載入 `ayuanff.safetensors`，prompt 例：

```
ayuanff, 3d chibi firefighter mascot, holding a microphone and waving, happy, plain white background
ayuanff, 3d chibi firefighter mascot, thinking pose hand on chin, plain white background
ayuanff, 3d chibi firefighter mascot, giving a thumbs up, big smile, plain white background
```
- negative：`two people, 2 characters, extra limbs, blurry, low quality`
- 一次生 4~8 張挑最好的，下載 PNG。

## 6. 帶回 pipeline

1. 下載的 PNG 放進 `D:\ayuan-laoshi-agent\_ref\`，命名成 `黃色-<姿勢>.png`。
2. 到 `pipeline\mascot.py` 的 RULES 加對應關鍵字→檔名（或叫 Claude 幫加）。
3. 之後製片時 `auto:<關鍵字>` 就會自動挑到新姿勢。

> 備份：把 `ayuanff.safetensors` 存一份到 Drive「阿遠老師本人」，換電腦不必重訓。

---

## 為什麼不在本機生圖？

本機是 GTX 1050 4GB + 8GB RAM，跑不動 SDXL（要 8GB+ 顯存）。所以**訓練與生成都在 Colab 免費 T4 上做**，產出的 PNG 再下載回本機 `_ref\` 即可。屬於 [[ayuan-laoshi-mascot-assets]] 的延伸。
