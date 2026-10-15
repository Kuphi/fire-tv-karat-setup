@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp000_setup.ps1" %*
exit /b %ERRORLEVEL%
