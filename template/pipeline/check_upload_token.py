"""預檢 YouTube 上傳 token 是否可用（給心跳在產片前呼叫）。

為什麼需要：upload_youtube.py 在 token 過期且 refresh 失敗時，會 fallback 去開瀏覽器
互動授權（run_local_server）。無人值守的心跳開了瀏覽器沒人登入，會卡住/失敗，還可能
弄丟 token.json——結果是「產了一支片卻上傳失敗」，浪費整輪產線與 Claude 用量。
（2026-06-29 就因 token 7 天過期、refresh 失敗而失敗。根因：OAuth 同意畫面在 Testing 狀態
 → refresh token 每 7 天過期；治本要把 App 發布成 Production。）

行為：純檢查，不開瀏覽器、不互動。
  exit 0 = token 有效（或過期但成功 refresh，已寫回 token.json）→ 可以放心產片+上傳。
  exit 2 = token 不存在 / 無 refresh_token / refresh 失敗 → 需要人工重新授權，心跳應跳過產片並告警。
"""
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, "token.json")


def main():
    if not os.path.exists(TOKEN):
        print("NEED_REAUTH: token.json 不存在，需重新授權 YouTube 上傳。")
        sys.exit(2)
    try:
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    except Exception as e:
        print(f"NEED_REAUTH: token.json 讀取失敗（{e}），需重新授權。")
        sys.exit(2)

    if creds and creds.valid:
        print("OK: 上傳 token 有效。")
        sys.exit(0)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN, "w") as f:
                f.write(creds.to_json())
            print("OK: 上傳 token 已過期但成功 refresh 並寫回。")
            sys.exit(0)
        except Exception as e:
            print(f"NEED_REAUTH: refresh 失敗（{e}）。多半是 OAuth 同意畫面仍在 Testing 狀態、"
                  f"refresh token 每 7 天過期——治本請把 App 發布成 Production。")
            sys.exit(2)

    print("NEED_REAUTH: token 無效且無可用 refresh_token，需重新授權。")
    sys.exit(2)


if __name__ == "__main__":
    main()
