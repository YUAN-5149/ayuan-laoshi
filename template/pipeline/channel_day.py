"""計算頻道「第幾天」與基本養成數據，供碎碎念開場與每週回顧使用。

天數 = 今天 - 最早一支影片日期 + 1（只讀 MEMORY.md 裡的 `PUBLISHED:yyyy-mm-dd` 標記，
因此非 AI 系列影片的日期不會干擾天數）。若還沒有任何已發布標記，回傳第 1 天。

用法:
    python channel_day.py          # 印出：第 N 天｜已發布 M 支
"""
import datetime
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY = os.path.join(ROOT, "MEMORY.md")


def stats():
    dates = []
    if os.path.exists(MEMORY):
        with open(MEMORY, encoding="utf-8") as f:
            for m in re.finditer(r"PUBLISHED:(\d{4})-(\d{2})-(\d{2})", f.read()):
                try:
                    dates.append(datetime.date(int(m[1]), int(m[2]), int(m[3])))
                except ValueError:
                    pass
    today = datetime.date.today()
    if dates:
        start = min(dates)
        day = (today - start).days + 1
        count = len(set(dates))
    else:
        day, count = 1, 0
    return day, count


if __name__ == "__main__":
    day, count = stats()
    print(f"第 {day} 天｜已發布 {count} 支")
