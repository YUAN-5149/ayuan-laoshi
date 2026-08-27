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

# 外部 dead-man（選用）：成功就 ping，沒 ping 外部服務(如 healthchecks.io)就會提醒你。
# 即使電腦整天關機也收得到斷更通知。設環境變數 AYUAN_HEALTHCHECK_URL 即啟用，未設則略過。
function Ping-Health([string]$suffix = "") {
    if (-not $env:AYUAN_HEALTHCHECK_URL) {
        "HEALTHCHECK: 未設 AYUAN_HEALTHCHECK_URL，略過 dead-man 回報。" | Add-Content $log
        return
    }
    try {
        Invoke-RestMethod -Uri ($env:AYUAN_HEALTHCHECK_URL + $suffix) -Method Get -TimeoutSec 10 | Out-Null
        "HEALTHCHECK: ping$(if($suffix){$suffix}else{'(存活)'}) OK" | Add-Content $log
    } catch {
        "HEALTHCHECK: ping$suffix 失敗（$($_.Exception.Message)）" | Add-Content $log
    }
}

# 等網路就緒：排程喚醒的瞬間 Wi-Fi 常還沒連上，DNS 全掛會讓 sync/token 預檢/ntfy 全部誤判
# （曾因此整天沒發片、告警也推不出去；實測 15 分鐘可能仍不夠 → 預設 30 分）。
function Wait-Network {
    param([int]$MaxWaitSec = 1800, [int]$IntervalSec = 30)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $MaxWaitSec) {
        try {
            [System.Net.Dns]::GetHostAddresses('oauth2.googleapis.com') | Out-Null
            "NETWORK OK @ $(Get-Date -Format o)（等了 $([int]$sw.Elapsed.TotalSeconds)s）" | Add-Content $log
            return $true
        } catch {
            Start-Sleep -Seconds $IntervalSec
        }
    }
    "NETWORK TIMEOUT: 等了 $MaxWaitSec 秒仍無法解析 DNS。" | Add-Content $log
    return $false
}
if (-not (Wait-Network)) {
    # 沒網路什麼都做不了；桌面通知還是發得出（ntfy 需要網路、大概率也失敗，Send-Alert 内部會容錯）。
    Send-Alert "阿遠老師 無網路" "心跳啟動後等了 15 分鐘仍無網路，今天發片流程未執行，請檢查連線後手動 Start-ScheduledTask AI-YouTuber-Heartbeat。"
    Ping-Health "/fail"
    exit 1
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
    Ping-Health
    exit 0
}

# 預檢 OAuth：缺 client_secret.json 不開 Claude（省 quota；上傳一定會敗，做白工沒意義）。
if (-not (Test-Path "pipeline\client_secret.json")) {
    "SKIP: 缺 pipeline\client_secret.json，請依 README 步驟 2 完成 YouTube OAuth 設定。" | Add-Content $log
    Send-Alert "阿遠老師 缺 OAuth 憑證" "pipeline\client_secret.json 不存在，請完成 YouTube OAuth 設定（README 步驟 2）。"
    exit 0
}

# 預檢上傳 token：過期且 refresh 失敗時，與其產一支無法上傳的片（浪費整輪產線+Claude 用量），
# 不如直接告警請人工重新授權。（曾因 token 7 天過期、refresh 失敗而整支白做。）
# 治本：把 Google OAuth 同意畫面從 Testing 發布成 Production，refresh token 才不會每 7 天過期。
python "pipeline\check_upload_token.py" *>> $log
$tokenCheck = $LASTEXITCODE
if ($tokenCheck -eq 3) {
    # 網路型失敗（DNS/連線）≠ token 失效：等 60 秒再試一次；再不行就照常產片
    # （產線要跑好幾分鐘，屆時網路多半已恢復；上傳真失敗也有 Attempt 重試與告警兜底）。
    "WARN: token 預檢遇網路問題（exit 3），60 秒後重試一次。" | Add-Content $log
    Start-Sleep -Seconds 60
    python "pipeline\check_upload_token.py" *>> $log
    $tokenCheck = $LASTEXITCODE
    if ($tokenCheck -eq 3) {
        "WARN: token 預檢仍是網路問題，照常繼續產片（上傳階段自有重試/告警）。" | Add-Content $log
        $tokenCheck = 0
    }
}
if ($tokenCheck -ne 0) {
    "SKIP: 上傳 token 失效（check_upload_token 回 $tokenCheck），需人工重新授權，今天不產片。" | Add-Content $log
    Send-Alert "阿遠老師 需重新授權" "YouTube 上傳 token 失效（多半 OAuth 仍在 Testing、refresh token 每 7 天過期）。請手動跑一次 upload 完成瀏覽器授權，或把 OAuth App 發布成 Production 根治。"
    Ping-Health "/fail"
    exit 0
}

