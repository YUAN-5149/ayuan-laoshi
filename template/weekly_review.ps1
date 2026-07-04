# 每週復盤腳本：喚醒 Claude Code 依 WEEKLY_REVIEW.md 用數據修正選題方向。
# 由 Windows 工作排程器呼叫（工作名稱: AI-YouTuber-Weekly-Review，每週六）。
# 只做分析＋更新 MEMORY.md，不發片、不上傳。

Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force "logs" | Out-Null
$log = "logs\weekly-review-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# 失敗告警：桌面通知 + ntfy 推播（與心跳同一套主題）。
function Send-Alert {
    param([string]$Title, [string]$Message)
    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $n = New-Object System.Windows.Forms.NotifyIcon
        $n.Icon = [System.Drawing.SystemIcons]::Warning
        $n.Visible = $true
        $n.ShowBalloonTip(15000, $Title, $Message, [System.Windows.Forms.ToolTipIcon]::Warning)
        Start-Sleep -Seconds 12
        $n.Dispose()
    } catch {}
    $topic = $env:AYUAN_NTFY_TOPIC
    if (-not $topic -and (Test-Path "pipeline\ntfy_topic.txt")) {
        $topic = (Get-Content -Raw "pipeline\ntfy_topic.txt").Trim()
    }
    if ($topic) {
        try {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes("$Title`n$Message")
            Invoke-RestMethod -Uri "https://ntfy.sh/$topic" -Method Post -Body $bytes `
                -ContentType "text/plain; charset=utf-8" `
                -Headers @{ Title = "AYuan Laoshi Weekly"; Priority = "default"; Tags = "bar_chart" } | Out-Null
        } catch {}
    }
}

"=== 週復盤開始 @ $(Get-Date -Format o) ===" | Add-Content $log

# 1) 先刷新數據（缺 token 也不擋，claude 會用現有 ANALYTICS.md）。
"--- fetch_analytics ---" | Add-Content $log
python "pipeline\fetch_analytics.py" *>> $log

# 2) 喚醒 claude 做復盤，包 timeout 防卡死（與心跳同機制）。
$attemptTimeoutSec = if ($env:AYUAN_ATTEMPT_TIMEOUT_SEC) { [int]$env:AYUAN_ATTEMPT_TIMEOUT_SEC } else { 1500 }
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
$prompt = "週復盤：請讀取 WEEKLY_REVIEW.md，依清單用本週數據檢視爆款/冷門、歸納有效模式，並回寫 MEMORY.md 的選題題庫與下次改進方向。只做分析與更新記憶，不要發片或上傳。"

"=== 喚醒 claude 復盤 @ $(Get-Date -Format o)（逾時上限 ${attemptTimeoutSec}s）===" | Add-Content $log
$outTmp = "logs\weekly.out"; $errTmp = "logs\weekly.err"
if ($claudeCmd -and $claudeCmd.CommandType -eq 'ExternalScript') {
    $startArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $claudeCmd.Source, '-p', $prompt, '--dangerously-skip-permissions')
    $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $startArgs -NoNewWindow -PassThru -RedirectStandardOutput $outTmp -RedirectStandardError $errTmp
} else {
    $exe = if ($claudeCmd) { $claudeCmd.Source } else { 'claude' }
    $proc = Start-Process -FilePath $exe -ArgumentList @('-p', $prompt, '--dangerously-skip-permissions') -NoNewWindow -PassThru -RedirectStandardOutput $outTmp -RedirectStandardError $errTmp
}
$proc | Wait-Process -Timeout $attemptTimeoutSec -ErrorAction SilentlyContinue
if (-not $proc.HasExited) {
    try { & taskkill /T /F /PID $proc.Id 2>&1 | Out-Null } catch {}
    try { $proc | Stop-Process -Force -ErrorAction SilentlyContinue } catch {}
    "TIMEOUT: 復盤的 claude 子程序超過 ${attemptTimeoutSec}s 未結束，已強制終止。" | Add-Content $log
    Send-Alert "阿遠老師 週復盤逾時" "週復盤的 claude 子程序卡住已被終止，請手動檢查。"
} else {
    "exit=$($proc.ExitCode)" | Add-Content $log
}
foreach ($f in @($outTmp, $errTmp)) { if (Test-Path $f) { Get-Content $f -Raw -ErrorAction SilentlyContinue | Add-Content $log; Remove-Item $f -Force -ErrorAction SilentlyContinue } }

"=== 週復盤結束 @ $(Get-Date -Format o) ===" | Add-Content $log
exit 0
