"""拉 YouTube Analytics 數據，寫成 ANALYTICS.md 供阿遠選題時參考（資料驅動）。

從 MEMORY.md 的已發布清單解析影片 ID，查每支的生涯數據：
觀看數、平均觀看百分比（留存）、平均觀看秒數、帶來的訂閱數。

⚠️ 需要額外授權：第一次執行會開瀏覽器要求 `yt-analytics.readonly`（與上傳用的 token 分開存）。
人在電腦前完成一次即可，之後全自動。CTR（曝光點閱率）API 不開放，請到 YouTube Studio 看。

用法:
    python fetch_analytics.py            # 寫到 ../ANALYTICS.md
    python fetch_analytics.py out.md
"""
import datetime as dt
import os
import re
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOKEN = os.path.join(HERE, "token_analytics.json")   # 與 upload 的 token.json 分開
SECRET = os.path.join(HERE, "client_secret.json")
MEMORY = os.path.join(ROOT, "MEMORY.md")


def get_credentials():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
    return creds


def video_ids_from_memory():
    """從 MEMORY.md 解析 youtu.be/<id> 與 watch?v=<id>，保序去重。"""
    if not os.path.exists(MEMORY):
        return []
    text = open(MEMORY, encoding="utf-8").read()
    ids = re.findall(r"(?:youtu\.be/|watch\?v=)([\w-]{11})", text)
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i); out.append(i)
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "ANALYTICS.md")
    ids = video_ids_from_memory()
    if not ids:
        sys.exit("MEMORY.md 找不到任何影片 ID，先發幾支再來。")

    ya = build("youtubeAnalytics", "v2", credentials=get_credentials())
    today = dt.date.today().isoformat()
    resp = ya.reports().query(
        ids="channel==MINE",
        startDate="2005-01-01", endDate=today,
        dimensions="video",
        metrics="views,averageViewPercentage,averageViewDuration,subscribersGained",
        filters="video==" + ",".join(ids),
        sort="-views", maxResults=200,
    ).execute()

    rows = resp.get("rows", [])
    # 對回標題（從 MEMORY 抓「《標題》」與 id 的鄰近關係較麻煩，這裡簡單以 id 連結呈現）
    lines = [f"# ANALYTICS.md — 頻道數據（自動產生 @ {today}）", "",
             "> 選題/標題前先看這份。CTR 請到 YouTube Studio 看（API 不開放）。", "",
             "| 觀看 | 留存% | 平均秒 | 帶來訂閱 | 影片 |",
             "|---:|---:|---:|---:|---|"]
    for r in rows:
        vid, views, retpct, avgdur, subs = r[0], r[1], r[2], r[3], r[4]
        lines.append(f"| {int(views)} | {retpct:.0f}% | {avgdur:.0f}s | {int(subs)} | "
                     f"https://youtu.be/{vid} |")

    # 一句洞察：留存最高的那支
    if rows:
        best = max(rows, key=lambda r: r[1])   # 依 averageViewPercentage
        lines += ["", f"**留存最高**：{best[1]:.0f}%（https://youtu.be/{best[0]} ）"
                  "——這支的選題/比喻/節奏值得複製。"]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"OK: {out_path} ｜ {len(rows)} 支影片數據")


if __name__ == "__main__":
    main()