# ---- Claude CLI 登入到期預檢 ----
# 為什麼：`claude auth login` 發的 access token 只有約 8 小時（實測 2026-08-27：12:24 登入 → 20:24 到期），
# 所以隔天 06:00 的無人值守心跳幾乎必定已經過期、Agent 根本啟動不了，只丟一個看不懂的 401。
# 這裡先讀憑證檔的 claudeAiOauth.expiresAt，過期就直接發出「請重新登入」的明確告警並跳過，
# 不白跑產線、也不讓人看著 401 猜原因。
# 註：設了長效 token（環境變數 CLAUDE_CODE_OAUTH_TOKEN）時本檢查自動略過——那條路才是根治。
function Test-ClaudeLogin {
    if ($env:CLAUDE_CODE_OAUTH_TOKEN) {
        "CLI LOGIN: 使用長效 token（CLAUDE_CODE_OAUTH_TOKEN），略過到期檢查。" | Add-Content $log
        return $true
    }
    $cred = Join-Path $env:USERPROFILE ".claude\.credentials.json"
    if (-not (Test-Path $cred)) {
        "CLI LOGIN: 找不到憑證檔，略過檢查（交給 Attempt 自行嘗試）。" | Add-Content $log
        return $true
    }
    try {
        $j = Get-Content $cred -Raw -ErrorAction Stop | ConvertFrom-Json
        $ms = $j.claudeAiOauth.expiresAt
        if (-not $ms) {
            "CLI LOGIN: 憑證檔沒有 expiresAt 欄位，略過檢查。" | Add-Content $log
            return $true
        }
        $exp  = [DateTimeOffset]::FromUnixTimeMilliseconds($ms).LocalDateTime
        $mins = ($exp - (Get-Date)).TotalMinutes
        if ($mins -le 0) {
            "CLI LOGIN: 已於 $($exp.ToString('yyyy-MM-dd HH:mm')) 過期（$([math]::Abs([math]::Round($mins))) 分鐘前）。" | Add-Content $log
            return $false
        }
        "CLI LOGIN: 有效至 $($exp.ToString('yyyy-MM-dd HH:mm'))（剩 $([math]::Round($mins)) 分鐘）。" | Add-Content $log
        if ($mins -lt 90) {
            "CLI LOGIN: ⚠ 不到 90 分鐘就到期，本次可能跑到一半失效。" | Add-Content $log
        }
        return $true
    } catch {
        "CLI LOGIN: 讀取憑證檔失敗（$($_.Exception.Message)），略過檢查。" | Add-Content $log
        return $true
    }
}
if (-not (Test-ClaudeLogin)) {
    "SKIP: Claude CLI 登入已過期，今天不產片（避免白跑產線）。" | Add-Content $log
    Send-Alert "阿遠老師 CLI 登入過期" "Claude Code 登入已過期，心跳叫不動 Agent，今天沒發片。請在終端機執行 claude auth login（登入 d086110）。註：auth login 只有約 8 小時效期，長久之計是用 claude setup-token 設定長效 token。"
    Ping-Health "/fail"
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

# ---- 系列日策略（選用）----
# 指定星期固定出某個主題系列（例：把考照系列排在週四、週五）。
# 啟用條件：環境變數 AYUAN_SERIES_DAYS 有值（逗號分隔英文星期，如 "Thursday,Friday"）
# 且工作區有 SERIES.md（系列規劃書：定位、內容型態、選題順序、已講清單、SEO 規則）。
# 未設變數或找不到 SERIES.md 就完全不影響原本流程。
$SeriesDays = if ($env:AYUAN_SERIES_DAYS) { ($env:AYUAN_SERIES_DAYS -split ',') | ForEach-Object { $_.Trim() } } else { @() }
$IsSeriesDay = ((Get-Date).DayOfWeek.ToString() -in $SeriesDays) -and (Test-Path "SERIES.md")
if ($IsSeriesDay) {
    "SERIES=ON（今天 $((Get-Date).DayOfWeek) 是系列日，將依 SERIES.md 選題）" | Add-Content $log
} elseif ($SeriesDays.Count -gt 0) {
    "SERIES=off（系列日設定=$($SeriesDays -join '/')，今天不是）" | Add-Content $log
}

$maxAttempts = 2
# claude 子程序逾時上限：防止 CLI 卡死導致整個心跳無限阻塞——「卡住」是沒產出也沒告警的元兇
# （曾在週日長片日因 claude -p 無 timeout 卡死，整天沒發片也沒推播）。
# 可用環境變數 AYUAN_ATTEMPT_TIMEOUT_SEC 覆蓋，預設 1500 秒（25 分鐘，含產線+上傳綽綽有餘）。
$attemptTimeoutSec = if ($env:AYUAN_ATTEMPT_TIMEOUT_SEC) { [int]$env:AYUAN_ATTEMPT_TIMEOUT_SEC } else { 1500 }
# 解析 claude 執行檔：npm 安裝時是 claude.ps1（外部腳本），需用 powershell -File 啟動才能 PassThru 控制與逾時強殺。
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
$seriesHint = if ($IsSeriesDay) { "【最優先·今天是系列日】今天出的是 SERIES.md 指定的主題系列，不是一般科普題。動手前務必先完整讀過工作區的 SERIES.md，然後：依它的選題順序與已講清單挑題（**不要用 MEMORY.md 的一般待發題庫**）、照它指定的腳本型態寫、標題與描述套它的 SEO 規則、加它指定的播放清單、遵守它的內容準則；發完把本集補進 SERIES.md 的「已講考點」。 " } else { "" }
$prompt = "$seriesHint`n心跳：今天影片格式＝$FormatHint。請讀取 HEARTBEAT.md，依清單檢查並執行今天的工作；腳本長度與字卡張數要配合上述格式。"

for ($i = 1; $i -le $maxAttempts; $i++) {
    "=== Attempt $i / $maxAttempts @ $(Get-Date -Format o)（逾時上限 ${attemptTimeoutSec}s）===" | Add-Content $log

    # --dangerously-skip-permissions: 無人值守必須跳過權限確認。
    # 風險已透過限縮工作目錄與 SOP 控制，勿在其他目錄使用此旗標。
    $outTmp = "logs\attempt-$i.out"; $errTmp = "logs\attempt-$i.err"
    if ($claudeCmd -and $claudeCmd.CommandType -eq 'ExternalScript') {
        $startArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $claudeCmd.Source, '-p', $prompt, '--dangerously-skip-permissions')
        $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $startArgs -NoNewWindow -PassThru -RedirectStandardOutput $outTmp -RedirectStandardError $errTmp
    } else {
        $exe = if ($claudeCmd) { $claudeCmd.Source } else { 'claude' }
        $proc = Start-Process -FilePath $exe -ArgumentList @('-p', $prompt, '--dangerously-skip-permissions') -NoNewWindow -PassThru -RedirectStandardOutput $outTmp -RedirectStandardError $errTmp
    }

    $proc | Wait-Process -Timeout $attemptTimeoutSec -ErrorAction SilentlyContinue
    if (-not $proc.HasExited) {
        # 卡死：強制終止整個程序樹（含 node 子程序），讓本次視為失敗、進入重試/告警，而非無限阻塞。
        try { & taskkill /T /F /PID $proc.Id 2>&1 | Out-Null } catch {}
        try { $proc | Stop-Process -Force -ErrorAction SilentlyContinue } catch {}
        "TIMEOUT: claude 子程序超過 ${attemptTimeoutSec}s 未結束，已強制終止（第 $i 次）。" | Add-Content $log
    } else {
        "exit=$($proc.ExitCode)" | Add-Content $log
    }
    # 把子程序輸出併回主 log，再清掉暫存。
    foreach ($f in @($outTmp, $errTmp)) { if (Test-Path $f) { Get-Content $f -Raw -ErrorAction SilentlyContinue | Add-Content $log; Remove-Item $f -Force -ErrorAction SilentlyContinue } }

    if (Test-PublishedToday) {
        "RESULT=SUCCESS (偵測到今日 $today 發布紀錄)" | Add-Content $log
        Ping-Health
        exit 0
    }
    "RESULT=NO_VIDEO_YET (第 $i 次嘗試未產出今日影片)" | Add-Content $log
    if ($i -lt $maxAttempts) { Start-Sleep -Seconds 90 }
}

# 連續失敗：標記 FAILED 並發出告警（桌面通知 + 手機推播），方便人工介入。
"RESULT=FAILED 連續 $maxAttempts 次未產出今日 ($today) 影片，請人工檢查 CLI 登入與用量。" | Add-Content $log
Send-Alert "阿遠老師 發片失敗" "今日 ($today) 自動發片失敗，連續 $maxAttempts 次未產出影片，請手動檢查（claude 登入/用量）。"
Ping-Health "/fail"
exit 1
