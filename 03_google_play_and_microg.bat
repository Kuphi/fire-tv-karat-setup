@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp003_google_play_and_microg.ps1" %*
exit /b %ERRORLEVEL%
