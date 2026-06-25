@echo off
chcp 65001 > nul
echo ========================================
echo YouTube 자동 요약 시스템 실행
echo ========================================

cd /d "%~dp0"

REM Python 실행
python youtube_summarizer.py %*

if %ERRORLEVEL% NEQ 0 (
    echo [오류] 스크립트 실행 실패
    pause
    exit /b 1
)

echo.
echo 완료!
