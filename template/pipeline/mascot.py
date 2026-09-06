r"""吉祥物姿勢對照表：依主題挑姿勢，並「每天換一張」讓觀眾覺得新穎。

用法（也可被其他腳本 import）:
    python mascot.py "AI 機器人"      # 印出今天該用的素材路徑（每天不同）
    python mascot.py --list          # 列出全部可用姿勢
    python mascot.py --today          # 只印今天已定的姿勢（除錯用）

挑選規則（pick）：
  1. 同一天多次呼叫 → 回同一張（整支影片的字卡+縮圖保持一致）。
  2. 首選「主題相關」的姿勢；但若它最近 ANTI_REPEAT_DAYS 天內用過，就避開。
  3. 避開後從「最久沒用」的姿勢裡挑 → 達成每天不同 + 全部姿勢平均輪替。
  歷史記在 pipeline\mascot_history.json（不進 git、每天一筆）。
"""
import datetime
import glob
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(os.path.dirname(HERE), "_ref")
HISTORY = os.path.join(HERE, "mascot_history.json")
ANTI_REPEAT_DAYS = 8  # 今天挑的姿勢盡量避開最近這幾天用過的（2026-09-06 素材 13→18 張，窗口 5→8 減少重複）

# 關鍵字 → 檔名（依主題情境挑姿勢）。第一個符合的群組勝出。
# 2026-06：改用「正黃色」一致版素材（綠頭盔），檔名對應 _ref/ 內實際檔案。
RULES = [
    (["歡迎", "開場", "嗨", "大家好", "哈囉", "打招呼", "你好"], "黃色-張手歡迎.png"),
    (["思考", "為什麼", "觀念", "原理", "幻覺", "原因", "判斷", "疑問", "迷思"], "黃色-思考.png"),
    (["通訊", "對講", "溝通", "介紹", "openai", "模型", "token", "agent", "ai", "機器人", "robot", "智慧", "解釋", "講解", "llm", "gpt"], "黃色-對講機通訊.png"),
    (["英勇", "加油", "努力", "奮鬥", "挑戰", "訂閱", "收尾", "一起", "衝", "成長"], "黃色-加油英勇.png"),
    (["指向", "重點", "注意", "看這", "標題"], "黃色-指向前方介紹.png"),
    (["鏈鋸", "鋸", "拆除"], "黃色-鏈鋸破壞.png"),
    (["圓盤", "切割機"], "黃色-圓盤切割機.png"),
    (["切割", "破壞", "工具", "tool", "油壓", "破壞器"], "黃色-電動油壓破壞器.png"),
    (["救援", "搬運", "救護", "救人", "搜救", "狗", "犬", "夥伴", "合作", "團隊"], "黃色-救援犬搜救.png"),
    (["射水", "滅火", "水", "撲滅"], "黃色-放水瞄準子.png"),
    # 2026-09-06 新增 5 張姿勢（素材庫挑出、畫風一致的綠頭盔版），讓輪替週期從 13 天延長到 18 天
    (["提問", "發問", "問題", "舉手", "打招呼", "招呼", "嗨囉"], "黃色-舉手發問.png"),
    (["檢查", "找出", "細節", "排查", "偵測", "翻找", "彎腰"], "黃色-彎腰檢查.png"),
    (["休息", "放鬆", "慢", "等待", "耐心", "坐下", "喘口氣"], "黃色-坐姿休息.png"),
    (["跟我來", "帶你", "開始", "出發", "指引", "報到"], "黃色-俯視招手.png"),
    (["側身", "旁邊", "順帶", "補充", "另外"], "黃色-側身站立.png"),
]

DEFAULT = "黃色-官方正面.png"  # 取自正本角色設定表 CHIBA-01 的正面 T-pose（權威長相）


def list_poses():
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(REF_DIR, "黃色-*.png")))


def _load_history():
    try:
        with open(HISTORY, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_history(h):
    try:
        with open(HISTORY, "w", encoding="utf-8") as f:
            json.dump(h, f, ensure_ascii=False, indent=0)
    except Exception:
        pass  # 歷史寫入失敗不擋發片


def _topic_pose(topic):
    """回主題相關的檔名（存在才回），沒有就回 None。"""
    t = (topic or "").lower()
    for keys, fname in RULES:
        if any(k.lower() in t for k in keys):
            if os.path.exists(os.path.join(REF_DIR, fname)):
                return fname
    return None


def pick(topic: str, today: str = None) -> str:
    poses = list_poses()
    if not poses:
        return ""
    today = today or datetime.date.today().isoformat()
    hist = _load_history()

    # 1) 同一天已定過 → 回同一張，整支影片一致。
    if today in hist and hist[today] in poses:
        return os.path.join(REF_DIR, hist[today])

    # 2) 最近幾天用過的姿勢（用來避免重複）。
    recent_days = sorted([d for d in hist if d < today])[-ANTI_REPEAT_DAYS:]
    recent = {hist[d] for d in recent_days}

    tp = _topic_pose(topic)
    if tp and tp not in recent:
        chosen = tp                      # 主題相關且最近沒用過 → 用它
    else:
        fresh = [p for p in poses if p not in recent] or poses
        if tp and tp in fresh:
            chosen = tp
        else:
            # 從最近沒用過的裡面，挑「歷史累計用最少」的一張 → 平均輪替、每天不同。
            cnt = Counter(hist.values())
            chosen = sorted(fresh, key=lambda p: (cnt.get(p, 0), p))[0]

    hist[today] = chosen
    _save_history(hist)
    return os.path.join(REF_DIR, chosen)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for p in list_poses():
            print(p)
    elif len(sys.argv) > 1 and sys.argv[1] == "--today":
        h = _load_history()
        t = datetime.date.today().isoformat()
        print(h.get(t, "(今天尚未決定)"))
    else:
        print(pick(sys.argv[1] if len(sys.argv) > 1 else ""))
