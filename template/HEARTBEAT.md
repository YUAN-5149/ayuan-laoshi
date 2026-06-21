# HEARTBEAT.md — 心跳喚醒時的待辦清單

每次收到「心跳」訊息時，依序檢查：

0a. **先同步記憶**（若由 `heartbeat.ps1` 喚醒，這步已自動做過，可略過；若是手動 `claude` 進來則要自己跑）：執行 `python pipeline\sync_memory.py`。換電腦後 MEMORY.md 會空白，這步從頻道 RSS 把已發布影片補回，避免撞題。
0. **OAuth 憑證齊全嗎？** 若 `pipeline\client_secret.json` 不存在 → 立刻在 `MEMORY.md` 的「待金主爸爸處理」段落新增一行「缺 client_secret.json，請依 README 步驟 2 完成 YouTube OAuth 設定」（若已有同樣訊息就不重複加），然後**直接結束**。不要選題、不要寫腳本——發片到最後一步一定會失敗，做白工浪費 Claude 用量。
1. **今天發片了嗎？** 查 `MEMORY.md` 的已發布清單。今天（以系統日期為準）還沒發 → 使用 youtube-video skill 執行完整製片流程。
2. **前一支影片表現如何？** 若 `pipeline\token.json` 存在，可查 YouTube 數據；有新觀察就寫進 `MEMORY.md`。
3. **遇到無法解決的問題**（上傳失敗、產線錯誤等）→ 把問題清楚寫進 `MEMORY.md` 的「待金主爸爸處理」段落，然後結束。

原則：一次心跳只推進一件主要任務。今天已發片就直接結束，不要重複發。
