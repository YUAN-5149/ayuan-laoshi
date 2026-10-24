"""週六「GitHub 寶藏專案」選題工具：即時查星數、比對已介紹清單，確保 ≥1000 星且不重複。

用法:
    python github_repo.py search [關鍵字...]   # 列出 ≥1000 星、近一年有更新、還沒介紹過的候選
    python github_repo.py check owner/repo     # 定案前必跑：印專案資訊，最後一行 OK 或 DENY <原因>

已介紹清單讀工作區 GITHUB.md 裡所有 github.com/owner/repo 連結（大小寫不分）。
有環境變數 GITHUB_TOKEN 就帶上（未帶也能用，GitHub 匿名上限每小時 60 次，選題綽綽有餘）。
"""
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

MIN_STARS = int(os.environ.get("AYUAN_GITHUB_MIN_STARS", "1000"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_FILE = os.path.join(ROOT, "GITHUB.md")
API = "https://api.github.com"


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "ayuan-laoshi"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def introduced():
    """GITHUB.md 裡出現過的 owner/repo（小寫）。"""
    if not os.path.exists(LIST_FILE):
        return set()
    with open(LIST_FILE, encoding="utf-8") as f:
        text = f.read()
    return {m.lower().rstrip(".") for m in re.findall(r"github\.com/([\w.-]+/[\w.-]+)", text)}


def stale(pushed_at):
    pushed = datetime.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    return (datetime.datetime.now(datetime.timezone.utc) - pushed).days > 365


def check(full):
    full = full.strip().strip("/")
    full = re.sub(r"^https?://github\.com/", "", full)
    try:
        r = api(f"/repos/{full}")
    except Exception as e:
        print(f"DENY 查不到這個 repo：{full}（{e}）")
        return 1
    name = r["full_name"]
    lic = (r.get("license") or {}).get("spdx_id") or "無授權聲明"
    print(f"專案：{name}")
    print(f"網址：{r['html_url']}")
    print(f"星數：{r['stargazers_count']:,}")
    print(f"說明：{r.get('description') or '（無）'}")
    print(f"語言：{r.get('language') or '-'}｜授權：{lic}｜最後更新：{r['pushed_at'][:10]}｜封存：{r['archived']}")
    print(f"官網：{r.get('homepage') or '-'}")
    if name.lower() in introduced() or full.lower() in introduced():
        print(f"DENY 已經介紹過（GITHUB.md 有 {name}）")
        return 1
    if r["stargazers_count"] < MIN_STARS:
        print(f"DENY 星數 {r['stargazers_count']} 未達 {MIN_STARS}")
        return 1
    if r["archived"]:
        print("DENY 專案已封存（不再維護）")
        return 1
    if stale(r["pushed_at"]):
        print("DENY 超過一年沒更新")
        return 1
    if r.get("fork"):
        print("DENY 這是 fork，請介紹原專案")
        return 1
    print("OK")
    return 0


def search(words):
    since = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
    q = " ".join(words + [f"stars:>={MIN_STARS}", f"pushed:>={since}", "archived:false", "fork:false"])
    res = api(f"/search/repositories?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=50")
    done = introduced()
    n = 0
    for r in res.get("items", []):
        if r["full_name"].lower() in done:
            continue
        n += 1
        desc = (r.get("description") or "").replace("\n", " ")[:90]
        print(f"{r['stargazers_count']:>8,}★  {r['full_name']}  [{r.get('language') or '-'}]  {desc}")
        if n >= 25:
            break
    print(f"（共 {n} 筆候選，已排除 {len(done)} 個介紹過的；定案前務必再跑 check）")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("search", "check"):
        sys.exit(__doc__)
    if sys.argv[1] == "check":
        if len(sys.argv) < 3:
            sys.exit("用法：python github_repo.py check owner/repo")
        sys.exit(check(sys.argv[2]))
    sys.exit(search(sys.argv[2:]))


if __name__ == "__main__":
    main()
