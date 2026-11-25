@echo off
setlocal
set ROOT=%~dp0..
cd /d "%ROOT%"

set SLOT=%1
if "%SLOT%"=="" set SLOT=auto

if not exist logs mkdir logs
python -u "%~dp0youtube_shorts_daily_pipeline.py" --slot %SLOT% %2 %3 %4 >> "%ROOT%\logs\yt_shorts_publisher.log" 2>&1
exit /b %errorlevel%
