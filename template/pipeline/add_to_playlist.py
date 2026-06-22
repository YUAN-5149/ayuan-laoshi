"""把影片加進系列播放清單（拉長 session 觀看、建立追看習慣）。

找不到同名清單會自動建立。預設清單名「AI 名詞白話系列」，可用環境變數 AYUAN_PLAYLIST 覆蓋。

⚠️ 需要額外授權：第一次執行會開瀏覽器要求 `youtube`（管理播放清單），token 存 token_manage.json
（與上傳/分析的 token 分開）。人在電腦前完成一次即可，之後全自動。

用法:
    python add_to_playlist.py <videoId> ["播放清單標題"]
"""
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, "token_manage.json")
SECRET = os.path.join(HERE, "client_secret.json")
DEFAULT_TITLE = os.environ.get("AYUAN_PLAYLIST", "AI 名詞白話系列")


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


def find_or_create_playlist(yt, title):
    req = yt.playlists().list(part="snippet", mine=True, maxResults=50)
    while req is not None:
        resp = req.execute()
        for it in resp.get("items", []):
            if it["snippet"]["title"] == title:
                return it["id"]
        req = yt.playlists().list_next(req, resp)
    # 沒有就建立
    resp = yt.playlists().insert(part="snippet,status", body={
        "snippet": {"title": title,
                    "description": "阿遠老師用最白話的方式講懂 AI 名詞。本頻道由 AI Agent 自主經營。"},
        "status": {"privacyStatus": "public"},
    }).execute()
    print(f"建立新播放清單：{title}")
    return resp["id"]


def main():
    video_id = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TITLE
    yt = build("youtube", "v3", credentials=get_credentials())
    pid = find_or_create_playlist(yt, title)
    yt.playlistItems().insert(part="snippet", body={
        "snippet": {"playlistId": pid,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id}},
    }).execute()
    print(f"OK: {video_id} 已加入播放清單「{title}」")


if __name__ == "__main__":
    main()
