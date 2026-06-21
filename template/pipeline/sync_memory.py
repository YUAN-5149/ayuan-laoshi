"""從 YouTube 頻道 RSS 同步「已發布影片」回 MEMORY.md。

為什麼需要：換電腦後 MEMORY.md 會回到 template 的空白狀態，Agent 不記得
自己發過什麼，就會重複選題（2026-06-22 就因此重發過 AI Agent）。這支腳本
在每次心跳前先跑，把頻道上「已存在但本機記憶沒有」的影片補回 MEMORY.md，
讓 Agent 跨機也記得自己的創作史。

特性：
- 冪等：以 videoId 去重，重複跑不會重複寫入。
- 純標準函式庫（urllib + xml），不需額外安裝套件。
- 抓取失敗（沒網路等）只警告、exit 0，絕不擋住心跳。
- 自動分類：標題像 AI 主題的進「已發布影片清單」並加 PUBLISHED 標記；
  其餘（如金主本人的消防考試影片）進「非 AI 內容」區、不加標記，
  因此不會被 channel_day 算進 AI 系列天數。

用法:
    python pipeline/sync_memory.py            # 同步並寫入
    python pipeline/sync_memory.py --dry-run  # 只報告不寫入

頻道 ID 來源優先序：環境變數 YT_CHANNEL_ID > MEMORY.md 內的 `channel_id: UC...` 註記。
"""
import datetime
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY = os.path.join(ROOT, "MEMORY.md")

# 標題含這些關鍵字 → 視為 AI 系列影片（大小寫不敏感）
AI_KEYWORDS = [
    "ai", "a i", "llm", "rag", "token", "agent", "gpt", "模型", "人工智慧",
    "機器學習", "深度學習", "神經", "embedding", "transformer", "提示", "prompt",
    "幻覺", "向量", "微調", "fine-tun", "參數", "多模態", "演算法", "訓練資料",
    "語言模型", "生成式", "脈絡", "context", "溫度", "temperature",
]

PUB_HEADER = "## 已發布影片清單"
OTHER_HEADER = "## 同頻道的非 AI 內容（金主本人上傳，勿動、勿計入 AI 系列天數）"


def get_channel_id():
    cid = os.environ.get("YT_CHANNEL_ID")
    if cid:
        return cid.strip()
    if os.path.exists(MEMORY):
        with open(MEMORY, encoding="utf-8") as f:
            m = re.search(r"channel_id:\s*(UC[\w-]+)", f.read())
            if m:
                return m.group(1)
    return None


def fetch_feed(cid):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    ns = {"a": "http://www.w3.org/2005/Atom",
          "yt": "http://www.youtube.com/xml/schemas/2015"}
    root = ET.fromstring(data)
    out = []
    for e in root.findall("a:entry", ns):
        vid = e.find("yt:videoId", ns).text
        title = (e.find("a:title", ns).text or "").strip()
        raw = (e.find("a:published", ns).text or "")  # ISO，含 UTC 時區
        try:
            # 轉成本機當地日期，避免深夜跨日時 UTC 日期差一天造成 dedup 失準
            date = datetime.datetime.fromisoformat(raw).astimezone().date().isoformat()
        except ValueError:
            date = raw[:10]
        out.append((vid, title, date))
    return out


def is_ai(title):
    t = title.lower()
    return any(k in t for k in AI_KEYWORDS)


def insert_into_section(lines, header, new_lines):
    """把 new_lines 插到指定 ## 區段最後一筆 '- ' 之後。找不到區段就回傳 None。"""
    try:
        h = next(i for i, ln in enumerate(lines) if ln.strip() == header.strip())
    except StopIteration:
        return None
    # 區段結束 = 下一個 '## ' 標題，或檔尾
    e = len(lines)
    for i in range(h + 1, len(lines)):
        if lines[i].startswith("## "):
            e = i
            break
    # 插入點 = 區段內最後一筆 '- ' 之後；沒有就接在標題下一行
    insert_at = h + 1
    for i in range(h + 1, e):
        if lines[i].startswith("- "):
            insert_at = i + 1
    return lines[:insert_at] + new_lines + lines[insert_at:]


def ensure_other_section(lines, new_lines):
    """非 AI 區段不存在就在檔尾建立。"""
    block = ["", OTHER_HEADER] + new_lines
    if lines and lines[-1].strip() != "":
        block = [""] + block
    return lines + block


def main():
    dry = "--dry-run" in sys.argv
    cid = get_channel_id()
    if not cid:
        print("ERROR: 找不到頻道 ID（請設環境變數 YT_CHANNEL_ID，或在 MEMORY.md 寫 `channel_id: UC...`）")
        sys.exit(1)

    try:
        entries = fetch_feed(cid)
    except Exception as ex:  # 網路問題等：絕不擋心跳
        print(f"WARN: 抓取頻道 RSS 失敗，跳過同步：{ex}")
        sys.exit(0)

    with open(MEMORY, encoding="utf-8") as f:
        mem = f.read()
    known = set(re.findall(r"youtu\.be/([\w-]+)", mem))

    new_ai, new_other = [], []
    for vid, title, date in sorted(entries, key=lambda x: x[2]):  # 由舊到新
        if vid in known:
            continue
        if is_ai(title):
            new_ai.append(
                f"- {date} 《{title}》 https://youtu.be/{vid} <!-- PUBLISHED:{date} -->（RSS 同步補入）")
        else:
            slash = date.replace("-", "/")
            new_other.append(f"- {title}（{slash}） https://youtu.be/{vid}")

    if not new_ai and not new_other:
        print("MEMORY.md 已是最新，無新增影片。")
        return

    print(f"偵測到 {len(new_ai)} 支 AI 影片、{len(new_other)} 支非 AI 影片尚未記錄：")
    for ln in new_ai + new_other:
        print("  +", ln)
    if dry:
        print("(--dry-run，未寫入)")
        return

    lines = mem.split("\n")
    if new_ai:
        res = insert_into_section(lines, PUB_HEADER, new_ai)
        if res is None:
            print(f"ERROR: MEMORY.md 找不到「{PUB_HEADER}」區段，無法寫入 AI 影片")
            sys.exit(1)
        lines = res
    if new_other:
        res = insert_into_section(lines, OTHER_HEADER, new_other)
        lines = res if res is not None else ensure_other_section(lines, new_other)

    with open(MEMORY, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已補入 MEMORY.md（{datetime.date.today()}）。")


if __name__ == "__main__":
    main()
