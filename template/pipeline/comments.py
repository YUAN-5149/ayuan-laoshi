"""觀眾留言：列出還沒回的留言、以頻道身分回覆，回覆紀錄寫進 COMMENTS.md。

金主 2026-11-17/18 訂：觀眾留言要**主動、懇切地回應，並虛心學習**。回覆準則在工作區 COMMENTS.md。

用法：
  python pipeline\\comments.py list [天數=30]
      列出最近 N 天、頻道還沒回過的觀眾留言（略過頻道自己的留言）。印出 thread id、影片標題、留言原文。
  python pipeline\\comments.py reply <threadId> <回覆文字檔.txt>
      以頻道身分回覆該留言（文字檔 UTF-8），並在 COMMENTS.md 的「回覆紀錄」補一行。
      同一則已回過會拒絕，避免重複回。

用的是 token_manage.json（youtube.force-ssl，與播放清單共用）。
"""
import datetime as dt
import io
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOKEN = os.path.join(HERE, "token_manage.json")
LOG = os.path.join(ROOT, "COMMENTS.md")


def client():
    c = Credentials.from_authorized_user_file(TOKEN)
    if not c.valid:
        c.refresh(Request())
        with open(TOKEN, "w", encoding="utf-8") as f:
            f.write(c.to_json())
    return build("youtube", "v3", credentials=c)


def channel_id(yt):
    return yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]


def threads(yt, ch, days):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    out, token = [], None
    while True:
        r = yt.commentThreads().list(part="snippet,replies", allThreadsRelatedToChannelId=ch,
                                     maxResults=100, order="time", pageToken=token,
                                     textFormat="plainText").execute()
        for it in r["items"]:
            top = it["snippet"]["topLevelComment"]["snippet"]
            when = dt.datetime.fromisoformat(top["publishedAt"].replace("Z", "+00:00"))
            if when < since:
                return out
            out.append(it)
        token = r.get("nextPageToken")
        if not token:
            return out


def owner_replied(yt, it, ch):
    n = it["snippet"]["totalReplyCount"]
    if n == 0:
        return False
    reps = it.get("replies", {}).get("comments", [])
    if len(reps) < n:  # 內嵌的回覆不完整時再查全部
        reps = yt.comments().list(part="snippet", parentId=it["id"], maxResults=100).execute()["items"]
    return any(x["snippet"].get("authorChannelId", {}).get("value") == ch for x in reps)


def cmd_list(days):
    yt = client()
    ch = channel_id(yt)
    pending = []
    for it in threads(yt, ch, days):
        top = it["snippet"]["topLevelComment"]["snippet"]
        if top.get("authorChannelId", {}).get("value") == ch:
            continue  # 頻道自己發的
        if owner_replied(yt, it, ch):
            continue
        pending.append(it)
    if not pending:
        print("NONE：最近 %d 天沒有待回的留言。" % days)
        return
    titles = {}
    vids = list({it["snippet"].get("videoId") for it in pending if it["snippet"].get("videoId")})
    for i in range(0, len(vids), 50):
        for v in yt.videos().list(part="snippet", id=",".join(vids[i:i + 50])).execute()["items"]:
            titles[v["id"]] = v["snippet"]["title"]
    print("待回留言 %d 則：" % len(pending))
    for it in reversed(pending):  # 舊的先
        top = it["snippet"]["topLevelComment"]["snippet"]
        vid = it["snippet"].get("videoId", "")
        print("=" * 60)
        print("thread:", it["id"])
        print("影片:", vid, titles.get(vid, ""))
        print("時間:", top["publishedAt"][:16], "｜讚", top.get("likeCount", 0))
        print("留言者:", top["authorDisplayName"])
        print("內容:", top["textDisplay"])
        for x in it.get("replies", {}).get("comments", []):
            print("   ↳", x["snippet"]["authorDisplayName"], ":", x["snippet"]["textDisplay"])


def cmd_reply(thread_id, text_file):
    with io.open(text_file, encoding="utf-8-sig") as f:
        text = f.read().strip()
    if not text:
        sys.exit("回覆文字是空的")
    yt = client()
    ch = channel_id(yt)
    it = yt.commentThreads().list(part="snippet,replies", id=thread_id).execute()["items"]
    if not it:
        sys.exit("找不到這則留言：" + thread_id)
    it = it[0]
    if owner_replied(yt, it, ch):
        sys.exit("SKIP：這則已經回過了，不重複回。")
    yt.comments().insert(part="snippet", body={"snippet": {"parentId": thread_id, "textOriginal": text}}).execute()
    top = it["snippet"]["topLevelComment"]["snippet"]
    line = "- %s ｜%s｜影片 %s｜「%s」→ 回：「%s」\n" % (
        dt.date.today().isoformat(), top["authorDisplayName"], it["snippet"].get("videoId", ""),
        top["textDisplay"].replace("\n", " ")[:120], text.replace("\n", " ")[:200])
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print("OK：已回覆", thread_id)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) >= 2 and sys.argv[1] == "list":
        cmd_list(int(sys.argv[2]) if len(sys.argv) > 2 else 30)
    elif len(sys.argv) == 4 and sys.argv[1] == "reply":
        cmd_reply(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
