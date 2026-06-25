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
]

DEFAULT = "黃色-官方正面.png"  # 取自正本角色設定表 CHIBA-01 的正面 T-pose（權威長相）


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
