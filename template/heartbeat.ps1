# 心跳腳本：喚醒 Claude Code 執行每日發片流程
# 由 Windows 工作排程器呼叫（工作名稱: AI-YouTuber-Heartbeat）

Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force "logs" | Out-Null
$log = "logs\heartbeat-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# --dangerously-skip-permissions: 無人值守必須跳過權限確認。
# 風險已透過限縮工作目錄與 SOP 控制，勿在其他目錄使用此旗標。
claude -p "心跳：請讀取 HEARTBEAT.md，依照清單檢查並執行今天的工作。" --dangerously-skip-permissions *> $log

"exit=$LASTEXITCODE" | Add-Content $log
