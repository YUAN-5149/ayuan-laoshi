r"""「阿遠實測」用：把同一個問題丟給多個 AI，存下原文答案，並畫成對話截圖卡（可當字卡插圖）。

用法:
    python ask_ai.py ask   <問題檔.txt> <輸出資料夾> [gpt,claude]
    python ask_ai.py card  <答案.txt> <輸出.png> "<標籤，如 ChatGPT 的回答>" [最多字數]

- ask：每個模型各問一次（純問答、唯讀，不讓它動任何檔案），答案存成 <輸出資料夾>\<模型>.txt，
       並各畫一張 <模型>_card.png（截前段）。最後印出 OK/FAIL 摘要。
  * gpt    ＝ Codex CLI（ChatGPT 月費，不花 API 錢）
  * claude ＝ Claude CLI（claude -p，純文字回答）
- card：把任一段文字畫成對話截圖卡（例如只想截答案裡的某一段來當證據）。

問題檔一律用 UTF-8 檔案傳（中文走命令列參數會亂碼）。每個模型逾時 240 秒；某個失敗不影響其他。
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import style as S  # noqa: E402  頻道字型與配色

TIMEOUT = int(os.environ.get("AYUAN_ASK_TIMEOUT", "240"))
LABELS = {"gpt": "ChatGPT", "claude": "Claude"}


def find_codex():
    p = os.environ.get("CODEX_CLI_PATH")
    if p and os.path.exists(p):
        return p
    root = os.path.join(os.environ.get("LOCALAPPDATA", ""), "OpenAI", "Codex", "bin")
    cands = sorted(glob.glob(os.path.join(root, "**", "codex.exe"), recursive=True),
                   key=os.path.getmtime, reverse=True)
    return cands[0] if cands else "codex"


def ask_gpt(question):
    work = tempfile.mkdtemp()
    out = os.path.join(work, "last.txt")
    qf = os.path.join(work, "q.txt")
    with open(qf, "w", encoding="utf-8") as f:
        f.write(question)
    args = [find_codex(), "exec", "-s", "read-only", "-C", work, "-", "--skip-git-repo-check",
            "--ignore-user-config", "--output-last-message", out]
    with open(qf, encoding="utf-8") as fin:  # stdin 一定要給到 EOF，否則 codex 會卡住
        subprocess.run(args, stdin=fin, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=TIMEOUT, check=False)
    if not os.path.exists(out):
        raise RuntimeError("codex 沒有產出答案")
    with open(out, encoding="utf-8") as f:
        return f.read().strip()


def claude_env():
    """長效 token 存在使用者層環境變數；從舊程序叫起時繼承不到（會 401），直接從登錄檔補讀。"""
    env = dict(os.environ)
    if not env.get("CLAUDE_CODE_OAUTH_TOKEN") and os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                env["CLAUDE_CODE_OAUTH_TOKEN"] = winreg.QueryValueEx(k, "CLAUDE_CODE_OAUTH_TOKEN")[0]
        except OSError:
            pass
    return env


def ask_claude(question):
    # 純問答：不給 --dangerously-skip-permissions，模型想用工具也拿不到權限，只會用文字回答。
    exe = "claude.cmd" if os.name == "nt" else "claude"
    r = subprocess.run([exe, "-p", "--output-format", "text"], input=question, text=True,
                       encoding="utf-8", capture_output=True, timeout=TIMEOUT, check=False,
                       env=claude_env())
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"claude -p exit={r.returncode} {r.stderr.strip()[:200]}")
    return r.stdout.strip()


BACKENDS = {"gpt": ask_gpt, "claude": ask_claude}


def wrap(draw, text, font, max_w):
    lines = []
    for para in text.splitlines() or [""]:
        line = ""
        for ch in para:
            if draw.textlength(line + ch, font=font) > max_w:
                lines.append(line)
                line = ch
            else:
                line += ch
        lines.append(line)
    return lines


def render_card(text, out_png, label, limit=220):
    """暖白底對話截圖卡（方形 1200x1200），上方標籤、下方答案前段。超過字數用「…」截斷。"""
    W = H = 1200
    pad = 70
    img = Image.new("RGB", (W, H), (250, 244, 232))
    d = ImageDraw.Draw(img)
    import re
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)   # [文字](網址) 只留文字
    clean = re.sub(r"https?://\S+", "", clean).replace("**", "").replace("#", "").strip()
    if len(clean) > limit:
        clean = clean[:limit].rstrip() + "…"
    lf = S.load_font(56)
    tf = S.load_font(46)
    # 標籤膠囊
    lw = int(d.textlength(label, font=lf)) + 60
    d.rounded_rectangle([pad, pad, pad + lw, pad + 96], radius=48, fill=S.RED)
    d.text((pad + 30, pad + 16), label, font=lf, fill=(255, 255, 255))
    # 對話泡泡
    top = pad + 140
    d.rounded_rectangle([pad, top, W - pad, H - pad], radius=40, fill=(255, 255, 255), outline=S.INK, width=4)
    y = top + 50
    for line in wrap(d, clean, tf, W - pad * 2 - 100):
        if y > H - pad - 80:
            break
        d.text((pad + 50, y), line, font=tf, fill=S.INK)
        y += 66
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    img.save(out_png)


def cmd_ask(qfile, outdir, models):
    with open(qfile, encoding="utf-8") as f:
        question = f.read().strip()
    os.makedirs(outdir, exist_ok=True)
    summary = {}
    for m in models:
        t = time.time()
        try:
            ans = BACKENDS[m](question)
            with open(os.path.join(outdir, f"{m}.txt"), "w", encoding="utf-8") as f:
                f.write(ans)
            render_card(ans, os.path.join(outdir, f"{m}_card.png"), f"{LABELS[m]} 的回答")
            summary[m] = f"OK {len(ans)}字 {time.time() - t:.0f}s"
        except Exception as e:  # 單一模型失敗不擋其他
            summary[m] = f"FAIL {type(e).__name__}: {e}"
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"question": question, "result": summary}, f, ensure_ascii=False, indent=1)
    for m, s in summary.items():
        print(f"{m}: {s}")
    return 0 if any(s.startswith("OK") for s in summary.values()) else 1


def main():
    if len(sys.argv) < 4 or sys.argv[1] not in ("ask", "card"):
        sys.exit(__doc__)
    if sys.argv[1] == "ask":
        models = (sys.argv[4] if len(sys.argv) > 4 else "gpt,claude").split(",")
        sys.exit(cmd_ask(sys.argv[2], sys.argv[3], [m.strip() for m in models if m.strip() in BACKENDS]))
    with open(sys.argv[2], encoding="utf-8") as f:
        text = f.read()
    render_card(text, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "AI 的回答",
                int(sys.argv[5]) if len(sys.argv) > 5 else 220)
    print(f"OK: {sys.argv[3]}")


if __name__ == "__main__":
    main()
