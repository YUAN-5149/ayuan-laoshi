"""吉祥物姿勢對照表：依主題關鍵字挑選最合適的消防員素材。

用法（也可被其他腳本 import）:
    python mascot.py "AI 機器人"      # 印出最合適的素材路徑
    python mascot.py --list          # 列出全部可用姿勢
"""
import glob
import os
import sys

REF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_ref")

# 關鍵字 → 檔名（依主題情境挑姿勢）。第一個符合的群組勝出。
RULES = [
    (["機器人", "robot", "agent", "ai", "自動", "智慧"], "黃色-消防機器人2.png"),
    (["無人機", "drone", "空拍", "偵察"], "黃色-無人機.png"),
    (["熱顯像", "感測", "偵測", "視覺", "鏡頭", "sensor", "vision"], "黃色-無人機.png"),
    (["思考", "為什麼", "觀念", "原理", "幻覺", "原因", "判斷"], "黃色-低頭凝視，雙手抱胸前，呈現思考或觀察的姿勢。.png"),
    (["通訊", "對講", "溝通", "介紹", "openai", "模型", "token"], "黃色-側身站立，頭朝前看，一手搭在腰間，另一手拿著一個小型的對講機，準備通訊。.png"),
    (["切割", "破壞", "工具", "tool"], "黃色-電動油壓破壞器.png"),
    (["鏈鋸", "鋸"], "黃色-鏈鋸.png"),
    (["圓盤", "切割機"], "黃色-圓盤切割機.png"),
    (["射水", "滅火", "水", "撲滅"], "黃色-放水瞄準子.png"),
    (["救援", "搬運", "救護", "救人", "搜救", "狗", "犬", "夥伴", "合作", "團隊"], "黃色-救援犬搜救.png"),
    (["車", "出勤", "救護車"], "黃色-消防車救護車2.png"),
    (["檢查", "巡檢", "觀察", "地面"], "黃色-身體蹲下，頭部平視，雙手放在膝蓋上，進行檢查或觀察地面的動作。.png"),
    (["歡迎", "開場", "嗨", "大家好"], "黃色-頭稍微有點恍惚，閱讀展開，好像在歡迎或截圖安全。.png"),
    (["英勇", "加油", "努力", "奮鬥", "挑戰"], "黃色-頭顱向上看，一手握拳舉起，另一手向前伸展，做出英勇奮鬥的姿勢。.png"),
]

DEFAULT = "黃色-指向前方介紹.png"


def list_poses():
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(REF_DIR, "黃色-*.png")))


def pick(topic: str) -> str:
    t = topic.lower()
    for keys, fname in RULES:
        if any(k.lower() in t for k in keys):
            cand = os.path.join(REF_DIR, fname)
            if os.path.exists(cand):
                return cand
    # 退回預設；預設不存在就挑任一張
    cand = os.path.join(REF_DIR, DEFAULT)
    if os.path.exists(cand):
        return cand
    poses = list_poses()
    return os.path.join(REF_DIR, poses[0]) if poses else ""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for p in list_poses():
            print(p)
    else:
        print(pick(sys.argv[1] if len(sys.argv) > 1 else ""))
