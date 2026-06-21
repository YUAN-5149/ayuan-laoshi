# 心跳腳本：喚醒 Claude Code 執行每日發片流程
# 由 Windows 工作排程器呼叫（工作名稱: AI-YouTuber-Heartbeat）

Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force "logs" | Out-Null
$today = Get-Date -Format 'yyyy-MM-dd'
$log = "logs\heartbeat-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# 先從頻道 RSS 同步記憶：換電腦後 MEMORY.md 會空白，這步把已發布影片補回，避免撞題。
# 失敗（沒網路等）腳本內部自會 exit 0，不擋心跳；接著的 dedup 也才會讀到最新記憶。
"=== 同步記憶 (sync_memory) @ $(Get-Date -Format o) ===" | Add-Content $log
python "pipeline\sync_memory.py" *>> $log

# 偵測「今天是否已成功發片」：MEMORY.md 含 `<!-- PUBLISHED:YYYY-MM-DD -->` 標記才算。
# 用明確標記避免誤判（例如 Agent 在「待處理」段落寫到今天日期會被當成已發片）。
function Test-PublishedToday {
    if (-not (Test-Path "MEMORY.md")) { return $false }
    $marker = "<!-- PUBLISHED:$today -->"
    return [bool](Select-String -Path "MEMORY.md" -SimpleMatch $marker -Quiet)
}

# 若今天「已經」發過片，直接結束，避免重複工作。
if (Test-PublishedToday) {
    "SKIP: 今天 ($today) 已有發布紀錄，無需再跑。" | Add-Content $log
    exit 0
}

# 預檢 OAuth：缺 client_secret.json 不開 Claude（省 quota；上傳一定會敗，做白工沒意義）。
if (-not (Test-Path "pipeline\client_secret.json")) {
    "SKIP: 缺 pipeline\client_secret.json，請依 README 步驟 2 完成 YouTube OAuth 設定。" | Add-Content $log
    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $n = New-Object System.Windows.Forms.NotifyIcon
        $n.Icon = [System.Drawing.SystemIcons]::Warning
        $n.Visible = $true
        $n.ShowBalloonTip(15000, "阿遠老師 缺 OAuth 憑證", "pipeline\client_secret.json 不存在，請完成 YouTube OAuth 設定（README 步驟 2）。", [System.Windows.Forms.ToolTipIcon]::Warning)
        Start-Sleep -Seconds 12
        $n.Dispose()
    } catch {}
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
