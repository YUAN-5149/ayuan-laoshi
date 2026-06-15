# 心跳腳本：喚醒 Claude Code 執行每日發片流程
# 由 Windows 工作排程器呼叫（工作名稱: AI-YouTuber-Heartbeat）

Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force "logs" | Out-Null
$today = Get-Date -Format 'yyyy-MM-dd'
$log = "logs\heartbeat-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# 偵測「今天是否已成功發片」：MEMORY.md 的已發布清單含今天日期即視為成功。
# 這與 Agent 自己的去重判斷同源，故重試不會重複發片。
function Test-PublishedToday {
    if (-not (Test-Path "MEMORY.md")) { return $false }
    return [bool](Select-String -Path "MEMORY.md" -SimpleMatch $today -Quiet)
}

# 若今天「已經」發過片，直接結束，避免重複工作。
if (Test-PublishedToday) {
    "SKIP: 今天 ($today) 已有發布紀錄，無需再跑。" | Add-Content $log
    exit 0
}

$maxAttempts = 2
for ($i = 1; $i -le $maxAttempts; $i++) {
    "=== Attempt $i / $maxAttempts @ $(Get-Date -Format o) ===" | Add-Content $log

    # --dangerously-skip-permissions: 無人值守必須跳過權限確認。
    # 風險已透過限縮工作目錄與 SOP 控制，勿在其他目錄使用此旗標。
    claude -p "心跳：請讀取 HEARTBEAT.md，依照清單檢查並執行今天的工作。" --dangerously-skip-permissions *>> $log
    "exit=$LASTEXITCODE" | Add-Content $log

    if (Test-PublishedToday) {
        "RESULT=SUCCESS (偵測到今日 $today 發布紀錄)" | Add-Content $log
        exit 0
    }
    "RESULT=NO_VIDEO_YET (第 $i 次嘗試未產出今日影片)" | Add-Content $log
    if ($i -lt $maxAttempts) { Start-Sleep -Seconds 90 }
}

# 連續失敗：標記 FAILED 並彈出桌面通知，方便人工介入。
"RESULT=FAILED 連續 $maxAttempts 次未產出今日 ($today) 影片，請人工檢查 CLI 登入與用量。" | Add-Content $log
try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $n = New-Object System.Windows.Forms.NotifyIcon
    $n.Icon = [System.Drawing.SystemIcons]::Warning
    $n.Visible = $true
    $n.ShowBalloonTip(15000, "阿遠老師 發片失敗", "今日 ($today) 自動發片失敗，請手動檢查（claude 登入/用量）。", [System.Windows.Forms.ToolTipIcon]::Warning)
    Start-Sleep -Seconds 12
    $n.Dispose()
} catch {}
exit 1
