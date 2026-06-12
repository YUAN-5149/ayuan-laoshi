# HEARTBEAT.md — 心跳喚醒時的待辦清單

每次收到「心跳」訊息時，依序檢查：

1. **今天發片了嗎？** 查 `MEMORY.md` 的已發布清單。今天（以系統日期為準）還沒發 → 使用 youtube-video skill 執行完整製片流程。
2. **前一支影片表現如何？** 若 `pipeline\token.json` 存在，可查 YouTube 數據；有新觀察就寫進 `MEMORY.md`。
3. **遇到無法解決的問題**（如缺 client_secret.json、上傳失敗）→ 把問題清楚寫進 `MEMORY.md` 的「待金主爸爸處理」段落，然後結束。

原則：一次心跳只推進一件主要任務。今天已發片就直接結束，不要重複發。
