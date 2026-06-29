"""一次性：OAuth App 發布成 Production 後重新授權，取得不會每 7 天過期的 token.json。

為什麼需要：在「測試 Testing」狀態下發出的 refresh token，即使之後把 App 改成 Production，
那一張仍會 7 天後過期。必須在改成 Production「之後」重新授權，才會拿到不過期的新 token。

行為：直接跑互動授權流程（會開瀏覽器，請登入 bbbb086110），成功才覆寫 token.json；
失敗/取消則不動到既有 token.json。用法：python reauth_upload.py
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, "token.json")
SECRET = os.path.join(HERE, "client_secret.json")

flow = InstalledAppFlow.from_client_secrets_file(SECRET, SCOPES)
creds = flow.run_local_server(port=0)
with open(TOKEN, "w") as f:
    f.write(creds.to_json())
print("OK: token.json 已在 Production 狀態下重新授權寫入（不再每 7 天過期）。")
