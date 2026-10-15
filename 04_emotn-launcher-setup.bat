@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp004_emotn-launcher-setup.ps1" %*
exit /b %ERRORLEVEL%
