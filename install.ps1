# ============================================================
#  阿遠老師 — AI YouTuber 懶人安裝包 (Windows)
#  用法（在本倉庫根目錄執行）:
#    powershell -ExecutionPolicy Bypass -File install.ps1
#  可選參數:
#    -InstallDir  安裝位置   (預設 %USERPROFILE%\ayuan-laoshi-agent)
#    -AgentName   AI 老師名字 (預設 阿遠老師)
#    -DailyTime   每日發片時間 (預設 09:00)
# ============================================================
param(
    [string]$InstallDir = "$env:USERPROFILE\ayuan-laoshi-agent",
    [string]$AgentName  = "阿遠老師",
    [string]$DailyTime  = "09:00"
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "    [X] $msg" -ForegroundColor Red; exit 1 }

# ---------- 1. 檢查必要環境 ----------
Step "檢查 Node.js 與 Python"
try { $nodeV = (node --version) } catch { Fail "未安裝 Node.js（需 v18+），請到 https://nodejs.org 安裝後重跑" }
Ok "Node.js $nodeV"
try { $pyV = (python --version) } catch { Fail "未安裝 Python（需 3.10+），請到 https://python.org 安裝後重跑" }
Ok "$pyV"

# ---------- 2. 安裝 Claude Code CLI ----------
Step "安裝 Claude Code CLI"
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) { Ok "已安裝: $(claude --version)" }
else {
    npm install -g "@anthropic-ai/claude-code"
    Ok "已安裝: $(claude --version)"
}

# ---------- 3. 安裝 ffmpeg ----------
Step "安裝 ffmpeg"
$ffCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffCmd) {
    Ok "已在 PATH: $($ffCmd.Source)"
} else {
    $toolsDir = "$env:USERPROFILE\tools"
    New-Item -ItemType Directory -Force $toolsDir | Out-Null
    $existing = Get-ChildItem $toolsDir -Directory -Filter "ffmpeg-*-essentials_build" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $existing) {
        Write-Host "    下載 ffmpeg（約 100MB，請稍候）..."
        $zip = "$toolsDir\ffmpeg.zip"
        Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip
        tar -xf $zip -C $toolsDir
        Remove-Item $zip -Force
        $existing = Get-ChildItem $toolsDir -Directory -Filter "ffmpeg-*-essentials_build" | Select-Object -First 1
    }
    if (-not $existing) { Fail "ffmpeg 解壓失敗" }
    $bin = Join-Path $existing.FullName "bin"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$bin*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User")
    }
    [Environment]::SetEnvironmentVariable("FFMPEG",  (Join-Path $bin "ffmpeg.exe"),  "User")
    [Environment]::SetEnvironmentVariable("FFPROBE", (Join-Path $bin "ffprobe.exe"), "User")
    Ok "已安裝到 $bin 並加入 PATH（新開的視窗才會生效）"
}

# ---------- 4. 安裝 Python 套件 ----------
Step "安裝 Python 套件"
python -m pip install --quiet edge-tts pillow google-api-python-client google-auth-oauthlib requests
Ok "edge-tts, pillow, google-api-python-client, google-auth-oauthlib"

# ---------- 5. 部署 Agent 工作區 ----------
Step "部署 Agent 工作區到 $InstallDir"
New-Item -ItemType Directory -Force $InstallDir | Out-Null
# MEMORY.md 是 Agent 的記憶，重跑安裝不可覆蓋
$skipIfExists = @("MEMORY.md")
Get-ChildItem "$here\template" -Recurse -File -Force | ForEach-Object {
    $rel = $_.FullName.Substring("$here\template".Length + 1)
    $dest = Join-Path $InstallDir $rel
    if (($skipIfExists -contains $rel) -and (Test-Path $dest)) { return }
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    Copy-Item $_.FullName $dest -Force
}
# 套用自訂名字
$claudeMd = Join-Path $InstallDir "CLAUDE.md"
(Get-Content $claudeMd -Raw -Encoding utf8).Replace("{{AGENT_NAME}}", $AgentName) |
    Set-Content $claudeMd -Encoding utf8 -NoNewline
Ok "工作區就緒（老師名字: $AgentName）"

# ---------- 6. 註冊每日心跳排程（先停用） ----------
Step "註冊工作排程器: AI-YouTuber-Heartbeat（每天 $DailyTime，先停用）"
$action   = New-ScheduledTaskAction -Execute "powershell.exe" `
            -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$InstallDir\heartbeat.ps1`""
$trigger  = New-ScheduledTaskTrigger -Daily -At $DailyTime
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName "AI-YouTuber-Heartbeat" -Action $action -Trigger $trigger `
    -Settings $settings -Description "每天喚醒 Claude Code 製作並上傳 YouTube 影片" -Force | Out-Null
Disable-ScheduledTask -TaskName "AI-YouTuber-Heartbeat" | Out-Null
Ok "已註冊（停用中，完成設定後再開啟）"

# ---------- 完成 ----------
Write-Host @"

============================================================
 安裝完成！剩下 3 步需要你親手做（詳見 README.md）:

 1. CLI 登入（一次性）:
      cd $InstallDir
      claude        # 進入後輸入 /login

 2. YouTube 上傳授權（一次性）:
      Google Cloud Console 啟用 YouTube Data API v3，
      下載桌面版 OAuth 憑證存成 pipeline\client_secret.json，
      跑一次測試上傳完成瀏覽器授權。

 3. 開啟每日自動發片:
      Enable-ScheduledTask -TaskName "AI-YouTuber-Heartbeat"

 手動測試一次心跳:
      powershell -ExecutionPolicy Bypass -File $InstallDir\heartbeat.ps1
============================================================
"@ -ForegroundColor Yellow
