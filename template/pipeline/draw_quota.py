"""阿遠老師 /draw 生圖額度守門員。

規則（金主訂）：
- 一週最多調用 3 次 /draw（滾動 7 天視窗）。
- quality 用預設 low，不要調高。
- 只畫「黃色消防員阿遠」的角色圖：情境 / 簡報 / 教學插圖 / 封面 / demo。
- 每次放行都用 ntfy 通知金主。

用法（製作影片要畫圖前，務必先呼叫）:
    python draw_quota.py check            # 只看還剩幾次（不扣）；有額度 exit 0、用完 exit 1
    python draw_quota.py claim "<用途>"   # 真的要畫之前呼叫：有額度→記錄+通知+exit 0；用完→exit 1

claim 回 exit 0 才可以接著用 /draw（quality 預設 low）；回 exit 1 代表本週額度用完，這次不要畫。
"""
import datetime as dt
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "draw_log.json")
TOPIC_FILE = os.path.join(HERE, "ntfy_topic.txt")
LIMIT = 3
WINDOW_DAYS = 7


def _load():
    if os.path.exists(LOG):
        try:
            return json.load(open(LOG, encoding="utf-8"))
        except Exception:
            return []
    return []


def _recent(events):
    cutoff = dt.datetime.now() - dt.timedelta(days=WINDOW_DAYS)
    out = []
    for e in events:
        try:
            if dt.datetime.fromisoformat(e["ts"]) >= cutoff:
                out.append(e)
        except Exception:
            pass
    return out


def _ntfy(title, msg):
    topic = os.environ.get("AYUAN_NTFY_TOPIC")
    if not topic and os.path.exists(TOPIC_FILE):
        topic = open(TOPIC_FILE, encoding="utf-8").read().strip()
    if not topic:
        return
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=f"{title}\n{msg}".encode("utf-8"),
            headers={"Title": "AYuan Laoshi Draw", "Priority": "default", "Tags": "art"},
        )
        urllib.request.urlopen(req, timeout=10).read()
    except Exception:
        pass


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    events = _load()
    recent = _recent(events)
    used = len(recent)
    remaining = max(0, LIMIT - used)

    if cmd == "check":
        print(f"本週已用 {used}/{LIMIT} 次，剩 {remaining} 次。")
        sys.exit(0 if remaining > 0 else 1)

    if cmd == "claim":
        desc = sys.argv[2] if len(sys.argv) > 2 else "(未註明用途)"
        if remaining <= 0:
            oldest = min((e["ts"] for e in recent), default="")
            print(f"DENY：本週 /draw 額度已用完（{used}/{LIMIT}）。最早一次在 {oldest[:10]}，"
                  f"滿 7 天後才會釋出。這次請勿生圖。")
            _ntfy("阿遠老師 生圖額度用完", f"想畫「{desc}」但本週已達 {LIMIT} 次上限，已擋下。")
            sys.exit(1)
        events.append({"ts": dt.datetime.now().isoformat(timespec="seconds"), "desc": desc})
        json.dump(events, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"OK：可生圖（quality=low）。這是本週第 {used + 1}/{LIMIT} 次，剩 {remaining - 1} 次。")
        _ntfy("阿遠老師 要生圖了", f"用途：{desc}\n本週第 {used + 1}/{LIMIT} 次（quality=low）。")
        sys.exit(0)

    print(f"未知指令：{cmd}（用 check 或 claim）")
    sys.exit(2)


if __name__ == "__main__":
    main()
