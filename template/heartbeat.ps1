# 心跳腳本：喚醒 Claude Code 執行每日發片流程
# 由 Windows 工作排程器呼叫（工作名稱: AI-YouTuber-Heartbeat）

Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force "logs" | Out-Null
$today = Get-Date -Format 'yyyy-MM-dd'
$log = "logs\heartbeat-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# 失敗告警：本機桌面通知 + 遠端推播（ntfy.sh，手機/桌面 App 收得到）。
# 推播主題來源優先序：環境變數 AYUAN_NTFY_TOPIC > pipeline\ntfy_topic.txt（本機、不進 git）。
# 沒設主題時只跳桌面通知、不推播（不報錯）。手機端裝 ntfy App 訂閱同一主題即可收。
function Send-Alert {
    param([string]$Title, [string]$Message)
    # 1) 本機桌面通知
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
    # 2) 遠端推播（ntfy.sh）
    $topic = $env:AYUAN_NTFY_TOPIC
    if (-not $topic -and (Test-Path "pipeline\ntfy_topic.txt")) {
        $topic = (Get-Content -Raw "pipeline\ntfy_topic.txt").Trim()
    }
    if ($topic) {
        try {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes("$Title`n$Message")
            Invoke-RestMethod -Uri "https://ntfy.sh/$topic" -Method Post -Body $bytes `
                -ContentType "text/plain; charset=utf-8" `
                -Headers @{ Title = "AYuan Laoshi Alert"; Priority = "high"; Tags = "warning,rotating_light" } | Out-Null
            "ALERT pushed to ntfy topic: $topic" | Add-Content $log
        } catch {
            "ALERT ntfy push failed: $($_.Exception.Message)" | Add-Content $log
        }
    } else {
        "ALERT no ntfy topic set（僅桌面通知）。設 AYUAN_NTFY_TOPIC 或建 pipeline\ntfy_topic.txt 可開啟手機推播。" | Add-Content $log
    }
}

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
    Send-Alert "阿遠老師 缺 OAuth 憑證" "pipeline\client_secret.json 不存在，請完成 YouTube OAuth 設定（README 步驟 2）。"
    exit 0
}

# ---- 漸進公開策略 ----
# 觀察期內發的影片設 unlisted（不公開、有連結才看得到），方便先看品質；
# 到「公開起始日」當天起自動改成 public。env 會傳給 claude 子程序與 upload_youtube.py。
#   想改觀察期長短：調整 $GoPublicDate（或設環境變數 YT_GO_PUBLIC_DATE 覆蓋）。
#   想立刻全公開：把日期設成過去；想一直 unlisted：設成很遠的未來。
# 若外部已手動指定 $env:YT_PRIVACY（例如人工測試），尊重之、不覆蓋。
if (-not $env:YT_PRIVACY) {
    if ($env:YT_GO_PUBLIC_DATE) { $GoPublicDate = [datetime]$env:YT_GO_PUBLIC_DATE }
    else { $GoPublicDate = [datetime]'2026-06-22' }   # 2026-06-22 起立即公開（攻 Shorts 需公開才有推薦流）
    if ((Get-Date).Date -lt $GoPublicDate.Date) { $env:YT_PRIVACY = 'unlisted' }
    else { $env:YT_PRIVACY = 'public' }
    "PRIVACY=$($env:YT_PRIVACY)（公開起始日 $($GoPublicDate.ToString('yyyy-MM-dd'))）" | Add-Content $log
}

# ---- 混合格式策略 ----
# 平日出直式 Shorts；指定的「長片日」(預設週日 Sunday) 出橫式 16:9 深入長片。
# 想改長片日：設環境變數 AYUAN_LONG_DAY（英文星期，如 Saturday）；想全 Shorts 設成不存在的值（如 None）。
$LongDay = if ($env:AYUAN_LONG_DAY) { $env:AYUAN_LONG_DAY } else { 'Sunday' }
if ((Get-Date).DayOfWeek.ToString() -eq $LongDay) {
    $env:VIDEO_VERTICAL = '0'
    $FormatHint = '長片（橫式 16:9、深入講解、約 2~3 分鐘、字卡 6~9 張）'
} else {
    $env:VIDEO_VERTICAL = '1'
    $FormatHint = 'Shorts（直式 9:16、精簡明快、60~90 秒、字卡 4~6 張）'
}
"FORMAT=$(if ($env:VIDEO_VERTICAL -eq '0') {'LONG 16:9'} else {'SHORTS 9:16'})（長片日=$LongDay）" | Add-Content $log

$maxAttempts = 2
for ($i = 1; $i -le $maxAttempts; $i++) {
    "=== Attempt $i / $maxAttempts @ $(Get-Date -Format o) ===" | Add-Content $log

    # --dangerously-skip-permissions: 無人值守必須跳過權限確認。
    # 風險已透過限縮工作目錄與 SOP 控制，勿在其他目錄使用此旗標。
    claude -p "心跳：今天影片格式＝$FormatHint。請讀取 HEARTBEAT.md，依清單檢查並執行今天的工作；腳本長度與字卡張數要配合上述格式。" --dangerously-skip-permissions *>> $log
    "exit=$LASTEXITCODE" | Add-Content $log

    if (Test-PublishedToday) {
        "RESULT=SUCCESS (偵測到今日 $today 發布紀錄)" | Add-Content $log
        exit 0
    }
    "RESULT=NO_VIDEO_YET (第 $i 次嘗試未產出今日影片)" | Add-Content $log
    if ($i -lt $maxAttempts) { Start-Sleep -Seconds 90 }
}

# 連續失敗：標記 FAILED 並發出告警（桌面通知 + 手機推播），方便人工介入。
"RESULT=FAILED 連續 $maxAttempts 次未產出今日 ($today) 影片，請人工檢查 CLI 登入與用量。" | Add-Content $log
Send-Alert "阿遠老師 發片失敗" "今日 ($today) 自動發片失敗，連續 $maxAttempts 次未產出影片，請手動檢查（claude 登入/用量）。"
exit 1
