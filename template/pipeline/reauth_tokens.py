"""一次重授權管理與 Analytics 兩顆 token（Production 下發的、不再 7 天過期）。

token_manage.json    scope=youtube.force-ssl     （播放清單/改隱私/標題）
token_analytics.json scope=yt-analytics.readonly （週復盤拉觀看/留存數據）

用法：python reauth_tokens.py   （瀏覽器會依序跳兩次授權，請都登入 bbbb086110）
成功才覆寫對應檔案；失敗/取消不動原檔。
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

HERE = os.path.dirname(os.path.abspath(__file__))
SECRET = os.path.join(HERE, "client_secret.json")

TARGETS = [
    ("token_manage.json", ["https://www.googleapis.com/auth/youtube.force-ssl"]),
    ("token_analytics.json", ["https://www.googleapis.com/auth/yt-analytics.readonly"]),
]

for fname, scopes in TARGETS:
    print(f"--- 授權 {fname}（{scopes[0].rsplit('/', 1)[-1]}）---")
    flow = InstalledAppFlow.from_client_secrets_file(SECRET, scopes)
    creds = flow.run_local_server(port=0)
    with open(os.path.join(HERE, fname), "w") as f:
        f.write(creds.to_json())
    print(f"OK: {fname} 已更新")

print("完成：兩顆 token 都已在 Production 下重發。")
