# ============================================================
# YouTube 자동 요약 - Windows 작업 스케줄러 등록
# ============================================================
# 실행: PowerShell -ExecutionPolicy Bypass -File register_scheduler.ps1
# ============================================================

param(
    [int]$IntervalMinutes = 30,
    [switch]$Unregister
)

$TaskName = "YouTubeAutoSummarizer"
$ScriptPath = Join-Path $PSScriptRoot "youtube_summarizer.py"
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonPath) {
    Write-Error "Python이 설치되어 있지 않거나 PATH에 없습니다."
    exit 1
}

# 삭제 모드
if ($Unregister) {
    Write-Host "작업 스케줄러에서 삭제 중..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "삭제 완료!" -ForegroundColor Green
    exit 0
}

# 기존 작업 삭제
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# 작업 생성
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $PSScriptRoot

# 반복 트리거 (30분마다)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 9999)

# 설정
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# 현재 사용자로 실행
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

# 등록
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "YouTube 채널 새 영상 자동 요약 시스템"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " YouTube 자동 요약 스케줄러 등록 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "작업명: $TaskName"
Write-Host "실행 간격: ${IntervalMinutes}분마다"
Write-Host ""
Write-Host "수동 실행: schtasks /run /tn `"$TaskName`""
Write-Host "상태 확인: schtasks /query /tn `"$TaskName`""
Write-Host "삭제: .\register_scheduler.ps1 -Unregister"
Write-Host ""
