"""上傳影片到 YouTube（YouTube Data API v3）。

第一次執行會開瀏覽器要求授權，token 存在 token.json 之後全自動。

事前準備（一次性，需要人類完成）:
1. 到 https://console.cloud.google.com 建立專案
2. 啟用「YouTube Data API v3」
3. 建立 OAuth 2.0 用戶端 ID（桌面應用程式），下載 JSON 存成本目錄的 client_secret.json
4. OAuth 同意畫面把自己的 Google 帳號加入測試使用者

用法:
    python upload_youtube.py video.mp4 "影片標題" "影片描述" "tag1,tag2"
"""
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, "token.json")
SECRET = os.path.join(HERE, "client_secret.json")


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


def main():
    video, title, desc = sys.argv[1], sys.argv[2], sys.argv[3]
    tags = sys.argv[4].split(",") if len(sys.argv) > 4 else []
    thumbnail = sys.argv[5] if len(sys.argv) > 5 else ""

    yt = build("youtube", "v3", credentials=get_credentials())
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": tags,
            "categoryId": "28",  # Science & Technology
            "defaultLanguage": "zh-TW",
        },
        "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"),
                   "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video, chunksize=-1, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"upload {int(status.progress() * 100)}%")
    vid = resp["id"]

    # 設定自訂縮圖（需頻道已通過手機驗證；失敗不影響影片本身）
    if thumbnail and os.path.exists(thumbnail):
        try:
            yt.thumbnails().set(
                videoId=vid, media_body=MediaFileUpload(thumbnail)).execute()
            print("thumbnail set OK")
        except Exception as e:
            print(f"thumbnail set FAILED (頻道可能尚未驗證，可手動上傳): {e}")

    print(f"OK: https://youtu.be/{vid}")


if __name__ == "__main__":
    main()
