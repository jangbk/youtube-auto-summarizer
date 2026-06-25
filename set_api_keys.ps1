# ============================================================
# YouTube 자동 요약 - API 키 환경 변수 설정
# ============================================================
# 실행: PowerShell -ExecutionPolicy Bypass -File set_api_keys.ps1
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " API 키 환경 변수 설정" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Claude API 키
Write-Host "[1/4] Claude API 키" -ForegroundColor Yellow
Write-Host "      (https://console.anthropic.com/)" -ForegroundColor Gray
$claudeKey = Read-Host "      입력 (Enter로 스킵)"
if ($claudeKey) {
    [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $claudeKey, "User")
    Write-Host "      설정 완료!" -ForegroundColor Green
} else {
    $existing = [Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "User")
    if ($existing) {
        Write-Host "      기존 값 유지: $($existing.Substring(0,10))..." -ForegroundColor Gray
    } else {
        Write-Host "      스킵됨" -ForegroundColor Gray
    }
}

# YouTube API 키
Write-Host ""
Write-Host "[2/4] YouTube Data API 키" -ForegroundColor Yellow
Write-Host "      (https://console.cloud.google.com/)" -ForegroundColor Gray
$youtubeKey = Read-Host "      입력 (Enter로 스킵)"
if ($youtubeKey) {
    [Environment]::SetEnvironmentVariable("YOUTUBE_API_KEY", $youtubeKey, "User")
    Write-Host "      설정 완료!" -ForegroundColor Green
} else {
    $existing = [Environment]::GetEnvironmentVariable("YOUTUBE_API_KEY", "User")
    if ($existing) {
        Write-Host "      기존 값 유지: $($existing.Substring(0,10))..." -ForegroundColor Gray
    } else {
        Write-Host "      스킵됨" -ForegroundColor Gray
    }
}

# Notion API 키
Write-Host ""
Write-Host "[3/4] Notion API 키" -ForegroundColor Yellow
Write-Host "      (https://www.notion.so/my-integrations)" -ForegroundColor Gray
$notionKey = Read-Host "      입력 (Enter로 스킵)"
if ($notionKey) {
    [Environment]::SetEnvironmentVariable("NOTION_API_KEY", $notionKey, "User")
    Write-Host "      설정 완료!" -ForegroundColor Green
} else {
    $existing = [Environment]::GetEnvironmentVariable("NOTION_API_KEY", "User")
    if ($existing) {
        Write-Host "      기존 값 유지: $($existing.Substring(0,10))..." -ForegroundColor Gray
    } else {
        Write-Host "      스킵됨" -ForegroundColor Gray
    }
}

# Notion 데이터베이스 ID
Write-Host ""
Write-Host "[4/4] Notion 데이터베이스 ID" -ForegroundColor Yellow
Write-Host "      (노션 DB URL에서 추출: notion.so/[DATABASE_ID]?v=...)" -ForegroundColor Gray
$notionDbId = Read-Host "      입력 (Enter로 스킵)"
if ($notionDbId) {
    [Environment]::SetEnvironmentVariable("NOTION_DATABASE_ID", $notionDbId, "User")
    Write-Host "      설정 완료!" -ForegroundColor Green
} else {
    $existing = [Environment]::GetEnvironmentVariable("NOTION_DATABASE_ID", "User")
    if ($existing) {
        Write-Host "      기존 값 유지: $($existing.Substring(0,10))..." -ForegroundColor Gray
    } else {
        Write-Host "      스킵됨" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "환경 변수가 설정되었습니다."
Write-Host "새 PowerShell 창을 열어야 적용됩니다."
Write-Host ""
Write-Host "확인 명령어:"
Write-Host '  $env:ANTHROPIC_API_KEY'
Write-Host '  $env:YOUTUBE_API_KEY'
Write-Host ""
