# ============================================================
# YouTube 자동 요약 시스템 - 초기 설정 스크립트
# ============================================================
# 실행: PowerShell -ExecutionPolicy Bypass -File setup.ps1
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " YouTube 자동 요약 시스템 설정" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Python 패키지 설치
Write-Host "[1/4] Python 패키지 설치 중..." -ForegroundColor Yellow
pip install -r "$ScriptDir\requirements.txt" --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "      Python 패키지 설치 완료!" -ForegroundColor Green
} else {
    Write-Host "      [경고] 일부 패키지 설치 실패" -ForegroundColor Red
}

# 2. 설정 파일 확인
Write-Host ""
Write-Host "[2/4] 설정 파일 확인..." -ForegroundColor Yellow
$ConfigPath = "$ScriptDir\config.yaml"

if (Test-Path $ConfigPath) {
    Write-Host "      config.yaml 존재함" -ForegroundColor Green
    Write-Host ""
    Write-Host "      [중요] config.yaml을 열어 다음 항목을 설정하세요:" -ForegroundColor Cyan
    Write-Host "      - api_keys.claude: Claude API 키"
    Write-Host "      - api_keys.youtube: YouTube Data API 키"
    Write-Host "      - api_keys.notion: Notion API 키"
    Write-Host "      - notion.database_id: Notion 데이터베이스 ID"
    Write-Host "      - channels.[].channel_id: 각 채널의 YouTube 채널 ID"
} else {
    Write-Host "      [오류] config.yaml이 없습니다!" -ForegroundColor Red
}

# 3. 채널 ID 조회
Write-Host ""
Write-Host "[3/4] 채널 ID 조회 (API 키 설정 후 실행)..." -ForegroundColor Yellow
Write-Host "      명령어: python youtube_summarizer.py --setup"

# 4. 스케줄러 등록 안내
Write-Host ""
Write-Host "[4/4] 스케줄러 등록..." -ForegroundColor Yellow
Write-Host "      명령어: .\register_scheduler.ps1"
Write-Host "      또는: .\register_scheduler.ps1 -IntervalMinutes 60"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:"
Write-Host "1. config.yaml에 API 키 입력"
Write-Host "2. python youtube_summarizer.py --setup (채널 ID 확인)"
Write-Host "3. config.yaml에 채널 ID 입력"
Write-Host "4. python youtube_summarizer.py (수동 테스트)"
Write-Host "5. .\register_scheduler.ps1 (자동화 등록)"
Write-Host ""
