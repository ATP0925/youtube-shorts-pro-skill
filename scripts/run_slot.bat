@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0..
if defined YT_PRO_HOME set ROOT=%YT_PRO_HOME%
cd /d "%ROOT%"

set SLOT=%1
if "%SLOT%"=="" set SLOT=auto

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"
set LOG_FILE=%ROOT%\logs\yt_shorts_publisher.log

where python >nul 2>nul
if errorlevel 1 (
    echo [%date% %time%] ERROR: Python executable not found in PATH.>> "%LOG_FILE%"
    echo ERROR: Python executable not found in PATH.
    exit /b 9009
)

echo ============================================================================>> "%LOG_FILE%"
echo [%date% %time%] Starting YouTube Shorts Pipeline (slot=%SLOT%, args=%2 %3 %4)>> "%LOG_FILE%"

python -u "%~dp0youtube_shorts_daily_pipeline.py" --slot %SLOT% %2 %3 %4 >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%errorlevel%

echo [%date% %time%] Finished with exit code %EXIT_CODE%>> "%LOG_FILE%"
exit /b %EXIT_CODE%
