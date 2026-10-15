@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp002_permanent_root_magisk.ps1" %*
exit /b %ERRORLEVEL%
